using System.Text.Json;
using System.Text.Json.Serialization;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Synthesis;

namespace Ensrick.WolfTerritorialPatcher;

/// <summary>
/// Encounter-side half of issue #42: fewer wilderness predator encounters while
/// keeping pack size.
///
/// The two requirements pull against each other through the leveled lists, because
/// every placed reference rolls its regional predator list independently: thinning
/// wolves out of the list lowers frequency AND turns a three-point site into a wolf,
/// a bear and a spider. Retiring whole spatial CLUSTERS instead lowers frequency and
/// leaves pack size exactly as Bethesda placed it - and retiring the singletons first
/// raises it, because the lone predator between packs is what makes the wilderness
/// feel crowded.
///
/// Nothing is deleted: a deleted ACHR is a UDR. The retired references are flagged
/// Initially Disabled, which is reversible by disabling one plugin.
/// </summary>
internal static class EncounterThinning
{
    public sealed class Policy
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonPropertyName("issue")] public string? Issue { get; set; }
        [JsonPropertyName("ruleText")] public string? RuleText { get; set; }
        [JsonPropertyName("rule")] public Rule Rule { get; set; } = new();
        [JsonPropertyName("baseActors")] public List<BaseActor> BaseActors { get; set; } = [];
    }

    public sealed class Rule
    {
        /// <summary>Two references belong to the same encounter when they are within this
        /// many game units of each other in the same worldspace (1 unit = 1.428 cm).</summary>
        [JsonPropertyName("clusterLinkRadius")] public double ClusterLinkRadius { get; set; } = 2000;
        /// <summary>Clusters of this size or smaller are retired. 1 = singletons only.</summary>
        [JsonPropertyName("retireClustersUpToSize")] public int RetireClustersUpToSize { get; set; } = 1;
        /// <summary>Refuse to run if the retired share exceeds this fraction; a policy or
        /// load-order change that suddenly empties the map should stop, not ship.</summary>
        [JsonPropertyName("maxRetiredFraction")] public double MaxRetiredFraction { get; set; } = 0.40;
    }

    public sealed class BaseActor
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("role")] public string? Role { get; set; }
    }

    private sealed record Point(double X, double Y, double Z);

    public static void Run(IPatcherState<ISkyrimMod, ISkyrimModGetter> state, string policyPath)
    {
        var policy = JsonSerializer.Deserialize<Policy>(File.ReadAllText(policyPath))
            ?? throw new InvalidOperationException($"Could not read {policyPath}.");
        Require(policy.SchemaVersion == 1, "policy.json schemaVersion must be 1.");
        Require(policy.BaseActors.Count > 0, "policy.json lists no base actors.");
        Require(policy.Rule.RetireClustersUpToSize >= 1, "retireClustersUpToSize must be at least 1.");
        Require(policy.Rule.ClusterLinkRadius > 0, "clusterLinkRadius must be positive.");

        var bases = policy.BaseActors.ToDictionary(b => FormKey.Factory(b.FormKey), b => b);
        foreach (var (formKey, entry) in bases)
        {
            Require(state.LinkCache.TryResolve<INpcGetter>(formKey, out var npc)
                    && string.Equals(npc.EditorID, entry.EditorId, StringComparison.Ordinal),
                $"{entry.FormKey}: no NPC_ with EditorID {entry.EditorId} in the load order.");
        }

        state.PatchMod.ModHeader.Author = "Ensrick";
        state.PatchMod.ModHeader.Description =
            $"Retires whole spatial clusters of wilderness predator spawn points (size <= {policy.Rule.RetireClustersUpToSize} "
            + $"within {policy.Rule.ClusterLinkRadius:0} units) by flagging them Initially Disabled. Issue #42. Override-only, generated.";
        state.PatchMod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small;

        var cellWorld = new Dictionary<FormKey, FormKey>();
        foreach (var listing in state.LoadOrder.PriorityOrder)
        {
            if (listing.Mod is not { } mod) continue;
            foreach (var world in mod.Worldspaces)
            {
                if (world.TopCell is { } topCell) cellWorld[topCell.FormKey] = world.FormKey;
                foreach (var block in world.SubCells)
                {
                    foreach (var subBlock in block.Items)
                    {
                        foreach (var worldCell in subBlock.Items)
                        {
                            cellWorld[worldCell.FormKey] = world.FormKey;
                        }
                    }
                }
            }
        }

        // Collect every candidate placed reference: exterior, temporary, no enable
        // parent, not already disabled, and pointing at one of the policy's base actors.
        var candidates = new List<(IModContext<ISkyrimMod, ISkyrimModGetter, IPlacedNpc, IPlacedNpcGetter> Context,
                                   FormKey Worldspace, Point Position, FormKey BaseKey, string? Ineligible)>();
        var skipped = new Dictionary<string, int>();
        void Skip(string reason) => skipped[reason] = skipped.GetValueOrDefault(reason) + 1;

        var seenPlaced = 0;
        var seenOnBase = 0;
        foreach (var context in state.LoadOrder.PriorityOrder.PlacedNpc().WinningContextOverrides(state.LinkCache))
        {
            seenPlaced++;
            var record = context.Record;
            if (record.Base.IsNull || !bases.ContainsKey(record.Base.FormKey)) continue;
            seenOnBase++;
            if (record.Placement is not { } placement)
            {
                Skip("no placement data"); continue;
            }
            if (context.Parent?.Record is not ICellGetter cell)
            {
                Skip("no parent cell"); continue;
            }
            if (cell.Flags.HasFlag(Cell.Flag.IsInteriorCell))
            {
                Skip("interior cell"); continue;
            }
            // Placed-record contexts carry only their cell as a parent, so the
            // worldspace comes from a cell -> worldspace map built over every plugin
            // (the mapping is a stable fact and does not depend on who wins).
            var worldspace = cellWorld.GetValueOrDefault(cell.FormKey, FormKey.Null);
            if (worldspace.IsNull)
            {
                Skip("no parent worldspace"); continue;
            }

            // Ineligible references still take part in CLUSTERING: a pack is a pack
            // whether or not we may retire one of its members. Dropping them from the
            // clustering instead is how a pair becomes a fake singleton - that error
            // turned a 31% cut into 72% on the first run of this generator.
            string? ineligible = null;
            if (record.SkyrimMajorRecordFlags.HasFlag(SkyrimMajorRecord.SkyrimMajorRecordFlag.InitiallyDisabled))
            {
                ineligible = "already initially disabled";
            }
            else if (record.SkyrimMajorRecordFlags.HasFlag(SkyrimMajorRecord.SkyrimMajorRecordFlag.Deleted))
            {
                ineligible = "deleted";
            }
            else if (!record.EnableParent?.Reference.IsNull.Equals(true) ?? false)
            {
                ineligible = "has an enable parent";
            }
            else if (cell.Persistent.Any(reference => reference.FormKey == record.FormKey))
            {
                // Persistence is not a record flag in Skyrim; it is which child group
                // the reference lives in. A persistent actor is loaded for the whole
                // game and is far more likely to be quest-relevant.
                ineligible = "persistent reference";
            }
            if (ineligible is not null) Skip(ineligible);

            candidates.Add((context, worldspace,
                new Point(placement.Position.X, placement.Position.Y, placement.Position.Z),
                record.Base.FormKey, ineligible));
        }

        Console.WriteLine(
            $"placedNpcContexts={seenPlaced} onPolicyBases={seenOnBase} candidates={candidates.Count} "
            + $"skipped=[{string.Join(", ", skipped.Select(kv => $"{kv.Key}:{kv.Value}"))}]");
        Require(candidates.Count > 0,
            $"No candidate placed references found ({seenPlaced} placed contexts, {seenOnBase} on policy bases).");

        // Single-linkage clustering inside each worldspace.
        var retired = new List<int>();
        var heldClusters = 0;
        var clusterSizes = new SortedDictionary<int, int>();
        var byWorld = candidates
            .Select((item, index) => (item, index))
            .GroupBy(pair => pair.item.Worldspace);
        var radiusSquared = policy.Rule.ClusterLinkRadius * policy.Rule.ClusterLinkRadius;
        foreach (var group in byWorld)
        {
            var members = group.ToArray();
            var used = new bool[members.Length];
            for (var i = 0; i < members.Length; i++)
            {
                if (used[i]) continue;
                var stack = new Stack<int>();
                var cluster = new List<int>();
                stack.Push(i);
                used[i] = true;
                while (stack.Count > 0)
                {
                    var current = stack.Pop();
                    cluster.Add(current);
                    for (var k = 0; k < members.Length; k++)
                    {
                        if (used[k]) continue;
                        var a = members[current].item.Position;
                        var b = members[k].item.Position;
                        var dx = a.X - b.X; var dy = a.Y - b.Y; var dz = a.Z - b.Z;
                        if (dx * dx + dy * dy + dz * dz <= radiusSquared)
                        {
                            used[k] = true;
                            stack.Push(k);
                        }
                    }
                }
                clusterSizes[cluster.Count] = clusterSizes.GetValueOrDefault(cluster.Count) + 1;
                if (cluster.Count > policy.Rule.RetireClustersUpToSize) continue;
                // All or nothing: a cluster holding a reference we may not touch is
                // left whole, so no encounter is ever half-retired.
                if (cluster.Any(index => candidates[members[index].index].Ineligible is not null))
                {
                    heldClusters++;
                    continue;
                }
                retired.AddRange(cluster.Select(index => members[index].index));
            }
        }

        var fraction = (double)retired.Count / candidates.Count;
        Require(fraction <= policy.Rule.MaxRetiredFraction,
            $"Would retire {retired.Count} of {candidates.Count} references ({fraction:P1}), "
            + $"over the {policy.Rule.MaxRetiredFraction:P0} guard rail.");

        // Deterministic order: FormKey, not enumeration order.
        foreach (var index in retired
                     .Select(i => candidates[i])
                     .OrderBy(c => c.Context.Record.FormKey.ModKey.FileName.String, StringComparer.Ordinal)
                     .ThenBy(c => c.Context.Record.FormKey.ID))
        {
            var patch = index.Context.GetOrAddAsOverride(state.PatchMod);
            patch.SkyrimMajorRecordFlags |= SkyrimMajorRecord.SkyrimMajorRecordFlag.InitiallyDisabled;
            patch.MajorRecordFlagsRaw &= ~0x00040000;
        }

        var byBase = retired
            .Select(i => candidates[i].BaseKey)
            .GroupBy(key => key)
            .ToDictionary(g => bases[g.Key].EditorId, g => g.Count());
        Console.WriteLine(
            $"candidates={candidates.Count} heldClusters={heldClusters} clusters={clusterSizes.Values.Sum()} "
            + $"sizes=[{string.Join(", ", clusterSizes.Select(kv => $"{kv.Key}:{kv.Value}"))}] "
            + $"retired={retired.Count} ({fraction:P1}) "
            + $"skipped=[{string.Join(", ", skipped.Select(kv => $"{kv.Key}:{kv.Value}"))}]");
        foreach (var (editorId, count) in byBase.OrderByDescending(kv => kv.Value))
        {
            Console.WriteLine($"  retired {count,4} references on {editorId}");
        }

        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        Require(records.All(record => record is IPlacedNpcGetter or ICellGetter or IWorldspaceGetter),
            "Structural invariant failed: the patch contains something other than placed actors and their parents.");
        Require(!records.Any(record => record.FormKey.ModKey == state.PatchMod.ModKey),
            "The patch contains a newly allocated FormKey.");
        Console.WriteLine(
            $"Generated {retired.Count} Initially Disabled placed-actor overrides "
            + $"(cluster link radius {policy.Rule.ClusterLinkRadius:0}, retiring clusters of size "
            + $"<= {policy.Rule.RetireClustersUpToSize}).");
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
