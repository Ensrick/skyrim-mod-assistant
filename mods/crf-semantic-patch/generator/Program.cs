using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Translations;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Synthesis;

namespace Ensrick.CrfSemanticPatcher;

public static class Program
{
    public const string OutputPlugin = "Ensrick CRF Semantic Patch.esp";
    private static readonly ModKey Crf = ModKey.FromNameAndExtension("cutting room floor.esp");
    private static readonly IReadOnlyList<ModKey> RequiredMasters =
    [
        ModKey.FromNameAndExtension("Skyrim.esm"),
        ModKey.FromNameAndExtension("Update.esm"),
        ModKey.FromNameAndExtension("Dawnguard.esm"),
        ModKey.FromNameAndExtension("HearthFires.esm"),
        Crf,
        ModKey.FromNameAndExtension("nwsFollowerFramework.esp"),
        ModKey.FromNameAndExtension("Skyrim Unbound.esp"),
        ModKey.FromNameAndExtension("Lux.esp"),
        ModKey.FromNameAndExtension("Water for ENB (Shades of Skyrim).esp"),
    ];
    private const int CompressedRecordFlag = 0x00040000;

    public static async Task<int> Main(string[] args)
    {
        if (args is ["--audit-links", var dataFolder, var loadOrderFile, var pluginPath])
        {
            return LinkAudit.Run(dataFolder, loadOrderFile, pluginPath);
        }
        var result = await SynthesisPipeline.Instance
            .AddPatch<ISkyrimMod, ISkyrimModGetter>(RunPatch)
            .SetTypicalOpen(GameRelease.SkyrimSE, OutputPlugin)
            .Run(args);
        if (result == 0 && TryGetOption(args, "--OutputPath", out var outputPath))
        {
            EnforceHardMasters(outputPath);
        }
        return result;
    }

    private static void RunPatch(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        state.PatchMod.ModHeader.Author = "Ensrick";
        state.PatchMod.ModHeader.Description =
            "Private profile patch preserving evidenced CRF 3.1.26 semantics with Water, NFF, Lux, and Skyrim Unbound.";
        state.PatchMod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small;

        PatchDarkChasm(state);
        PatchWhiterun(state);
        PatchKilkreath(state);
        PatchDushnikh(state);
        PatchTasiusResponse(state);

        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        if (records.Length != 6 || records.Count(record => record is ICellGetter) != 1
            || records.Count(record => record is ILocationGetter) != 3
            || records.Count(record => record is IDialogResponsesGetter) != 1
            || records.Count(record => record is IDialogTopicGetter) != 1)
        {
            throw new InvalidOperationException(
                $"Expected 5 semantic overrides plus the required INFO parent DIAL: got {records.Length}: " +
                string.Join(", ", records.Select(record => $"{record.FormKey}={record.GetType().Name}")));
        }
        if (records.Any(record => record.FormKey.ModKey == state.PatchMod.ModKey))
        {
            throw new InvalidOperationException("The patch contains a newly allocated FormKey.");
        }
        Console.WriteLine("Generated 5 semantic overrides plus the required INFO parent DIAL; ambiguous Hall of the Dead XLCN intentionally omitted.");
    }

    private static void PatchDarkChasm(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var key = FormKey.Factory("006439:Dawnguard.esm");
        var contexts = new FormLink<ICellGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ICell, ICellGetter>(state.LinkCache)
            .OrderBy(context => LoadPosition(state, context.ModKey))
            .ToArray();
        var winner = contexts[^1];
        var crf = contexts.Last(context => context.ModKey == Crf);
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.Location.SetTo(crf.Record.Location);
        ClearCompression(patch);
        Require(patch.Location.FormKey == FormKey.Factory("005900:cutting room floor.esp"),
            "Dark Chasm Location was not restored from CRF.");
    }

    private static void PatchWhiterun(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var (winner, crf) = LocationContexts(state, "018A56:Skyrim.esm");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.PersistentActorReferencesAdded ??= [];
        var actors = new HashSet<FormKey>(patch.PersistentActorReferencesAdded.Select(entry => entry.Actor.FormKey));
        var wanted = new HashSet<FormKey>
        {
            FormKey.Factory("01A6A4:Skyrim.esm"),
            FormKey.Factory("01A6A5:Skyrim.esm"),
            FormKey.Factory("10E2B6:Skyrim.esm"),
        };
        foreach (var entry in crf.PersistentActorReferencesAdded ?? [])
        {
            if (wanted.Contains(entry.Actor.FormKey) && actors.Add(entry.Actor.FormKey))
            {
                patch.PersistentActorReferencesAdded.Add(entry.DeepCopy());
            }
        }
        Require(wanted.All(actors.Contains), "Whiterun did not receive all three CRF ACPR entries.");

        patch.WorldspaceCellsAdded.Clear();
        foreach (var entry in crf.WorldspaceCellsAdded ?? [])
        {
            patch.WorldspaceCellsAdded.Add(entry.DeepCopy());
        }
        Require(patch.WorldspaceCellsAdded.Count == (crf.WorldspaceCellsAdded?.Count ?? 0),
            "Whiterun did not receive CRF's ACEC block.");
        ClearCompression(patch);
    }

