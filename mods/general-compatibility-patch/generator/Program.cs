using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Translations;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Synthesis;

namespace Ensrick.GeneralCompatibilityPatcher;

public static class Program
{
    public const string OutputPlugin = "Ensrick General Compatibility Patch.esp";
    public const string LuxOrbisCs = "Lux Orbis CS.esp";
    public const string Bruma = "BSHeartland.esm";

    internal static readonly IReadOnlyList<ModKey> RequiredMasters =
    [
        ModKey.FromNameAndExtension("Skyrim.esm"),
        ModKey.FromNameAndExtension("Dragonborn.esm"),
        ModKey.FromNameAndExtension("BSAssets.esm"),
        ModKey.FromNameAndExtension("BSHeartland.esm"),
        ModKey.FromNameAndExtension(LuxOrbisCs),
        ModKey.FromNameAndExtension("Water for ENB (Shades of Skyrim).esp"),
        ModKey.FromNameAndExtension("Water for ENB - Patch - Beyond Skyrim.esp"),
    ];

    private const int CompressedRecordFlag = 0x00040000;

    [Flags]
    internal enum WorldspaceFields
    {
        None = 0,
        Flags = 1 << 0,
        MaxHeight = 1 << 1,
        Parent = 1 << 2,
        Climate = 1 << 3,
        Location = 1 << 4,
        ObjectBoundsMax = 1 << 5,
    }

    internal sealed record WorldspaceTarget(
        FormKey FormKey,
        string EditorId,
        string SourcePlugin,
        WorldspaceFields Fields);

    internal sealed record CellTarget(
        FormKey FormKey,
        string EditorId,
        string SourcePlugin);

    internal static readonly IReadOnlyList<WorldspaceTarget> WorldspaceTargets =
    [
        Worldspace("000800", "Dragonborn.esm", "DLC2SolstheimWorld", LuxOrbisCs, WorldspaceFields.MaxHeight),
        Worldspace("016D71", "Skyrim.esm", "MarkarthWorld", LuxOrbisCs, WorldspaceFields.Flags | WorldspaceFields.MaxHeight),
        Worldspace("016BB4", "Skyrim.esm", "RiftenWorld", LuxOrbisCs, WorldspaceFields.Flags | WorldspaceFields.MaxHeight | WorldspaceFields.Parent),
        Worldspace("037EDF", "Skyrim.esm", "SolitudeWorld", LuxOrbisCs, WorldspaceFields.Flags | WorldspaceFields.MaxHeight | WorldspaceFields.Parent),
        Worldspace("02EE41", "Skyrim.esm", "Sovngarde", LuxOrbisCs, WorldspaceFields.MaxHeight),
        Worldspace("00003C", "Skyrim.esm", "Tamriel", LuxOrbisCs, WorldspaceFields.MaxHeight),
        Worldspace("01A26F", "Skyrim.esm", "WhiterunWorld", LuxOrbisCs, WorldspaceFields.MaxHeight | WorldspaceFields.Parent),
        Worldspace("01691D", "Skyrim.esm", "WindhelmWorld", LuxOrbisCs, WorldspaceFields.Flags | WorldspaceFields.MaxHeight | WorldspaceFields.Parent),
        Worldspace("0A764B", "BSHeartland.esm", "BSHeartland", Bruma, WorldspaceFields.Climate | WorldspaceFields.Location | WorldspaceFields.ObjectBoundsMax),
        Worldspace("060B7D", "BSHeartland.esm", "CYRBiomeTesting", Bruma, WorldspaceFields.Climate),
        Worldspace("0B95A6", "BSHeartland.esm", "CYRGreenLeafGlade", Bruma, WorldspaceFields.Climate),
        Worldspace("0717AE", "BSHeartland.esm", "CYRTestWorld", Bruma, WorldspaceFields.Climate),
    ];

    internal static readonly IReadOnlyList<CellTarget> CellTargets =
    [
        Cell("037EE9", "Skyrim.esm", "SolitudeOrigin", LuxOrbisCs),
        Cell("01A276", "Skyrim.esm", "WhiterunPlainsDistrict04", LuxOrbisCs),
    ];

