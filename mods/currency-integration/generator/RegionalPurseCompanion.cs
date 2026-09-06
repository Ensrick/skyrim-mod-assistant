using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace Ensrick.CurrencyIntegrationPatcher;

internal static class RegionalPurseCompanion
{
    private const int CompressedRecordFlag = 0x00040000;
    private static readonly ModKey Skyrim = ModKey.FromNameAndExtension("Skyrim.esm");
    private static readonly ModKey Update = ModKey.FromNameAndExtension("Update.esm");
    private static readonly ModKey BsAssets = ModKey.FromNameAndExtension("BSAssets.esm");
    private static readonly ModKey CoinPatch = ModKey.FromNameAndExtension("exchangeCurrency_patch_COIN.esp");
    private readonly record struct Outcome(FormKey Form, short Count);

    public static int Build(string dataFolder, string mainPluginPath, string policyPath, string outputPath)
    {
        var policy = Program.ReadPolicy(policyPath);
        Program.ValidatePolicy(policy);
        var companion = policy.Overrides.RegionalPurseCompanion;
        Program.Require(companion.OutputPlugin == Program.RegionalPursePlugin,
            $"Regional purse output must be {Program.RegionalPursePlugin}.");
        var outputKey = ModKey.FromNameAndExtension(companion.OutputPlugin);
        using var main = SkyrimMod.CreateFromBinaryOverlay(
            new ModPath(ModKey.FromNameAndExtension(Program.OutputPlugin), mainPluginPath), SkyrimRelease.SkyrimSE);
        Program.Require(main.ModKey == ModKey.FromNameAndExtension(Program.OutputPlugin) &&
                main.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small),
            "Regional purse companion requires the reviewed ESL-flagged main currency plugin.");
        using var skyrim = SkyrimMod.CreateFromBinaryOverlay(
            new ModPath(Skyrim, Path.Combine(dataFolder, Skyrim.FileName.String)), SkyrimRelease.SkyrimSE);
        var output = new SkyrimMod(outputKey, SkyrimRelease.SkyrimSE)
        {
            ModHeader =
            {
                Author = "Ensrick",
                Description = "Owned regional coin-purse FLOR clones and exact 1/10/100 denomination budgets.",
                Flags = SkyrimModHeader.HeaderFlag.Small,
            },
        };

        var nextTerminalId = ParseId(companion.TerminalFormIdBase);
        var expectedSizes = new[] { "Small", "Medium", "Large" };
        foreach (var familyPolicy in companion.Families)
        {
            var family = policy.Denominations.TieredFamilies.Single(item => item.Id == familyPolicy.FamilyId);
            var forms = family.Tiers.ToDictionary(pair => pair.Key,
                pair => pair.Value.FormKey is not null
                    ? FormKey.Factory(pair.Value.FormKey)
                    : new FormKey(main.ModKey, ParseId(pair.Value.FormId!)), StringComparer.Ordinal);
            foreach (var form in forms.Values.Where(form => form.ModKey == main.ModKey))
            {
                Program.Require(main.MiscItems.Any(item => item.FormKey == form),
                    $"{family.Id}: main plugin is missing owned denomination {form}.");
            }
            var terminalCache = new Dictionary<int, Outcome>();

            FormKey AllocateTerminal(string description)
            {
                Program.Require(nextTerminalId <= 0xFFF,
                    $"Regional purse companion exhausted ESL FormIDs while allocating {description}.");
                return new FormKey(outputKey, nextTerminalId++);
            }

            Outcome Vector(int amount, bool singleBreak, string label)
            {
                var vector = Program.DecomposeSeptims(amount, singleBreak);
                var parts = new[]
                {
                    (form: forms["copper"], count: vector.Copper),
                    (form: forms["silver"], count: vector.Silver),
                    (form: forms["gold"], count: vector.Gold),
                }.Where(item => item.count > 0).ToArray();
                Program.Require(parts.Length > 0 && Program.ValueOf(vector) == amount,
                    $"{family.Id}: purse amount {amount} failed value conservation.");
                if (parts.Length == 1) return new Outcome(parts[0].form, parts[0].count);
                var key = AllocateTerminal($"{family.Id} {amount} {label}");
                var list = NewList(key, $"Ensrick_RPX_{family.Id}_{amount}_{label}", LeveledItem.Flag.UseAll);
                foreach (var part in parts) Add(list, part.form, part.count);
                output.LeveledItems.Add(list);
                return new Outcome(key, 1);
            }

            Outcome Terminal(int amount)
            {
                if (terminalCache.TryGetValue(amount, out var cached)) return cached;
                var canonical = Vector(amount, false, "Canonical");
                if (Program.DecomposeSeptims(amount, false) == Program.DecomposeSeptims(amount, true))
                {
                    terminalCache.Add(amount, canonical);
                    return canonical;
                }
                var broken = Vector(amount, true, "SingleBreak");
                var selectorKey = AllocateTerminal($"{family.Id} {amount} 80/20 selector");
                var selector = NewList(selectorKey, $"Ensrick_RPX_{family.Id}_{amount}_80_20", 0);
                for (var choice = 0; choice < 5; choice++)
                {
                    var result = choice < 4 ? canonical : broken;
                    Add(selector, result.Form, result.Count);
                }
                output.LeveledItems.Add(selector);
                var outcome = new Outcome(selectorKey, 1);
                terminalCache.Add(amount, outcome);
                return outcome;
            }

            var floraBase = ParseId(familyPolicy.FloraFormIdBase);
            var budgetBase = ParseId(familyPolicy.BudgetFormIdBase);
            for (var size = 0; size < policy.Overrides.CoinPurses.Count; size++)
            {
                var sourcePolicy = policy.Overrides.CoinPurses[size];
                var sourceFloraKey = FormKey.Factory(sourcePolicy.FloraFormKey);
                var sourceFlora = skyrim.Florae.Single(item => item.FormKey == sourceFloraKey);
                Program.Require(sourceFlora.EditorID == sourcePolicy.FloraEditorId,
                    $"{sourceFloraKey}: vanilla purse FLOR identity changed.");
                var sourceName = sourceFlora.Name?.String;
                var sourceActivateText = sourceFlora.ActivateTextOverride?.String;
                Program.Require(!string.IsNullOrEmpty(sourceName) && !string.IsNullOrEmpty(sourceActivateText),
                    $"{sourceFloraKey}: vanilla purse localized FULL/RNAM did not resolve from the pinned game Data.");
                var budgetKey = new FormKey(outputKey, budgetBase + checked((uint)size));
                var budget = NewList(budgetKey,
                    $"Ensrick_{family.Id}_CoinPurse{expectedSizes[size]}Budget", 0);
                foreach (var amount in sourcePolicy.Counts)
                {
                    var outcome = Terminal(amount);
                    Add(budget, outcome.Form, outcome.Count);
                }
                output.LeveledItems.Add(budget);

                var floraKey = new FormKey(outputKey, floraBase + checked((uint)size));
                var flora = (Flora)((IMajorRecordGetter)sourceFlora).Duplicate(floraKey);
                flora.EditorID = $"Ensrick_{family.Id}_CoinPurse{expectedSizes[size]}";
                // The companion itself is intentionally non-localized. Materialize the source's
                // resolved target-language strings so its FULL/RNAM cannot retain dangling
                // Skyrim.esm StringIDs without matching companion sidecars.
                flora.Name = new TranslatedString(Language.English, sourceName);
                flora.ActivateTextOverride = new TranslatedString(Language.English, sourceActivateText);
                flora.Ingredient.SetTo(budgetKey);
                ClearCompression(flora);
                output.Florae.Add(flora);
            }
        }

