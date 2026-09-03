using System.Text.Json;
using System.Text.Json.Serialization;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Synthesis;

namespace Ensrick.WolfTerritorialPatcher;

/// <summary>
/// Ensrick Wolf Territorial Patch (issue #42). Ordinary wilderness wolves get a
/// warning band and a shorter attack radius, so they behave like bears and horkers
/// - hostile when you come close, not a charge across a field.
///
/// Which wolves count as "ordinary" is not decided here: policy.json (hand-reviewed
/// from the record audit) names every target and every exclusion with its reason,
/// and this generator refuses to touch anything else.
///
///   WolfTerritorialPatcher --audit DATA LOADORDER OUT.json     wolf AI-data audit
///   WolfTerritorialPatcher --audit-links DATA LOADORDER PLUGIN unresolved-link check
///   WolfTerritorialPatcher run-patcher ... --ExtraDataFolder DIR   DIR holds policy.json
/// </summary>
public static class Program
{
    public const string OutputPlugin = "Ensrick Wolf Territorial Patch.esp";
    public const string ThinningPlugin = "Ensrick Wolf Encounter Thinning.esp";
    private const int CompressedRecordFlag = 0x00040000;

    public static async Task<int> Main(string[] args)
    {
        if (args is ["--audit", var auditData, var auditLoadOrder, var auditOut])
        {
            return WolfAudit.Run(auditData, auditLoadOrder, auditOut);
        }
        if (args is ["--audit-links", var dataFolder, var loadOrderFile, var pluginPath])
        {
            return LinkAudit.Run(dataFolder, loadOrderFile, pluginPath);
        }
        return await SynthesisPipeline.Instance
            .AddPatch<ISkyrimMod, ISkyrimModGetter>(RunPatch, new PatcherPreferences
            {
                ExclusionMods =
                [
                    ModKey.FromNameAndExtension(OutputPlugin),
                    ModKey.FromNameAndExtension(ThinningPlugin),
                ],
            })
            .SetTypicalOpen(GameRelease.SkyrimSE, OutputPlugin)
            .Run(args);
    }