    public static async Task<int> Main(string[] args)
    {
        if (args is ["--self-test"])
        {
            return SelfTest.Run();
        }

        if (args is ["--audit-links", var dataFolder, var loadOrderFile, var pluginPath])
        {
            return LinkAudit.Run(dataFolder, loadOrderFile, pluginPath);
        }

        var result = await SynthesisPipeline.Instance
            .AddPatch<ISkyrimMod, ISkyrimModGetter>(RunPatch, new PatcherPreferences
            {
                ExclusionMods =
                [
                    ModKey.FromNameAndExtension(OutputPlugin),
                    ModKey.FromNameAndExtension("Synthesis.esp"),
                    ModKey.FromNameAndExtension("Requiem for the Indifferent.esp"),
                    ModKey.FromNameAndExtension("Occlusion.esp"),
                    ModKey.FromNameAndExtension("DynDOLOD.esm"),
                ],
            })
            .SetTypicalOpen(GameRelease.SkyrimSE, OutputPlugin)
            .Run(args);
        if (result == 0 && TryGetOption(args, "--OutputPath", out var outputPath))
        {
            EnforceHardMasters(outputPath);
        }
        return result;
    }

    public static void RunPatch(IPatcherState<ISkyrimMod, ISkyrimModGetter> state)
    {
        var positions = state.LoadOrder.ListedOrder
            .Select((listing, index) => (listing.ModKey, index))
            .ToDictionary(item => item.ModKey, item => item.index);

        state.PatchMod.ModHeader.Author = "Ensrick";
        state.PatchMod.ModHeader.Description =
            "Generated override-only patch preserving Lux Orbis CS, Water for ENB, and Bruma field ownership.";
        state.PatchMod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small;

        foreach (var target in WorldspaceTargets
                     .OrderBy(target => target.FormKey.ModKey.FileName.String, StringComparer.Ordinal)
                     .ThenBy(target => target.FormKey.ID))
        {
            PatchWorldspace(state, positions, target);
        }

        foreach (var target in CellTargets
                     .OrderBy(target => target.FormKey.ModKey.FileName.String, StringComparer.Ordinal)
                     .ThenBy(target => target.FormKey.ID))
        {
            PatchCell(state, positions, target);
        }

        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        var worldspaces = records.Count(record => record is IWorldspaceGetter);
        var cells = records.Count(record => record is ICellGetter);
        if (records.Length != 14 || worldspaces != 12 || cells != 2)
        {
            throw new InvalidOperationException(
                $"Structural invariant failed: expected 14 overrides (12 WRLD, 2 CELL), got " +
                $"{records.Length} ({worldspaces} WRLD, {cells} CELL).");
        }

        if (records.Any(record => record.FormKey.ModKey == state.PatchMod.ModKey))
        {
            throw new InvalidOperationException("The patch contains a newly allocated FormKey.");
        }

        Console.WriteLine("Generated 14 override-only records: 12 WRLD and 2 CELL.");
        Console.WriteLine($"Output: {OutputPlugin} (ESL-flagged ESP)");
    }

    private static void PatchWorldspace(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyDictionary<ModKey, int> positions,
        WorldspaceTarget target)
    {
        var contexts = new FormLink<IWorldspaceGetter>(target.FormKey)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IWorldspace, IWorldspaceGetter>(state.LinkCache)
            .Where(context => positions.ContainsKey(context.ModKey))
            .OrderBy(context => positions[context.ModKey])
            .ToArray();

        var winner = contexts.LastOrDefault()
            ?? throw MissingRecord(target.FormKey, "final active winner");
        var source = contexts.LastOrDefault(context => string.Equals(
            context.ModKey.FileName.String,
            target.SourcePlugin,
            StringComparison.OrdinalIgnoreCase))
            ?? throw MissingRecord(target.FormKey, target.SourcePlugin);

        RequireEditorId(target.FormKey, target.EditorId, winner.Record.EditorID);
        RequireEditorId(target.FormKey, target.EditorId, source.Record.EditorID);

        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        CopyWorldspaceFields(patch, source.Record, target.Fields);
        ClearCompression(patch);

        Console.WriteLine(
            $"WRLD {target.FormKey} {target.EditorId}: base={winner.ModKey.FileName}, " +
            $"source={source.ModKey.FileName}, fields={target.Fields}");
    }

