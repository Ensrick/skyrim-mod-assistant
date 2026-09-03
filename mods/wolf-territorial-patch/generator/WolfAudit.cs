using System.Text.Json;
using System.Text.RegularExpressions;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace Ensrick.WolfTerritorialPatcher;

/// <summary>
/// Record-level audit of every wolf-like NPC_ in the load order: which plugin wins,
/// what aggro-radius rule the winner carries, which record actually provides its AI
/// data (template chains), and how many placed references point at it. Reference
/// controls (bear, horker, sabre cat) are collected too, because the whole design
/// question is "how far is a wolf from a bear".
/// </summary>
internal static class WolfAudit
{
    // Deliberately wide. Collecting a quest wolf we will not touch is cheap; missing
    // a mod-added wolf family in Bruma or Beyond Reach is not.
    private static readonly Regex Candidate = new("wolf", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex Control = new("^Enc(Bear|Horker|SabreCat|Fox|Elk|Deer)",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public sealed record AiDescription(
        string Aggression,
        string Confidence,
        string Assistance,
        string Mood,
        string Responsibility,
        byte EnergyLevel,
        bool AggroRadiusBehavior,
        uint Warn,
        uint WarnOrAttack,
        uint Attack);

    public static AiDescription? Describe(IAIDataGetter? ai) => ai is null
        ? null
        : new AiDescription(
            ai.Aggression.ToString(),
            ai.Confidence.ToString(),
            ai.Assistance.ToString(),
            ai.Mood.ToString(),
            ai.Responsibility.ToString(),
            ai.EnergyLevel,
            ai.AggroRadiusBehavior,
            ai.Warn,
            ai.WarnOrAttack,
            ai.Attack);

    public static int Run(string dataFolder, string loadOrderFile, string outputJson)
    {
        var modKeys = LoadOrderFile.Read(loadOrderFile);
        using var loadOrder = LoadOrder.Import<ISkyrimModGetter>(
            new DirectoryPath(dataFolder),
            modKeys,
            GameRelease.SkyrimSE,
            factory: modPath => SkyrimMod.CreateFromBinaryOverlay(modPath.Path, SkyrimRelease.SkyrimSE));
        var missing = loadOrder.ListedOrder.Where(l => l.Mod is null).Select(l => l.ModKey.FileName.String).ToArray();
        var listed = loadOrder.ListedOrder.Where(l => l.Mod is not null).Select(l => l.Mod!).ToArray();
        using var cache = listed.ToImmutableLinkCache<ISkyrimMod, ISkyrimModGetter>();
        var positions = loadOrder.ListedOrder
            .Select((listing, index) => (listing.ModKey, index))
            .ToDictionary(item => item.ModKey, item => item.index);

        // One pass over every placed actor in the load order: how many references
        // point at each base actor. The exterior/interior split needs placement
        // contexts and is not what the AI-data policy turns on, so it is left to the
        // encounter-side audit.
        var placedTotal = new Dictionary<FormKey, int>();
        var placedRefs = 0;
        foreach (var placed in listed.WinningOverrides<IPlacedNpcGetter>())
        {
            placedRefs++;
            var baseKey = placed.Base.FormKey;
            if (baseKey.IsNull) continue;
            placedTotal[baseKey] = placedTotal.GetValueOrDefault(baseKey) + 1;
        }

        var wolves = new List<(string Key, object Row)>();
        var controls = new List<(string Key, object Row)>();
        // Every NPC keyed by the record it takes AI data from, so "who inherits from
        // whom" is measured rather than asserted.
        var heirs = new Dictionary<FormKey, List<string>>();
        foreach (var npc in listed.WinningOverrides<INpcGetter>())
        {
            if (!npc.Template.IsNull
                && npc.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.AIData))
            {
                heirs.GetOrAdd(npc.Template.FormKey).Add(npc.EditorID ?? npc.FormKey.ToString());
            }
        }

        foreach (var npc in listed.WinningOverrides<INpcGetter>())
        {
            var editorId = npc.EditorID ?? "";
            var isWolf = Candidate.IsMatch(editorId) && !editorId.Contains("werewolf", StringComparison.OrdinalIgnoreCase);
            var isControl = Control.IsMatch(editorId);
            if (!isWolf && !isControl) continue;

            var (provider, path) = AiProvider(npc, cache);
            var row = new
            {
                formKey = npc.FormKey.ToString(),
                editorId = npc.EditorID,
                name = npc.Name?.String,
                chain = Chain(npc.FormKey, cache, positions),
                templateFlags = npc.Configuration.TemplateFlags.ToString(),
                template = npc.Template.IsNull ? null : npc.Template.FormKey.ToString(),
                ownsAiData = provider.FormKey == npc.FormKey,
                aiDataProvider = provider.FormKey == npc.FormKey
                    ? null
                    : new { formKey = provider.FormKey.ToString(), editorId = provider.EditorID, path },
                ai = Describe(npc.AIData),
                effectiveAi = Describe(provider.AIData),
                combatStyle = Link(npc.CombatStyle, cache),
                race = Link(npc.Race, cache),
                factions = npc.Factions
                    .Select(f => Link(f.Faction, cache))
                    .OrderBy(f => f, StringComparer.Ordinal)
                    .ToArray(),
                respawns = npc.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Respawn),
                inheritedBy = heirs.GetValueOrDefault(npc.FormKey)?.OrderBy(x => x, StringComparer.Ordinal).ToArray()
                              ?? [],
                placedRefs = placedTotal.GetValueOrDefault(npc.FormKey),
            };
            (isWolf ? wolves : controls).Add((npc.FormKey.ToString(), row));
        }

        var document = new
        {
            schemaVersion = 1,
            generatedUtc = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            loadOrderEntries = loadOrder.ListedOrder.Count(),
            missingPlugins = missing,
            placedActorReferences = placedRefs,
            wolves = wolves.OrderBy(r => r.Key, StringComparer.Ordinal).Select(r => r.Row).ToArray(),
            controls = controls.OrderBy(r => r.Key, StringComparer.Ordinal).Select(r => r.Row).ToArray(),
        };
        File.WriteAllText(outputJson,
            JsonSerializer.Serialize(document, new JsonSerializerOptions { WriteIndented = true }) + "\n");
        Console.WriteLine($"wolves={wolves.Count} controls={controls.Count} placedActorReferences={placedRefs} -> {outputJson}");
        return missing.Length == 0 ? 0 : 3;
    }