        Program.Require(nextTerminalId == 0x997,
            $"Regional purse companion allocated through {nextTerminalId - 1:X6}, expected 000996.");
        var records = output.EnumerateMajorRecords().ToArray();
        Program.Require(records.Length == 405 && output.Florae.Count == 15 && output.LeveledItems.Count == 390 &&
                records.All(record => record.FormKey.ModKey == outputKey) && !records.Any(record => record.IsDeleted),
            "Regional purse companion record/type/ownership contract changed.");

        var requiredMasters = new[] { Skyrim, Update, BsAssets, CoinPatch, main.ModKey };
        foreach (var master in requiredMasters)
            output.ModHeader.MasterReferences.Add(new MasterReference { Master = master });
        var directory = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(directory)) Directory.CreateDirectory(directory);
        var temporary = outputPath + ".tmp";
        if (File.Exists(temporary)) File.Delete(temporary);
        try
        {
            output.BeginWrite.ToPath(temporary)
                .WithLoadOrder(requiredMasters)
                .WithKnownMasters([])
                .NoMastersListContentCheck()
                .NoModKeySync()
                .SingleThread()
                .Write();
            using (var check = SkyrimMod.CreateFromBinaryOverlay(
                       new ModPath(outputKey, temporary), SkyrimRelease.SkyrimSE))
            {
                Program.Require(check.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small) &&
                        check.ModHeader.MasterReferences.Select(item => item.Master).SequenceEqual(requiredMasters) &&
                        check.EnumerateMajorRecords().Count() == 405 &&
                        check.Florae.All(item => item.Name?.String == "Coin Purse" &&
                            item.ActivateTextOverride?.String == "Take"),
                    "Written regional purse companion failed header/master/record-count verification.");
            }
            File.Move(temporary, outputPath, true);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
        Console.WriteLine("Built 405-record regional purse companion: 15 FLORs, 15 budget selectors, and 375 shared exact 80/20 denomination lists.");
        return 0;
    }

    private static uint ParseId(string value) => uint.Parse(value,
        System.Globalization.NumberStyles.HexNumber, System.Globalization.CultureInfo.InvariantCulture);

    private static LeveledItem NewList(FormKey key, string editorId, LeveledItem.Flag flags) =>
        new(key, SkyrimRelease.SkyrimSE)
        {
            EditorID = editorId,
            Flags = flags,
            ChanceNone = new Percent(0.0),
            Entries = [],
        };

    private static void Add(ILeveledItem list, FormKey form, short count)
    {
        var entry = new LeveledItemEntry
        {
            Data = new LeveledItemEntryData { Level = 1, Count = count },
        };
        entry.Data.Reference.SetTo(form);
        list.Entries!.Add(entry);
    }

    private static void ClearCompression(IMajorRecord record) =>
        record.MajorRecordFlagsRaw &= ~CompressedRecordFlag;
}