    private static void PatchCell(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyDictionary<ModKey, int> positions,
        CellTarget target)
    {
        var contexts = new FormLink<ICellGetter>(target.FormKey)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ICell, ICellGetter>(state.LinkCache)
            .Where(context => positions.ContainsKey(context.ModKey))
            .OrderBy(context => positions[context.ModKey])
            .ToArray();

        var winner = contexts.LastOrDefault()
            ?? throw MissingRecord(target.FormKey, "final active winner");
        var source = contexts.LastOrDefault(context => string.Equals(
            context.ModKey.FileName.String,
            target.SourcePlugin,
            StringComparison.OrdinalIgnoreCase))
            ?? throw MissingRecord(target.FormKey, target.SourcePlugin);

        RequireEditorId(target.FormKey, target.EditorId, winner.Record.EditorID);
        RequireEditorId(target.FormKey, target.EditorId, source.Record.EditorID);

        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.Location.SetTo(source.Record.Location);
        ClearCompression(patch);

        Console.WriteLine(
            $"CELL {target.FormKey} {target.EditorId}: base={winner.ModKey.FileName}, " +
            $"source={source.ModKey.FileName}, fields=Location");
    }

    internal static void CopyWorldspaceFields(
        IWorldspace target,
        IWorldspaceGetter source,
        WorldspaceFields fields)
    {
        if (fields.HasFlag(WorldspaceFields.Flags))
        {
            target.Flags = source.Flags;
        }

        if (fields.HasFlag(WorldspaceFields.MaxHeight))
        {
            target.MaxHeight = source.MaxHeight?.DeepCopy();
        }

        if (fields.HasFlag(WorldspaceFields.Parent))
        {
            target.Parent = source.Parent?.DeepCopy();
        }

        if (fields.HasFlag(WorldspaceFields.Climate))
        {
            target.Climate.SetTo(source.Climate);
        }

        if (fields.HasFlag(WorldspaceFields.Location))
        {
            target.Location.SetTo(source.Location);
        }

        if (fields.HasFlag(WorldspaceFields.ObjectBoundsMax))
        {
            target.ObjectBoundsMax = source.ObjectBoundsMax;
        }
    }

    private static void ClearCompression(IMajorRecord record)
    {
        record.MajorRecordFlagsRaw &= ~CompressedRecordFlag;
    }

    private static void EnforceHardMasters(string outputPath)
    {
        // The ordinary Mutagen writer correctly infers masters from FormLinks,
        // but Lux Orbis CS contributes only scalar/vanilla-linked fields here.
        // Reopen the generated plugin and preserve the reviewed semantic master
        // list explicitly rather than manufacturing a record reference.
        var plugin = SkyrimMod.CreateFromBinary(outputPath, SkyrimRelease.SkyrimSE);
        plugin.ModHeader.MasterReferences.Clear();
        foreach (var master in RequiredMasters)
        {
            plugin.ModHeader.MasterReferences.Add(new MasterReference
            {
                Master = master,
            });
        }

        var temporary = outputPath + ".masters.tmp";
        if (File.Exists(temporary))
        {
            File.Delete(temporary);
        }
        plugin.BeginWrite
            .ToPath(temporary)
            .WithLoadOrder(RequiredMasters)
            .WithKnownMasters([])
            .NoMastersListContentCheck()
            .NoModKeySync()
            .Write();
        File.Move(temporary, outputPath, true);
        Console.WriteLine($"Declared hard masters ({RequiredMasters.Count}): " +
                          string.Join(", ", RequiredMasters.Select(master => master.FileName.String)));
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

    private static void RequireEditorId(FormKey formKey, string expected, string? actual)
    {
        if (!string.Equals(expected, actual, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"EditorID invariant failed for {formKey}: expected {expected}, found {actual ?? "<null>"}.");
        }
    }

    private static InvalidOperationException MissingRecord(FormKey formKey, string source) =>
        new($"Required record {formKey} was not found in {source}.");

    private static WorldspaceTarget Worldspace(
        string id,
        string master,
        string editorId,
        string source,
        WorldspaceFields fields) =>
        new(Form(id, master), editorId, source, fields);

    private static CellTarget Cell(string id, string master, string editorId, string source) =>
        new(Form(id, master), editorId, source);

    private static FormKey Form(string id, string master) =>
        new(ModKey.FromNameAndExtension(master), Convert.ToUInt32(id, 16));
}
