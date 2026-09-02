using System.Text.Json;
using System.Text.Json.Serialization;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Synthesis;

namespace Ensrick.GuardScalingPatcher;

/// <summary>
/// Ensrick Guard Scaling Patch (issue #51). Ordinary hold / city / Imperial / Stormcloak
/// guards scale 1:1 with the player, minimum level 5, no offset. Which records are
/// "ordinary" is not decided here: policy.json (hand-reviewed from the record audit)
/// lists every target and every exclusion with its reason, and this generator refuses
/// to touch anything else.
///
///   GuardScalingPatcher --audit DATA LOADORDER OUT.json        record audit (receipts)
///   GuardScalingPatcher --audit-links DATA LOADORDER PLUGIN     unresolved-link check
///   GuardScalingPatcher run-patcher ... --ExtraDataFolder DIR   Synthesis CLI; DIR holds policy.json
/// </summary>
public static class Program
{
    public const string OutputPlugin = "Ensrick Guard Scaling Patch.esp";
    private const int CompressedRecordFlag = 0x00040000;

    public static async Task<int> Main(string[] args)
    {
        if (args is ["--audit", var auditData, var auditLoadOrder, var auditOut])
        {
            return GuardAudit.Run(auditData, auditLoadOrder, auditOut);
        }
        if (args is ["--audit-links", var dataFolder, var loadOrderFile, var pluginPath])
        {
            return LinkAudit.Run(dataFolder, loadOrderFile, pluginPath);
        }
        return await SynthesisPipeline.Instance
            .AddPatch<ISkyrimMod, ISkyrimModGetter>(RunPatch, new PatcherPreferences
            {
                ExclusionMods = [ModKey.FromNameAndExtension(OutputPlugin)],
            })
            .SetTypicalOpen(GameRelease.SkyrimSE, OutputPlugin)
            .Run(args);
    }

    public sealed class Policy
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonPropertyName("issue")] public string? Issue { get; set; }
        [JsonPropertyName("rule")] public Rule Rule { get; set; } = new();
        [JsonPropertyName("targets")] public List<Target> Targets { get; set; } = [];
        [JsonPropertyName("excluded")] public List<Exclusion> Excluded { get; set; } = [];
    }

    public sealed class Rule
    {
        [JsonPropertyName("levelMult")] public float LevelMult { get; set; } = 1.0f;
        [JsonPropertyName("calcMinLevel")] public short CalcMinLevel { get; set; } = 5;
        /// <summary>null = keep the winning record's own cap.</summary>
        [JsonPropertyName("calcMaxLevel")] public short? CalcMaxLevel { get; set; }
    }

    public sealed class Target
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("role")] public string? Role { get; set; }
    }

    public sealed class Exclusion
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("reason")] public string Reason { get; set; } = "";
    }

    private static void RunPatch(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var policyDirectory = state.ExtraSettingsDataPath
            ?? throw new InvalidOperationException("--ExtraDataFolder must point at the folder holding policy.json.");
        var policyPath = Path.Combine(policyDirectory, "policy.json");
        var policy = JsonSerializer.Deserialize<Policy>(File.ReadAllText(policyPath))
            ?? throw new InvalidOperationException($"Could not read {policyPath}.");
        Require(policy.SchemaVersion == 1, "policy.json schemaVersion must be 1.");
        Require(policy.Targets.Count > 0, "policy.json lists no targets.");
        var excluded = policy.Excluded.Select(e => FormKey.Factory(e.FormKey)).ToHashSet();
        Require(!policy.Targets.Any(t => excluded.Contains(FormKey.Factory(t.FormKey))),
            "A FormKey is both a target and an exclusion.");

        state.PatchMod.ModHeader.Author = "Ensrick";
        state.PatchMod.ModHeader.Description =
            $"Ordinary guards scale 1:1 with the player (level mult {policy.Rule.LevelMult:0.##}, minimum level {policy.Rule.CalcMinLevel}). Issue #51. Override-only, generated.";
        state.PatchMod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small;

        var positions = state.LoadOrder.ListedOrder
            .Select((listing, index) => (listing.ModKey, index))
            .ToDictionary(item => item.ModKey, item => item.index);

        var patched = 0;
        foreach (var target in policy.Targets
                     .OrderBy(t => FormKey.Factory(t.FormKey).ModKey.FileName.String, StringComparer.Ordinal)
                     .ThenBy(t => FormKey.Factory(t.FormKey).ID))
        {
            var formKey = FormKey.Factory(target.FormKey);
            var contexts = state.LinkCache
                .ResolveAllContexts<INpc, INpcGetter>(formKey)
                .Where(context => positions.ContainsKey(context.ModKey))
                .OrderBy(context => positions[context.ModKey])
                .ToArray();
            Require(contexts.Length > 0, $"{target.FormKey} {target.EditorId}: no record in the load order.");
            var winner = contexts[^1];
            Require(string.Equals(winner.Record.EditorID, target.EditorId, StringComparison.Ordinal),
                $"{target.FormKey}: winner EditorID is {winner.Record.EditorID}, policy says {target.EditorId}.");
            Require(!winner.Record.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Stats),
                $"{target.FormKey} {target.EditorId}: uses its template's stats; the policy must name the stats provider instead.");

            var before = GuardAudit.Level(winner.Record.Configuration);
            var patch = winner.GetOrAddAsOverride(state.PatchMod);
            patch.Configuration.Level = new PcLevelMult { LevelMult = policy.Rule.LevelMult };
            patch.Configuration.CalcMinLevel = policy.Rule.CalcMinLevel;
            if (policy.Rule.CalcMaxLevel is { } cap)
            {
                patch.Configuration.CalcMaxLevel = cap;
            }
            ClearCompression(patch);
            patched++;
            var after = GuardAudit.Level(patch.Configuration);
            Console.WriteLine(
                $"NPC_ {formKey} {target.EditorId}: winner={winner.ModKey.FileName} " +
                $"before={JsonSerializer.Serialize(before)} after={JsonSerializer.Serialize(after)} ({target.Role})");
        }

        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        Require(records.Length == policy.Targets.Count && records.All(record => record is INpcGetter),
            $"Structural invariant failed: expected {policy.Targets.Count} NPC_ overrides, got {records.Length}.");
        Require(!records.Any(record => record.FormKey.ModKey == state.PatchMod.ModKey),
            "The patch contains a newly allocated FormKey.");
        Require(!records.Any(record => excluded.Contains(record.FormKey)),
            "An excluded record reached the output.");
        Console.WriteLine($"Generated {patched} NPC_ overrides; {policy.Excluded.Count} records excluded by policy. Output: {OutputPlugin} (ESL-flagged ESP)");
    }

    private static void ClearCompression(IMajorRecord record) =>
        record.MajorRecordFlagsRaw &= ~CompressedRecordFlag;

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
