using System.Text.Json;
using System.Text.RegularExpressions;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace Ensrick.GuardScalingPatcher;

/// <summary>
/// Record-level audit of every guard-like NPC_ in the load order: which plugin wins,
/// what level rule the winner carries, and which record actually provides the stats
/// (template chains, leveled templates). Output is one JSON document; the markdown
/// report is rendered from it by report.py so every number in the report has a
/// machine-readable receipt.
/// </summary>
internal static class GuardAudit
{
    // Deliberately wide: anything that looks like a guard, soldier or hold/civil-war
    // fighter is collected and the report decides. Collecting too much is cheap;
    // missing a mod-added guard family is not.
    private static readonly Regex Candidate = new(
        "guard|soldier|legion|stormcloak|militia|sentr|watchm|penitus",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

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

        var rows = new List<object>();
        var leveled = new Dictionary<FormKey, object>();
        var providers = new Dictionary<FormKey, object>();
        var candidates = 0;
        foreach (var npc in loadOrder.PriorityOrder.Where(l => l.Mod is not null).Select(l => l.Mod!).WinningOverrides<INpcGetter>())
        {
            var reasons = Reasons(npc, cache);
            if (reasons.Count == 0) continue;
            candidates++;
            var provs = new List<object>();
            foreach (var (leaf, path) in StatsProviders(npc, cache))
            {
                if (!providers.ContainsKey(leaf.FormKey))
                {
                    providers[leaf.FormKey] = new
                    {
                        formKey = leaf.FormKey.ToString(),
                        editorId = leaf.EditorID,
                        name = leaf.Name?.String,
                        chain = Chain(leaf.FormKey, cache, positions),
                        level = Level(leaf.Configuration),
                        flags = leaf.Configuration.Flags.ToString(),
                        templateFlags = leaf.Configuration.TemplateFlags.ToString(),
                        @class = Link(leaf.Class, cache),
                        combatStyle = Link(leaf.CombatStyle, cache),
                        factions = Factions(leaf, cache),
                    };
                }
                provs.Add(new { formKey = leaf.FormKey.ToString(), editorId = leaf.EditorID, path });
                foreach (var step in path.Where(p => p.StartsWith("LVLN ", StringComparison.Ordinal)))
                {
                    var key = FormKey.Factory(step.Split(' ')[1]);
                    if (!leveled.ContainsKey(key) && cache.TryResolve<ILeveledNpcGetter>(key, out var list))
                    {
                        leveled[key] = DescribeLeveled(list, cache, positions);
                    }
                }
            }
            rows.Add(new
            {
                formKey = npc.FormKey.ToString(),
                editorId = npc.EditorID,
                name = npc.Name?.String,
                reasons,
                chain = Chain(npc.FormKey, cache, positions),
                level = Level(npc.Configuration),
                flags = npc.Configuration.Flags.ToString(),
                templateFlags = npc.Configuration.TemplateFlags.ToString(),
                template = Link(npc.Template, cache),
                statsProviders = provs,
                @class = Link(npc.Class, cache),
                combatStyle = Link(npc.CombatStyle, cache),
                race = Link(npc.Race, cache),
                voice = Link(npc.Voice, cache),
                defaultOutfit = Link(npc.DefaultOutfit, cache),
                factions = Factions(npc, cache),
            });
        }

        var document = new
        {
            schemaVersion = 1,
            generatedUtc = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            loadOrderEntries = modKeys.Length,
            missingPlugins = missing,
            candidates,
            npcs = rows,
            statsProviders = providers.Values,
            leveledNpcs = leveled.Values,
        };
        File.WriteAllText(outputJson, JsonSerializer.Serialize(document, new JsonSerializerOptions { WriteIndented = true }));
        Console.WriteLine($"audit: {candidates} candidate NPC_ records, {providers.Count} stats providers, {leveled.Count} leveled templates, {missing.Length} missing plugins -> {outputJson}");
        return 0;
    }

    private static List<string> Reasons(INpcGetter npc, ILinkCache cache)
    {
        var reasons = new List<string>();
        if (npc.EditorID is { } id && Candidate.IsMatch(id)) reasons.Add("editorId");
        if (npc.Class.TryResolve(cache, out var cls) && cls.EditorID is { } c && Candidate.IsMatch(c)) reasons.Add("class:" + c);
        foreach (var placement in npc.Factions)
        {
            if (placement.Faction.TryResolve(cache, out var faction) && faction.EditorID is { } f && Candidate.IsMatch(f))
            {
                reasons.Add("faction:" + f);
            }
        }
        return reasons;
    }

    internal static object Level(INpcConfigurationGetter configuration) => configuration.Level switch
    {
        IPcLevelMultGetter mult => new
        {
            kind = "PcLevelMult",
            levelMult = (float?)mult.LevelMult,
            level = (short?)null,
            calcMin = configuration.CalcMinLevel,
            calcMax = configuration.CalcMaxLevel,
            healthOffset = configuration.HealthOffset,
            autoCalcStats = configuration.Flags.HasFlag(NpcConfiguration.Flag.AutoCalcStats),
        },
        INpcLevelGetter fixedLevel => new
        {
            kind = "Fixed",
            levelMult = (float?)null,
            level = (short?)fixedLevel.Level,
            calcMin = configuration.CalcMinLevel,
            calcMax = configuration.CalcMaxLevel,
            healthOffset = configuration.HealthOffset,
            autoCalcStats = configuration.Flags.HasFlag(NpcConfiguration.Flag.AutoCalcStats),
        },
        _ => new
        {
            kind = "unknown",
            levelMult = (float?)null,
            level = (short?)null,
            calcMin = configuration.CalcMinLevel,
            calcMax = configuration.CalcMaxLevel,
            healthOffset = configuration.HealthOffset,
            autoCalcStats = configuration.Flags.HasFlag(NpcConfiguration.Flag.AutoCalcStats),
        },
    };