    private static void PatchKilkreath(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var (winner, crf) = LocationContexts(state, "019260:Skyrim.esm");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.PersistentActorReferencesAdded ??= [];
        foreach (var entry in crf.PersistentActorReferencesAdded ?? [])
        {
            if (!patch.PersistentActorReferencesAdded.Any(output => output.Actor.FormKey == entry.Actor.FormKey))
            {
                patch.PersistentActorReferencesAdded.Add(entry.DeepCopy());
            }
        }
        patch.PersistentActorReferencesRemoved ??= [];
        foreach (var entry in crf.PersistentActorReferencesRemoved ?? [])
        {
            if (!patch.PersistentActorReferencesRemoved.Any(output => output.FormKey == entry.FormKey))
            {
                patch.PersistentActorReferencesRemoved.Add(entry.FormKey);
            }
        }
        Require(patch.PersistentActorReferencesAdded.Any(entry =>
                entry.Actor.FormKey == FormKey.Factory("00183A:cutting room floor.esp")),
            "Kilkreath Herebane ACPR was not restored.");
        foreach (var removed in new[] { "093A3A:Skyrim.esm", "093A34:Skyrim.esm", "093A35:Skyrim.esm" })
        {
            var key = FormKey.Factory(removed);
            Require(patch.PersistentActorReferencesRemoved.Any(entry => entry.FormKey == key),
                $"Kilkreath removal {key} was not restored.");
        }
        ClearCompression(patch);
    }

    private static void PatchDushnikh(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var (winner, crf) = LocationContexts(state, "01F7FD:Skyrim.esm");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.LocationRefTypeReferencesRemoved ??= [];
        foreach (var entry in crf.LocationRefTypeReferencesRemoved ?? [])
        {
            if (!patch.LocationRefTypeReferencesRemoved.Any(output => output.FormKey == entry.FormKey))
            {
                patch.LocationRefTypeReferencesRemoved.Add(entry.FormKey);
            }
        }
        Require(patch.LocationRefTypeReferencesRemoved.Any(entry =>
                entry.FormKey == FormKey.Factory("06A904:Skyrim.esm")),
            "Dushnikh location-reference removal was not restored.");
        ClearCompression(patch);
    }

    private static void PatchTasiusResponse(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var key = FormKey.Factory("02129C:Skyrim.esm");
        var contexts = new FormLink<IDialogResponsesGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IDialogResponses, IDialogResponsesGetter>(state.LinkCache)
            .OrderBy(context => LoadPosition(state, context.ModKey))
            .ToArray();
        var winner = contexts[^1];
        var crf = contexts.Last(context => context.ModKey == Crf);
        var crfGetDead = crf.Record.Conditions.Single(condition => condition.Data is GetDeadConditionData);
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        var levelIndex = patch.Conditions.FindIndex(condition => condition.Data is GetLevelConditionData);
        Require(levelIndex >= 0, "Skyrim Unbound's stale player-level condition was not found.");
        patch.Conditions[levelIndex] = crfGetDead.DeepCopy();
        Require(patch.Conditions.Any(condition => condition.Data is GetGlobalValueConditionData),
            "Skyrim Unbound alternate-start global condition was not preserved.");
        Require(patch.Conditions.Count(condition => condition.Data is GetDeadConditionData) == 1,
            "CRF GetDead condition was not merged exactly once.");
        Require(!patch.Conditions.Any(condition => condition.Data is GetLevelConditionData),
            "Stale player-level condition remains after CRF semantic merge.");
        ClearCompression(patch);
    }

    private static (IModContext<ISkyrimMod, ISkyrimModGetter, ILocation, ILocationGetter> Winner,
        ILocationGetter Crf) LocationContexts(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        string formKey)
    {
        var contexts = new FormLink<ILocationGetter>(FormKey.Factory(formKey))
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ILocation, ILocationGetter>(state.LinkCache)
            .OrderBy(context => LoadPosition(state, context.ModKey))
            .ToArray();
        return (contexts[^1], contexts.Last(context => context.ModKey == Crf).Record);
    }

    private static int LoadPosition(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        ModKey modKey)
    {
        var position = 0;
        foreach (var listing in state.LoadOrder.ListedOrder)
        {
            if (listing.ModKey == modKey) return position;
            position++;
        }
        throw new InvalidOperationException($"Active context {modKey.FileName} is absent from the load order.");
    }

    private static void EnforceHardMasters(string outputPath)
    {
        var plugin = SkyrimMod.CreateFromBinary(outputPath, SkyrimRelease.SkyrimSE);
        plugin.ModHeader.MasterReferences.Clear();
        foreach (var master in RequiredMasters)
        {
            plugin.ModHeader.MasterReferences.Add(new MasterReference { Master = master });
        }
        var temporary = outputPath + ".masters.tmp";
        if (File.Exists(temporary)) File.Delete(temporary);
        plugin.BeginWrite
            .ToPath(temporary)
            .WithLoadOrder(RequiredMasters)
            .WithKnownMasters([])
            .NoMastersListContentCheck()
            .NoModKeySync()
            .Write();
        File.Move(temporary, outputPath, true);
        Console.WriteLine($"Declared hard masters ({RequiredMasters.Count}).");
    }

    private static bool TryGetOption(string[] args, string option, out string value)
    {
        for (var index = 0; index < args.Length - 1; index++)
        {
            if (string.Equals(args[index], option, StringComparison.OrdinalIgnoreCase))
            {
                value = args[index + 1];
                return true;
            }
        }
        value = string.Empty;
        return false;
    }

    private static void ClearCompression(IMajorRecord record) =>
        record.MajorRecordFlagsRaw &= ~CompressedRecordFlag;

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