    /// <summary>Walk the template chain while the AI-data template flag is set; the
    /// record the walk stops on is the one whose AI data the game actually uses.</summary>
    private static (INpcGetter Provider, string[] Path) AiProvider(INpcGetter npc, ILinkCache<ISkyrimMod, ISkyrimModGetter> cache)
    {
        var path = new List<string>();
        var current = npc;
        var seen = new HashSet<FormKey> { npc.FormKey };
        while (current.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.AIData)
               && !current.Template.IsNull
               && cache.TryResolve<INpcGetter>(current.Template.FormKey, out var next)
               && seen.Add(next.FormKey))
        {
            path.Add($"NPC_ {next.FormKey} {next.EditorID}");
            current = next;
        }
        return (current, path.ToArray());
    }

    private static string[] Chain(FormKey formKey, ILinkCache<ISkyrimMod, ISkyrimModGetter> cache, IReadOnlyDictionary<ModKey, int> positions) =>
        cache.ResolveAllContexts<INpc, INpcGetter>(formKey)
            .Where(context => positions.ContainsKey(context.ModKey))
            .OrderBy(context => positions[context.ModKey])
            .Select(context => context.ModKey.FileName.String)
            .ToArray();

    private static string Link<T>(IFormLinkGetter<T> link, ILinkCache<ISkyrimMod, ISkyrimModGetter> cache) where T : class, IMajorRecordGetter
    {
        if (link.IsNull) return "";
        return cache.TryResolve<T>(link.FormKey, out var record)
            ? $"{link.FormKey} {record.EditorID}"
            : link.FormKey.ToString();
    }
}

internal static class LoadOrderFile
{
    /// <summary>plugins.txt-style file: one plugin per line, '*' marks active, '#' comments.
    /// The five base masters are always present first; our own output is never an input.</summary>
    public static ModKey[] Read(string loadOrderFile)
    {
        var listed = File.ReadAllLines(loadOrderFile)
            .Select(line => line.Trim())
            .Where(line => line.Length > 0 && !line.StartsWith('#'))
            .Select(line => ModKey.FromNameAndExtension(line.TrimStart('*')))
            .Where(modKey => !string.Equals(modKey.FileName.String, Program.OutputPlugin, StringComparison.OrdinalIgnoreCase))
            .ToArray();
        return new[] { "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm" }
            .Select(name => ModKey.FromNameAndExtension(name))
            .Concat(listed)
            .Distinct()
            .ToArray();
    }
}