    private static List<object> Chain(FormKey formKey, ILinkCache<ISkyrimMod, ISkyrimModGetter> cache, IReadOnlyDictionary<ModKey, int> positions)
    {
        return cache.ResolveAllContexts<INpc, INpcGetter>(formKey)
            .Where(context => positions.ContainsKey(context.ModKey))
            .OrderBy(context => positions[context.ModKey])
            .Select(context => (object)new
            {
                plugin = context.ModKey.FileName.String,
                level = Level(context.Record.Configuration),
                flags = context.Record.Configuration.Flags.ToString(),
                templateFlags = context.Record.Configuration.TemplateFlags.ToString(),
                template = context.Record.Template.FormKeyNullable?.ToString(),
                @class = context.Record.Class.FormKey.ToString(),
                combatStyle = context.Record.CombatStyle.FormKeyNullable?.ToString(),
                defaultOutfit = context.Record.DefaultOutfit.FormKeyNullable?.ToString(),
            })
            .ToList();
    }

    /// <summary>Walk the Use-Stats template chain to the record(s) whose ACBS the engine reads.</summary>
    internal static IEnumerable<(INpcGetter Leaf, List<string> Path)> StatsProviders(INpcGetter npc, ILinkCache cache)
    {
        var results = new List<(INpcGetter, List<string>)>();
        Walk(npc, new List<string>(), new HashSet<FormKey>(), results, cache);
        return results;
    }

    private static void Walk(INpcGetter npc, List<string> path, HashSet<FormKey> seen, List<(INpcGetter, List<string>)> results, ILinkCache cache)
    {
        if (!seen.Add(npc.FormKey)) return;
        var usesStats = npc.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Stats);
        if (!usesStats || npc.Template.IsNull || !npc.Template.TryResolve(cache, out var spawn))
        {
            results.Add((npc, path));
            return;
        }
        Descend(spawn, path, seen, results, cache);
    }

    private static void Descend(INpcSpawnGetter spawn, List<string> path, HashSet<FormKey> seen, List<(INpcGetter, List<string>)> results, ILinkCache cache)
    {
        switch (spawn)
        {
            case INpcGetter templateNpc:
                Walk(templateNpc, [.. path, "NPC_ " + templateNpc.FormKey + " " + templateNpc.EditorID], seen, results, cache);
                break;
            case ILeveledNpcGetter list:
                if (!seen.Add(list.FormKey)) return;
                foreach (var entry in list.Entries ?? [])
                {
                    if (entry.Data is null || entry.Data.Reference.IsNull) continue;
                    if (entry.Data.Reference.TryResolve(cache, out var child))
                    {
                        Descend(child, [.. path, "LVLN " + list.FormKey + " " + list.EditorID + " @" + entry.Data.Level], new HashSet<FormKey>(seen), results, cache);
                    }
                }
                break;
        }
    }

    private static object DescribeLeveled(ILeveledNpcGetter list, ILinkCache<ISkyrimMod, ISkyrimModGetter> cache, IReadOnlyDictionary<ModKey, int> positions)
    {
        var chain = cache.ResolveAllContexts<ILeveledNpc, ILeveledNpcGetter>(list.FormKey)
            .Where(context => positions.ContainsKey(context.ModKey))
            .OrderBy(context => positions[context.ModKey])
            .Select(context => context.ModKey.FileName.String)
            .ToArray();
        return new
        {
            formKey = list.FormKey.ToString(),
            editorId = list.EditorID,
            chain,
            flags = list.Flags.ToString(),
            chanceNone = list.ChanceNone.Value,
            entries = (list.Entries ?? []).Select(entry => new
            {
                level = entry.Data?.Level,
                count = entry.Data?.Count,
                reference = entry.Data?.Reference.FormKey.ToString(),
                editorId = entry.Data is { } d && d.Reference.TryResolve(cache, out var r) ? r.EditorID : null,
            }).ToArray(),
        };
    }

    private static object? Link<T>(IFormLinkGetter<T> link, ILinkCache cache) where T : class, IMajorRecordGetter
    {
        if (link.IsNull) return null;
        return new
        {
            formKey = link.FormKey.ToString(),
            editorId = link.TryResolve(cache, out var record) ? record.EditorID : null,
        };
    }

    private static List<object> Factions(INpcGetter npc, ILinkCache cache)
    {
        return npc.Factions.Select(placement => (object)new
        {
            formKey = placement.Faction.FormKey.ToString(),
            editorId = placement.Faction.TryResolve(cache, out var faction) ? faction.EditorID : null,
            rank = placement.Rank,
        }).ToList();
    }
}