    public sealed class Policy
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonPropertyName("issue")] public string? Issue { get; set; }
        [JsonPropertyName("rule")] public Rule Rule { get; set; } = new();
        [JsonPropertyName("expectedBefore")] public Expectation Expected { get; set; } = new();
        [JsonPropertyName("targets")] public List<Target> Targets { get; set; } = [];
        [JsonPropertyName("deInherit")] public List<Exclusion> DeInherit { get; set; } = [];
        [JsonPropertyName("excluded")] public List<Exclusion> Excluded { get; set; } = [];
    }

    /// <summary>
    /// Aggro-radius distances in game units (1 unit = 1.428 cm). Vanilla EncBear is
    /// Warn 2500 / WarnOrAttack 2000 / Attack 1500; vanilla EncHorker is 850 / 640 / 320.
    /// </summary>
    public sealed class Rule
    {
        [JsonPropertyName("warn")] public int Warn { get; set; }
        [JsonPropertyName("warnOrAttack")] public int WarnOrAttack { get; set; }
        [JsonPropertyName("attack")] public int Attack { get; set; }
        /// <summary>Must stay true or the distances above are ignored by the engine.</summary>
        [JsonPropertyName("requireAggroRadiusBehavior")] public bool RequireAggroRadiusBehavior { get; set; } = true;
    }

    /// <summary>The signature every target must currently have. A target that does not
    /// match is a record someone else already changed, and the run fails rather than
    /// silently stamping over it.</summary>
    public sealed class Expectation
    {
        [JsonPropertyName("aggression")] public string Aggression { get; set; } = "Unaggressive";
        [JsonPropertyName("aggroRadiusBehavior")] public bool AggroRadiusBehavior { get; set; } = true;
        [JsonPropertyName("warn")] public int Warn { get; set; }
        [JsonPropertyName("warnOrAttack")] public int WarnOrAttack { get; set; } = 2000;
        [JsonPropertyName("attack")] public int Attack { get; set; } = 1500;
    }

    public sealed class Target
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("role")] public string? Role { get; set; }
        /// <summary>EditorIDs that inherit this record's AI data through their template,
        /// i.e. the blast radius of editing it. Verified at run time.</summary>
        [JsonPropertyName("inheritedBy")] public List<string> InheritedBy { get; set; } = [];
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
        var policyText = File.ReadAllText(policyPath);
        // One generator, two patch shapes (#42 has a behaviour half and an encounter
        // half). policy.json says which; there is no CLI switch to get wrong.
        var mode = JsonDocument.Parse(policyText).RootElement.TryGetProperty("mode", out var modeNode)
            ? modeNode.GetString()
            : "aiData";
        if (string.Equals(mode, "encounterThinning", StringComparison.Ordinal))
        {
            EncounterThinning.Run(state, policyPath);
            return;
        }
        Require(string.Equals(mode, "aiData", StringComparison.Ordinal), $"Unknown policy mode: {mode}");
        var policy = JsonSerializer.Deserialize<Policy>(policyText)
            ?? throw new InvalidOperationException($"Could not read {policyPath}.");
        Require(policy.SchemaVersion == 1, "policy.json schemaVersion must be 1.");
        Require(policy.Targets.Count > 0, "policy.json lists no targets.");
        Require(policy.Rule.Warn >= policy.Rule.WarnOrAttack && policy.Rule.WarnOrAttack >= policy.Rule.Attack,
            "The rule must satisfy warn >= warnOrAttack >= attack; anything else has no warning band.");
        var excluded = policy.Excluded.Select(e => FormKey.Factory(e.FormKey)).ToHashSet();
        Require(!policy.Targets.Any(t => excluded.Contains(FormKey.Factory(t.FormKey))),
            "A FormKey is both a target and an exclusion.");

        state.PatchMod.ModHeader.Author = "Ensrick";
        state.PatchMod.ModHeader.Description =
            $"Ordinary wolves warn at {policy.Rule.Warn} units and attack at {policy.Rule.Attack} instead of {policy.Expected.Attack}. Issue #42. Override-only, generated.";
        state.PatchMod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small;

        var positions = state.LoadOrder.ListedOrder
            .Select((listing, index) => (listing.ModKey, index))
            .ToDictionary(item => item.ModKey, item => item.index);

        // Every NPC in the load order, by winning record, so the inheritance claim in
        // policy.json can be checked rather than trusted.
        var winners = new Dictionary<FormKey, INpcGetter>();
        foreach (var npc in state.LoadOrder.PriorityOrder.Npc().WinningOverrides())
        {
            winners[npc.FormKey] = npc;
        }

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
            Require(!winner.Record.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.AIData),
                $"{target.FormKey} {target.EditorId}: inherits AI data from its template; the policy must name the provider instead.");

            var before = WolfAudit.Describe(winner.Record.AIData);
            Require(before is not null, $"{target.FormKey} {target.EditorId}: no AI data on the winning record.");
            Require(string.Equals(before!.Aggression, policy.Expected.Aggression, StringComparison.Ordinal),
                $"{target.FormKey} {target.EditorId}: aggression is {before.Aggression}, policy expects {policy.Expected.Aggression}.");
            Require(before.AggroRadiusBehavior == policy.Expected.AggroRadiusBehavior,
                $"{target.FormKey} {target.EditorId}: aggroRadiusBehavior is {before.AggroRadiusBehavior}, policy expects {policy.Expected.AggroRadiusBehavior}.");
            Require(before.Warn == (uint)policy.Expected.Warn
                    && before.WarnOrAttack == (uint)policy.Expected.WarnOrAttack
                    && before.Attack == (uint)policy.Expected.Attack,
                $"{target.FormKey} {target.EditorId}: distances are {before.Warn}/{before.WarnOrAttack}/{before.Attack}, "
                + $"policy expects {policy.Expected.Warn}/{policy.Expected.WarnOrAttack}/{policy.Expected.Attack}. "
                + "Something in the load order already changed this record; re-audit before regenerating.");

            // The inheritance claim: exactly these EditorIDs take their AI data from here.
            var actualHeirs = winners.Values
                .Where(npc => !npc.Template.IsNull
                              && npc.Template.FormKey == formKey
                              && npc.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.AIData))
                .Select(npc => npc.EditorID ?? npc.FormKey.ToString())
                .OrderBy(id => id, StringComparer.Ordinal)
                .ToArray();
            var claimed = target.InheritedBy.OrderBy(id => id, StringComparer.Ordinal).ToArray();
            Require(actualHeirs.SequenceEqual(claimed, StringComparer.Ordinal),
                $"{target.FormKey} {target.EditorId}: inheritedBy is {string.Join(", ", claimed)}, "
                + $"the load order says {string.Join(", ", actualHeirs)}.");

            var patch = winner.GetOrAddAsOverride(state.PatchMod);
            var ai = patch.AIData ?? throw new InvalidOperationException($"{target.FormKey}: AI data vanished on override.");
            ai.AggroRadiusBehavior = policy.Rule.RequireAggroRadiusBehavior;
            ai.Warn = (uint)policy.Rule.Warn;
            ai.WarnOrAttack = (uint)policy.Rule.WarnOrAttack;
            ai.Attack = (uint)policy.Rule.Attack;
            ClearCompression(patch);
            patched++;
            var after = WolfAudit.Describe(patch.AIData);
            Console.WriteLine(
                $"NPC_ {formKey} {target.EditorId}: winner={winner.ModKey.FileName} "
                + $"before={JsonSerializer.Serialize(before)} after={JsonSerializer.Serialize(after)} "
                + $"heirs=[{string.Join(", ", actualHeirs)}] ({target.Role})");
        }

        // Non-wolves that inherit a target's AI data and must NOT follow the new rule
        // (a conjured familiar answers to its summoner, not to a territory). They are
        // pinned to the pre-patch numbers and stop inheriting.
        var deInherited = 0;
        foreach (var entry in policy.DeInherit
                     .OrderBy(e => FormKey.Factory(e.FormKey).ModKey.FileName.String, StringComparer.Ordinal)
                     .ThenBy(e => FormKey.Factory(e.FormKey).ID))
        {
            var formKey = FormKey.Factory(entry.FormKey);
            var contexts = state.LinkCache
                .ResolveAllContexts<INpc, INpcGetter>(formKey)
                .Where(context => positions.ContainsKey(context.ModKey))
                .OrderBy(context => positions[context.ModKey])
                .ToArray();
            Require(contexts.Length > 0, $"{entry.FormKey} {entry.EditorId}: no record in the load order.");
            var winner = contexts[^1];
            Require(string.Equals(winner.Record.EditorID, entry.EditorId, StringComparison.Ordinal),
                $"{entry.FormKey}: winner EditorID is {winner.Record.EditorID}, policy says {entry.EditorId}.");
            Require(winner.Record.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.AIData),
                $"{entry.FormKey} {entry.EditorId}: does not inherit AI data, so it does not need de-inheriting.");
            Require(!winner.Record.Template.IsNull
                    && policy.Targets.Any(t => FormKey.Factory(t.FormKey) == winner.Record.Template.FormKey),
                $"{entry.FormKey} {entry.EditorId}: its template is not one of this patch's targets.");

            var patch = winner.GetOrAddAsOverride(state.PatchMod);
            patch.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.AIData;
            var ai = patch.AIData ??= new AIData();
            ai.Aggression = Enum.Parse<Aggression>(policy.Expected.Aggression);
            ai.AggroRadiusBehavior = policy.Expected.AggroRadiusBehavior;
            ai.Warn = (uint)policy.Expected.Warn;
            ai.WarnOrAttack = (uint)policy.Expected.WarnOrAttack;
            ai.Attack = (uint)policy.Expected.Attack;
            ClearCompression(patch);
            deInherited++;
            Console.WriteLine(
                $"NPC_ {formKey} {entry.EditorId}: de-inherited, pinned to "
                + $"{policy.Expected.Warn}/{policy.Expected.WarnOrAttack}/{policy.Expected.Attack} ({entry.Reason})");
        }

        var expectedRecords = policy.Targets.Count + policy.DeInherit.Count;
        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        Require(records.Length == expectedRecords && records.All(record => record is INpcGetter),
            $"Structural invariant failed: expected {expectedRecords} NPC_ overrides, got {records.Length}.");
        Require(!records.Any(record => record.FormKey.ModKey == state.PatchMod.ModKey),
            "The patch contains a newly allocated FormKey.");
        Require(!records.Any(record => excluded.Contains(record.FormKey)),
            "An excluded record reached the output.");
        Console.WriteLine(
            $"Generated {patched} rule overrides + {deInherited} de-inherit overrides; "
            + $"{policy.Excluded.Count} records excluded by policy. "
            + $"Rule warn/warnOrAttack/attack = {policy.Rule.Warn}/{policy.Rule.WarnOrAttack}/{policy.Rule.Attack}. "
            + $"Output: {OutputPlugin} (ESL-flagged ESP)");
    }

    private static void ClearCompression(IMajorRecord record) =>
        record.MajorRecordFlagsRaw &= ~CompressedRecordFlag;

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
