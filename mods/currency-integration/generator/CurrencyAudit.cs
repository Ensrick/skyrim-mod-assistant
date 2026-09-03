using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace Ensrick.CurrencyIntegrationPatcher;

internal static class CurrencyAudit
{
    private static readonly FormKey GoldPile01 = FormKey.Factory("018486:Dragonborn.esm");
    private static readonly FormKey GoldPile02 = FormKey.Factory("018488:Dragonborn.esm");
    private static readonly FormKey Gold001 = FormKey.Factory("00000F:Skyrim.esm");
    private static readonly FormKey GiftUniversallyValuable = FormKey.Factory("0A0E55:Skyrim.esm");
    private static readonly FormKey MintConvert = FormKey.Factory("DE5037:Update.esm");
    private static readonly FormKey CoinManager = FormKey.Factory("00084B:C.O.I.N.esp");
    private static readonly FormKey MintFramework = FormKey.Factory("000800:M.I.N.T.esp");
    private static readonly FormKey PlayerRef = FormKey.Factory("000014:Skyrim.esm");

    public static int WriteSeq(string pluginPath, string seqPath)
    {
        using var plugin = SkyrimMod.CreateFromBinaryOverlay(pluginPath, SkyrimRelease.SkyrimSE);
        var quests = plugin.Quests.Where(record => record.FormKey.ModKey == plugin.ModKey &&
                record.Flags.HasFlag(Quest.Flag.StartGameEnabled))
            .OrderBy(record => record.FormKey.ID).ToArray();
        Program.Require(quests.Length == 2 &&
                quests[0].EditorID == Program.RuntimeQuestEditorId &&
                quests[0].FormKey.ID == Program.RuntimeQuestId &&
                quests[1].EditorID == Program.OhzerQuestEditorId &&
                quests[1].FormKey.ID == Program.OhzerQuestId,
            "The owned Start Game Enabled quest set differs from 000800/000803.");
        var masterCount = plugin.ModHeader.MasterReferences.Count;
        Program.Require(masterCount <= byte.MaxValue, "SEQ file-relative index does not fit in one byte.");
        var fileRelativeFormIds = quests.Select(quest =>
            ((uint)masterCount << 24) | quest.FormKey.ID).ToArray();
        var bytes = fileRelativeFormIds.SelectMany(BitConverter.GetBytes).ToArray();
        var directory = Path.GetDirectoryName(seqPath);
        if (!string.IsNullOrEmpty(directory)) Directory.CreateDirectory(directory);
        File.WriteAllBytes(seqPath, bytes);
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            quests = quests.Select(quest => quest.FormKey.ToString()).ToArray(),
            masterCount,
            fileRelativeFormIds = fileRelativeFormIds.Select(value => value.ToString("X8")).ToArray(),
            bytes = Convert.ToHexString(bytes),
        }));
        return 0;
    }

    public static int Run(
        string dataFolder,
        string loadOrderFile,
        string pluginPath,
        string policyPath,
        string seqPath,
        string outputPath)
    {
        var policy = Program.ReadPolicy(policyPath);
        Program.ValidatePolicy(policy);
        var modKeys = LoadOrderFile.Read(loadOrderFile);
        using var loadOrder = LoadOrder.Import<ISkyrimModGetter>(
            new DirectoryPath(dataFolder),
            modKeys,
            GameRelease.SkyrimSE,
            factory: modPath => SkyrimMod.CreateFromBinaryOverlay(modPath.Path, SkyrimRelease.SkyrimSE));
        using var plugin = SkyrimMod.CreateFromBinaryOverlay(pluginPath, SkyrimRelease.SkyrimSE);

        var providerListing = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.Exchange);
        var provider = providerListing.Mod
            ?? throw new InvalidOperationException($"{Program.Exchange}: active source plugin could not be loaded.");
        Program.ValidateExchangeWorkbenchProvider(
            provider,
            Path.Combine(dataFolder, policy.ExchangeWorkbenchProvider.Plugin),
            policy.ExchangeWorkbenchProvider);

        Program.Require(plugin.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small),
            "Plugin is not ESL-flagged.");
        var actualMasters = plugin.ModHeader.MasterReferences.Select(reference => reference.Master).ToArray();
        Program.Require(actualMasters.SequenceEqual(Program.RequiredMasters),
            $"Hard-master set/order mismatch: {string.Join(", ", actualMasters.Select(key => key.FileName.String))}.");

        var records = plugin.EnumerateMajorRecords().ToArray();
        Program.Require(records.Length == 45, $"Expected exactly 45 records, found {records.Length}.");
        Program.Require(!records.Any(record => record.IsDeleted), "Plugin contains a deleted record.");
        var derivedMasters = records
            .Select(record => record.FormKey.ModKey)
            .Concat(records.SelectMany(record => record.EnumerateFormLinks())
                .Where(link => !link.FormKey.IsNull)
                .Select(link => link.FormKey.ModKey))
            .Where(master => master != plugin.ModKey)
            .ToHashSet();
        Program.Require(derivedMasters.SetEquals(actualMasters),
            $"Master list is not minimal/exact. Derived: {string.Join(", ", derivedMasters.Select(key => key.FileName.String).Order())}.");

        var expectedOverrideKeys = policy.Overrides.GoldPiles.Select(item => FormKey.Factory(item.FormKey))
            .Concat(policy.Overrides.CoinPurses.Select(item => FormKey.Factory(item.FormKey)))
            .Append(FormKey.Factory(policy.Overrides.Gold.FormKey))
            .Append(FormKey.Factory(policy.Overrides.MintAutoConvert.FormKey))
            .Append(FormKey.Factory(policy.Overrides.EceAltCurrencyQuest.FormKey))
            .Append(FormKey.Factory(policy.Overrides.MintMadranQuest.FormKey))
            .Append(FormKey.Factory(policy.Overrides.EceSeptimQuest.FormKey))
            .Concat(policy.Overrides.DrakrPurseAdapters.Purses.Select(item => FormKey.Factory(item.FormKey)))
            .Append(FormKey.Factory(policy.Overrides.DrakrPile.FormKey))
            .Concat(policy.DisabledRecipes.Select(item => FormKey.Factory(item.FormKey)))
            .ToHashSet();
        var actualOverrideKeys = records
            .Where(record => record.FormKey.ModKey != plugin.ModKey)
            .Select(record => record.FormKey)
            .ToHashSet();
        Program.Require(actualOverrideKeys.SetEquals(expectedOverrideKeys),
            "Override FormKey set differs from policy.json.");
        var expectedOwnedKeys = new HashSet<FormKey>
        {
            new(plugin.ModKey, Program.RuntimeQuestId),
            new(plugin.ModKey, 0x801),
            new(plugin.ModKey, 0x802),
            new(plugin.ModKey, Program.OhzerQuestId),
        };
        expectedOwnedKeys.UnionWith(policy.Overrides.AncientExchangeRecipes.Select(target =>
            new FormKey(plugin.ModKey, uint.Parse(target.FormId,
                System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture))));
        var actualOwnedKeys = records.Where(record => record.FormKey.ModKey == plugin.ModKey)
            .Select(record => record.FormKey).ToHashSet();
        Program.Require(actualOwnedKeys.SetEquals(expectedOwnedKeys),
            "Owned FormKey set differs from the exact two-LVLI/two-quest/eight-exchange policy.");

        AuditPiles(plugin, loadOrder);
        var purseReceipts = AuditPurses(plugin, policy.Overrides.CoinPurses);

        var gold = plugin.MiscItems.Single(record => record.FormKey == Gold001);
        Program.Require(gold.Keywords?.Count(link => link.FormKey == GiftUniversallyValuable) == 1,
            "Gold001 does not forward GiftUniversallyValuable exactly once.");

        var mint = plugin.Globals.Single(record => record.FormKey == MintConvert);
        Program.Require(mint is IGlobalShortGetter, "DES_ConvertCoins is not a GlobalShort.");
        var shortGlobal = (IGlobalShortGetter)mint;
        Program.Require(shortGlobal.Data is 0, $"DES_ConvertCoins is {shortGlobal.Data}, expected 0.");

        var eceAltCoinBindings = AuditEceQuest(plugin, loadOrder,
            policy.Overrides.EceAltCurrencyQuest, policy.Overrides.EceAltCoinBindings);
        var ohzerReceipt = AuditOhzerQuest(plugin, loadOrder, policy.Overrides.OhzerQuest);
        var madranReceipt = AuditMadranQuest(plugin, loadOrder, policy.Overrides.MintMadranQuest);
        var staleVmadReceipt = AuditEceSeptimQuest(plugin, loadOrder, policy.Overrides.EceSeptimQuest);
        var drakrPurseReceipt = AuditDrakrPurseAdapters(plugin, loadOrder,
            policy.Overrides.DrakrPurseAdapters);
        var drakrPileReceipt = AuditDrakrPile(plugin, loadOrder, policy.Overrides.DrakrPile);

        var disabled = new List<object>();
        foreach (var target in policy.DisabledRecipes)
        {
            var key = FormKey.Factory(target.FormKey);
            var recipe = plugin.ConstructibleObjects.Single(record => record.FormKey == key);
            Program.Require(recipe.EditorID == target.EditorId,
                $"{key}: EditorID changed to {recipe.EditorID}.");
            Program.Require(recipe.WorkbenchKeyword.IsNull,
                $"{key} {target.EditorId}: WorkbenchKeyword is not null.");
            disabled.Add(new { formKey = key.ToString(), target.EditorId });
        }
        var ancientExchangeReceipts = AuditAncientExchangeRecipes(plugin, policy.Overrides);

        var quest = plugin.Quests.Single(record => record.EditorID == Program.RuntimeQuestEditorId);
        AuditQuest(quest, plugin.ModKey);
        var ohzerQuest = plugin.Quests.Single(record =>
            record.EditorID == policy.Overrides.OhzerQuest.EditorId);
        var seqBytes = File.ReadAllBytes(seqPath);
        Program.Require(seqBytes.Length == 8, $"SEQ must contain two FormIDs (8 bytes), found {seqBytes.Length} bytes.");
        var expectedSeqId = ((uint)actualMasters.Length << 24) | Program.RuntimeQuestId;
        var ohzerQuestId = uint.Parse(policy.Overrides.OhzerQuest.FormId,
            System.Globalization.NumberStyles.HexNumber,
            System.Globalization.CultureInfo.InvariantCulture);
        var expectedOhzerSeqId = ((uint)actualMasters.Length << 24) | ohzerQuestId;
        var actualSeqIds = new[] { BitConverter.ToUInt32(seqBytes, 0), BitConverter.ToUInt32(seqBytes, 4) };
        Program.Require(actualSeqIds.SequenceEqual(new[] { expectedSeqId, expectedOhzerSeqId }),
            $"SEQ contains {string.Join(", ", actualSeqIds.Select(value => value.ToString("X8")))}, " +
            $"expected {expectedSeqId:X8}, {expectedOhzerSeqId:X8}.");

        var receipt = new
        {
            schemaVersion = 1,
            plugin = plugin.ModKey.FileName.String,
            eslFlag = true,
            masters = actualMasters.Select(master => master.FileName.String).ToArray(),
            masterMinimality = new
            {
                derivedDirectMasters = derivedMasters.Select(master => master.FileName.String).Order().ToArray(),
                exact = true,
            },
            records = records.Length,
            exchangeWorkbenchProvider = new
            {
                plugin = policy.ExchangeWorkbenchProvider.Plugin,
                formKey = policy.ExchangeWorkbenchProvider.FormKey,
                editorId = policy.ExchangeWorkbenchProvider.EditorId,
                sha256 = policy.ExchangeWorkbenchProvider.Sha256,
                bytes = policy.ExchangeWorkbenchProvider.Bytes,
                records = policy.ExchangeWorkbenchProvider.Records,
                smallFlag = true,
                exactWinningBinary = true,
            },
            exactOverrides = actualOverrideKeys.OrderBy(key => key.ModKey.FileName.String).ThenBy(key => key.ID)
                .Select(key => key.ToString()).ToArray(),
            deletedRecords = 0,
            coinPurses = purseReceipts,
            eceDrakrVmadRepair = new
            {
                formKey = policy.Overrides.EceAltCurrencyQuest.FormKey,
                script = policy.Overrides.EceAltCurrencyQuest.Script,
                property = policy.Overrides.EceAltCurrencyQuest.Property,
                source = policy.Overrides.EceAltCurrencyQuest.SourceFormKey,
                target = policy.Overrides.EceAltCurrencyQuest.TargetFormKey,
            },
            eceInheritedAltCoinBindings = eceAltCoinBindings,
            ohzerTransactionScript = ohzerReceipt,
            madranScriptMigration = madranReceipt,
            removedStaleVmadProperties = staleVmadReceipt,
            drakrPurseAdapters = drakrPurseReceipt,
            drakrPileRepair = drakrPileReceipt,
            disabledRecipeCount = disabled.Count,
            disabledRecipes = disabled,
            ancientExchangeRecipes = ancientExchangeReceipts,
            runtimeQuest = new
            {
                formKey = quest.FormKey.ToString(),
                quest.EditorID,
                startGameEnabled = true,
                alias = quest.Aliases.Single().Name,
                script = Program.RuntimeScriptName,
                seqFileRelativeFormId = expectedSeqId.ToString("X8"),
                seqBytes = Convert.ToHexString(seqBytes),
            },
            ohzerQuest = new
            {
                formKey = ohzerQuest.FormKey.ToString(),
                ohzerQuest.EditorID,
                startGameEnabled = true,
                alias = ohzerQuest.Aliases.Single().Name,
                script = policy.Overrides.OhzerQuest.Script,
                seqFileRelativeFormId = expectedOhzerSeqId.ToString("X8"),
            },
        };
        File.WriteAllText(outputPath, JsonSerializer.Serialize(receipt, new JsonSerializerOptions { WriteIndented = true }) + "\n");
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            records = records.Length,
            disabledRecipes = disabled.Count,
            ancientExchangeRecipes = ancientExchangeReceipts.Count,
            seq = actualSeqIds.Select(value => value.ToString("X8")).ToArray(),
            noDeletions = true,
        }));
        return 0;
    }

    private static IReadOnlyList<object> AuditPurses(
        ISkyrimModGetter plugin,
        IReadOnlyList<Program.PurseTarget> targets)
    {
        var receipts = new List<object>();
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var purse = plugin.LeveledItems.Single(record => record.FormKey == key);
            Program.Require(purse.EditorID == target.EditorId,
                $"{key}: purse EditorID differs from policy.");
            Program.Require(purse.Flags == 0, $"{key}: purse LVLI flags must be empty (UseAll is forbidden).");
            Program.Require((double)purse.ChanceNone == 0.0, $"{key}: purse ChanceNone must be zero.");
            Program.Require(purse.Global.IsNull, $"{key}: purse chance-global must be null.");
            var entries = purse.Entries ?? throw new InvalidOperationException($"{key}: purse entries are null.");
            Program.Require(entries.Count == 16, $"{key}: purse must have 16 equal-choice entries.");
            var counts = entries.Select(entry => entry.Data?.Count
                ?? throw new InvalidOperationException($"{key}: purse entry data is null.")).ToArray();
            Program.Require(counts.SequenceEqual(target.Counts), $"{key}: purse count sequence differs from policy.");
            Program.Require(counts.Distinct().Count() == 16, $"{key}: purse counts are not unique.");
            Program.Require(entries.All(entry => entry.Data?.Level == 1), $"{key}: every purse entry must be level 1.");
            Program.Require(entries.All(entry => entry.Data?.Reference.FormKey == Gold001),
                $"{key}: every purse entry must use hidden Gold001.");
            receipts.Add(new
            {
                formKey = key.ToString(),
                target.EditorId,
                entries = counts.Length,
                min = counts.Min(),
                max = counts.Max(),
                mean = counts.Average(value => (double)value),
                counts,
                useAll = false,
                chanceNone = 0,
                global = "Null",
            });
        }
        return receipts;
    }

    private static void AuditPiles(ISkyrimModGetter plugin, ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder)
    {
        var ece = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.Ece).Mod
            ?? throw new InvalidOperationException("ECE is not loaded.");
        foreach (var key in new[] { GoldPile01, GoldPile02 })
        {
            var expected = ece.Activators.Single(record => record.FormKey == key);
            var actual = plugin.Activators.Single(record => record.FormKey == key);
            Program.Require(actual.EditorID == expected.EditorID, $"{key}: ACTI EditorID differs from ECE.");
            Program.Require(actual.Name?.String == expected.Name?.String, $"{key}: ACTI name differs from ECE.");
            Program.Require(string.Equals(actual.Model?.File.ToString(), expected.Model?.File.ToString(),
                    StringComparison.OrdinalIgnoreCase),
                $"{key}: ACTI model differs from ECE ({actual.Model?.File} != {expected.Model?.File}).");
            var expectedScript = expected.VirtualMachineAdapter?.Scripts.Single(entry => entry.Name == "DLC2GoldPileScript")
                ?? throw new InvalidOperationException($"{key}: ECE pile script is missing.");
            var actualScript = actual.VirtualMachineAdapter?.Scripts.Single(entry => entry.Name == "DLC2GoldPileScript")
                ?? throw new InvalidOperationException($"{key}: forwarded pile script is missing.");
            foreach (var propertyName in new[] { "Gold001", "ImperialLuck" })
            {
                var expectedProperty = expectedScript.Properties.OfType<IScriptObjectPropertyGetter>()
                    .Single(property => property.Name == propertyName);
                var actualProperty = actualScript.Properties.OfType<IScriptObjectPropertyGetter>()
                    .Single(property => property.Name == propertyName);
                Program.Require(actualProperty.Object.FormKey == expectedProperty.Object.FormKey,
                    $"{key}: {propertyName} differs from ECE.");
            }
        }
    }

    private static IReadOnlyList<object> AuditEceQuest(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.ScriptPropertyTarget target,
        IReadOnlyList<Program.InheritedCurrencyBinding> bindings)
    {
        var key = FormKey.Factory(target.FormKey);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.CoinPatch).Mod
            ?? throw new InvalidOperationException("ECE C.O.I.N. patch is not loaded.");
        var source = sourceMod.Quests.Single(record => record.FormKey == key);
        var actual = plugin.Quests.Single(record => record.FormKey == key);
        Program.Require(actual.EditorID == target.EditorId && actual.EditorID == source.EditorID,
            $"{key}: ECE alternate-currency quest identity changed.");
        Program.Require(actual.Flags == source.Flags && actual.NextAliasID == source.NextAliasID &&
                actual.Aliases.Count == source.Aliases.Count,
            $"{key}: non-VMAD quest structure differs from the vendor record.");

        var sourceAlias = source.VirtualMachineAdapter?.Aliases.Single(alias =>
            alias.Scripts.Any(script => script.Name == target.Script))
            ?? throw new InvalidOperationException($"{key}: source ECE alias/script is missing.");
        var actualAlias = actual.VirtualMachineAdapter?.Aliases.Single(alias =>
            alias.Scripts.Any(script => script.Name == target.Script))
            ?? throw new InvalidOperationException($"{key}: patched ECE alias/script is missing.");
        Program.Require(actualAlias.Scripts.Select(script => script.Name)
                .SequenceEqual(sourceAlias.Scripts.Select(script => script.Name)),
            $"{key}: ECE script list/order changed.");
        var receipts = new List<object>();
        foreach (var sourceScript in sourceAlias.Scripts)
        {
            var actualScript = actualAlias.Scripts.Single(script => script.Name == sourceScript.Name);
            var binding = bindings.SingleOrDefault(candidate => candidate.Script == sourceScript.Name);
            var expectedPropertyCount = sourceScript.Properties.Count + (binding is null ? 0 : 1);
            Program.Require(actualScript.Properties.Count == expectedPropertyCount,
                $"{key}: {sourceScript.Name} property count changed.");
            foreach (var sourceProperty in sourceScript.Properties)
            {
                var actualProperty = actualScript.Properties.Single(property =>
                    property.Name == sourceProperty.Name && property.GetType() == sourceProperty.GetType());
                if (sourceProperty is IScriptObjectPropertyGetter sourceObject &&
                    actualProperty is IScriptObjectPropertyGetter actualObject)
                {
                    var expected = sourceScript.Name == target.Script && sourceProperty.Name == target.Property
                        ? FormKey.Factory(target.TargetFormKey)
                        : sourceObject.Object.FormKey;
                    Program.Require(actualObject.Object.FormKey == expected,
                        $"{key}: {sourceScript.Name}.{sourceProperty.Name} is {actualObject.Object.FormKey}, expected {expected}.");
                }
                else if (sourceProperty is IScriptBoolPropertyGetter sourceBool &&
                         actualProperty is IScriptBoolPropertyGetter actualBool)
                {
                    Program.Require(actualBool.Data == sourceBool.Data,
                        $"{key}: {sourceScript.Name}.{sourceProperty.Name} bool value changed.");
                }
                else
                {
                    throw new InvalidOperationException(
                        $"{key}: unexpected ECE VMAD property type {sourceProperty.GetType().Name}.");
                }
            }
            if (binding is not null)
            {
                Program.Require(!sourceScript.Properties.Any(property => property.Name == "altCoins"),
                    $"{key}: vendor now binds {binding.Script}.altCoins; review the owned repair.");
                var inherited = actualScript.Properties.OfType<IScriptObjectPropertyGetter>()
                    .Single(property => property.Name == "altCoins");
                var expectedCurrency = FormKey.Factory(binding.CurrencyFormKey);
                Program.Require(inherited.Object.FormKey == expectedCurrency,
                    $"{key}: {binding.Script}.altCoins is {inherited.Object.FormKey}, expected {expectedCurrency}.");
                var declaredCurrency = actualScript.Properties.OfType<IScriptObjectPropertyGetter>()
                    .Single(property => property.Name == binding.CurrencyProperty);
                Program.Require(declaredCurrency.Object.FormKey == expectedCurrency,
                    $"{key}: {binding.Script}.{binding.CurrencyProperty} no longer matches altCoins.");
                receipts.Add(new
                {
                    script = binding.Script,
                    inheritedProperty = "altCoins",
                    currencyProperty = binding.CurrencyProperty,
                    currency = expectedCurrency.ToString(),
                    vendorBindingWasAbsent = true,
                });
            }
        }
        var shipped = sourceAlias.Scripts.Single(script => script.Name == target.Script)
            .Properties.OfType<IScriptObjectPropertyGetter>()
            .Single(property => property.Name == target.Property);
        Program.Require(shipped.Object.FormKey == FormKey.Factory(target.SourceFormKey),
            $"{key}: vendor Drakr source no longer matches the pinned defect.");
        Program.Require(receipts.Count == bindings.Count,
            $"{key}: audited {receipts.Count} inherited altCoins bindings, expected {bindings.Count}.");
        return receipts;
    }

    private static object AuditOhzerQuest(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.OhzerQuestPolicy target)
    {
        var questId = uint.Parse(target.FormId, System.Globalization.NumberStyles.HexNumber,
            System.Globalization.CultureInfo.InvariantCulture);
        var key = new FormKey(plugin.ModKey, questId);
        var actual = plugin.Quests.Single(record => record.FormKey == key);
        Program.Require(actual.EditorID == target.EditorId &&
                actual.Flags.HasFlag(Quest.Flag.StartGameEnabled) &&
                !actual.Flags.HasFlag(Quest.Flag.RunOnce) && actual.NextAliasID == 1,
            $"{key}: owned Ohzer quest header changed.");
        var alias = actual.Aliases.Single();
        Program.Require(alias.ID == target.AliasId && alias.Name == target.AliasName &&
                alias.Type == QuestAlias.TypeEnum.Reference && alias.ForcedReference.FormKey == PlayerRef,
            $"{key}: owned Ohzer quest alias changed.");
        var actualAlias = actual.VirtualMachineAdapter?.Aliases.Single()
            ?? throw new InvalidOperationException($"{key}: owned Ohzer alias VMAD is missing.");
        Program.Require(actualAlias.Property.Object.FormKey == key &&
                actualAlias.Property.Alias == target.AliasId,
            $"{key}: owned Ohzer VMAD alias binding changed.");

        var templateKey = FormKey.Factory(target.TemplateQuestFormKey);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.CoinPatch).Mod
            ?? throw new InvalidOperationException("ECE C.O.I.N. patch is not loaded.");
        var source = sourceMod.Quests.Single(record => record.FormKey == templateKey);
        var sourceAlias = source.VirtualMachineAdapter?.Aliases.Single(aliasEntry =>
            aliasEntry.Property.Alias == 0)
            ?? throw new InvalidOperationException($"{templateKey}: ECE currency template alias is missing.");
        Program.Require(!sourceAlias.Scripts.Any(script => script.Name == target.Script),
            $"{templateKey}: vendor now supplies {target.Script}; review the owned implementation.");
        var template = sourceAlias.Scripts.Single(script => script.Name == target.TemplateScript);
        var actualScript = actualAlias.Scripts.Single(script => script.Name == target.Script);
        var expected = template.Properties.OfType<IScriptObjectPropertyGetter>()
            .Where(property => property.Name is not ("Oshka" or "OshkaPerk"))
            .ToDictionary(property => property.Name, property => property.Object.FormKey,
                StringComparer.Ordinal);
        expected.Add(target.CurrencyProperty, FormKey.Factory(target.CurrencyFormKey));
        expected.Add(target.KeywordProperty, FormKey.Factory(target.KeywordFormKey));
        var bindings = actualScript.Properties.OfType<IScriptObjectPropertyGetter>()
            .ToDictionary(property => property.Name, property => property.Object.FormKey,
                StringComparer.Ordinal);
        Program.Require(actualAlias.Scripts.Count == 1 &&
                actualScript.Properties.Count == expected.Count &&
                bindings.Count == expected.Count &&
                expected.All(pair => bindings.GetValueOrDefault(pair.Key) == pair.Value),
            $"{key}: owned Ohzer VMAD bindings differ from the template-derived contract.");
        return new
        {
            formKey = key.ToString(),
            aliasId = target.AliasId,
            script = target.Script,
            template = target.TemplateScript,
            currency = target.CurrencyFormKey,
            keyword = target.KeywordFormKey,
            neutralBarterRate = true,
            upgradeSafeNewQuest = true,
            bindings = expected.ToDictionary(pair => pair.Key, pair => pair.Value.ToString()),
        };
    }

    private static object AuditMadranQuest(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.ScriptMigrationTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.EceMintUlfric).Mod
            ?? throw new InvalidOperationException("ECE M.I.N.T. Ulfric patch is not loaded.");
        var source = sourceMod.Quests.Single(record => record.FormKey == key);
        var actual = plugin.Quests.Single(record => record.FormKey == key);
        Program.Require(actual.EditorID == target.EditorId && actual.EditorID == source.EditorID,
            $"{key}: Ma'dran quest identity changed.");
        Program.Require(actual.Flags == source.Flags && actual.NextAliasID == source.NextAliasID &&
                actual.Aliases.Count == source.Aliases.Count,
            $"{key}: non-VMAD Ma'dran quest structure differs from the vendor record.");

        var sourceAlias = source.VirtualMachineAdapter?.Aliases.Single(alias =>
            alias.Property.Alias == target.AliasId)
            ?? throw new InvalidOperationException($"{key}: source Ma'dran alias VMAD is missing.");
        var actualAlias = actual.VirtualMachineAdapter?.Aliases.Single(alias =>
            alias.Property.Alias == target.AliasId)
            ?? throw new InvalidOperationException($"{key}: patched Ma'dran alias VMAD is missing.");
        Program.Require(actualAlias.Property.Object.FormKey == sourceAlias.Property.Object.FormKey &&
                actualAlias.Property.Alias == sourceAlias.Property.Alias &&
                actualAlias.Scripts.Count == sourceAlias.Scripts.Count,
            $"{key}: Ma'dran VMAD alias structure changed unexpectedly.");

        var sourceScript = sourceAlias.Scripts.Single(script => script.Name == target.SourceScript);
        Program.Require(sourceAlias.Scripts.Count(script => script.Name == target.SourceScript) == 1,
            $"{key}: vendor Ma'dran script identity is no longer unique.");
        var sourceObjects = sourceScript.Properties.OfType<IScriptObjectPropertyGetter>()
            .ToDictionary(property => property.Name, property => property.Object.FormKey, StringComparer.Ordinal);
        var expectedSource = new Dictionary<string, FormKey>(StringComparer.Ordinal)
        {
            ["CurrencyFunctions"] = FormKey.Factory("000800:M.I.N.T.esp"),
            ["DES_Ulfric"] = FormKey.Factory("DE5024:Update.esm"),
            ["DES_UlfricLocations"] = FormKey.Factory("000802:WindhelmUsesUlfrics.esp"),
            ["DES_WindhelmPriceAdjustmentPerk"] = FormKey.Factory("000800:WindhelmUsesUlfrics.esp"),
        };
        Program.Require(sourceScript.Properties.Count == expectedSource.Count &&
                sourceObjects.Count == expectedSource.Count &&
                expectedSource.All(pair => sourceObjects.GetValueOrDefault(pair.Key) == pair.Value),
            $"{key}: shipped orphan Ma'dran bindings differ from the pinned source contract.");

        Program.Require(!actualAlias.Scripts.Any(script => script.Name == target.SourceScript),
            $"{key}: orphan {target.SourceScript} attachment remains.");
        var actualScript = actualAlias.Scripts.Single(script => script.Name == target.TargetScript);
        var actualObjects = actualScript.Properties.OfType<IScriptObjectPropertyGetter>()
            .ToDictionary(property => property.Name, property => property.Object.FormKey, StringComparer.Ordinal);
        var expectedActual = new Dictionary<string, FormKey>(StringComparer.Ordinal)
        {
            ["CurrencyFunctions"] = FormKey.Factory("000800:M.I.N.T.esp"),
            ["PlayerRef"] = PlayerRef,
            ["akCurrency"] = FormKey.Factory("DE5024:Update.esm"),
            ["akSwapLocations"] = FormKey.Factory("000802:WindhelmUsesUlfrics.esp"),
            ["akPriceMod"] = FormKey.Factory("000800:WindhelmUsesUlfrics.esp"),
        };
        Program.Require(actualScript.Properties.Count == expectedActual.Count &&
                actualObjects.Count == expectedActual.Count &&
                expectedActual.All(pair => actualObjects.GetValueOrDefault(pair.Key) == pair.Value),
            $"{key}: migrated Ma'dran bindings differ from the current M.I.N.T. script contract.");

        var expectedScriptNames = sourceAlias.Scripts.Select(script =>
            script.Name == target.SourceScript ? target.TargetScript : script.Name);
        Program.Require(actualAlias.Scripts.Select(script => script.Name).SequenceEqual(expectedScriptNames),
            $"{key}: a Ma'dran VMAD script other than the intended migration changed.");

        var sourceVmad = source.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: source quest VMAD is missing.");
        var actualVmad = actual.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: patched quest VMAD is missing.");
        Program.Require(actualVmad.Scripts.Select(script => script.Name)
                .SequenceEqual(sourceVmad.Scripts.Select(script => script.Name)),
            $"{key}: top-level quest-fragment script list changed.");
        var staleQuestProperties = target.StaleQuestProperties.ToHashSet(StringComparer.Ordinal);
        foreach (var sourceTopScript in sourceVmad.Scripts)
        {
            var actualTopScript = actualVmad.Scripts.Single(script => script.Name == sourceTopScript.Name);
            var expectedProperties = sourceTopScript.Properties
                .Where(property => sourceTopScript.Name != "QF_DES_UlfricWindhelmService_03000002" ||
                                   !staleQuestProperties.Contains(property.Name))
                .ToArray();
            Program.Require(actualTopScript.Properties.Count == expectedProperties.Length,
                $"{key}: {sourceTopScript.Name} property count differs after stale-property cleanup.");
            for (var index = 0; index < expectedProperties.Length; index++)
            {
                AuditEquivalentProperty(key, sourceTopScript.Name, expectedProperties[index],
                    actualTopScript.Properties[index]);
            }
        }
        var sourceFragment = sourceVmad.Scripts.Single(script =>
            script.Name == "QF_DES_UlfricWindhelmService_03000002");
        var actualFragment = actualVmad.Scripts.Single(script =>
            script.Name == "QF_DES_UlfricWindhelmService_03000002");
        foreach (var propertyName in target.StaleQuestProperties)
        {
            Program.Require(sourceFragment.Properties.Count(property => property.Name == propertyName) == 1,
                $"{key}: pinned stale quest-fragment property {propertyName} is absent or ambiguous upstream.");
            Program.Require(!actualFragment.Properties.Any(property => property.Name == propertyName),
                $"{key}: stale quest-fragment property {propertyName} remains.");
        }

        return new
        {
            formKey = key.ToString(),
            aliasId = target.AliasId,
            sourceScript = target.SourceScript,
            targetScript = target.TargetScript,
            bindings = expectedActual.ToDictionary(pair => pair.Key, pair => pair.Value.ToString()),
            removedStaleQuestProperties = target.StaleQuestProperties,
            vendorPexBundled = false,
        };
    }

    private static IReadOnlyList<string> AuditEceSeptimQuest(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.StalePropertyTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.Ece).Mod
            ?? throw new InvalidOperationException("ECE is not loaded.");
        var source = sourceMod.Quests.Single(record => record.FormKey == key);
        var actual = plugin.Quests.Single(record => record.FormKey == key);
        Program.Require(actual.EditorID == target.EditorId && actual.EditorID == source.EditorID,
            $"{key}: ECE septim quest identity changed.");
        Program.Require(actual.Flags == source.Flags && actual.NextAliasID == source.NextAliasID &&
                actual.Aliases.Count == source.Aliases.Count,
            $"{key}: non-VMAD ECE septim quest structure differs from the vendor record.");

        var sourceAlias = source.VirtualMachineAdapter?.Aliases.Single()
            ?? throw new InvalidOperationException($"{key}: source ECE septim alias VMAD is missing.");
        var actualAlias = actual.VirtualMachineAdapter?.Aliases.Single()
            ?? throw new InvalidOperationException($"{key}: patched ECE septim alias VMAD is missing.");
        Program.Require(actualAlias.Property.Object.FormKey == sourceAlias.Property.Object.FormKey &&
                actualAlias.Property.Alias == sourceAlias.Property.Alias &&
                actualAlias.Scripts.Select(script => script.Name)
                    .SequenceEqual(sourceAlias.Scripts.Select(script => script.Name)),
            $"{key}: ECE septim VMAD alias/script structure changed unexpectedly.");

        var stale = target.StaleProperties.ToHashSet(StringComparer.Ordinal);
        foreach (var sourceScript in sourceAlias.Scripts)
        {
            var actualScript = actualAlias.Scripts.Single(script => script.Name == sourceScript.Name);
            var expectedProperties = sourceScript.Properties
                .Where(property => !stale.Contains($"{sourceScript.Name}.{property.Name}"))
                .ToArray();
            Program.Require(actualScript.Properties.Count == expectedProperties.Length,
                $"{key}: {sourceScript.Name} property count differs after stale-property cleanup.");
            for (var index = 0; index < expectedProperties.Length; index++)
            {
                AuditEquivalentProperty(key, sourceScript.Name, expectedProperties[index],
                    actualScript.Properties[index]);
            }
        }

        foreach (var qualified in target.StaleProperties)
        {
            var separator = qualified.LastIndexOf('.');
            var scriptName = qualified[..separator];
            var propertyName = qualified[(separator + 1)..];
            var sourceScript = sourceAlias.Scripts.Single(script => script.Name == scriptName);
            Program.Require(sourceScript.Properties.Count(property => property.Name == propertyName) == 1,
                $"{key}: pinned stale property {qualified} is absent or ambiguous in the vendor record.");
            var actualScript = actualAlias.Scripts.Single(script => script.Name == scriptName);
            Program.Require(!actualScript.Properties.Any(property => property.Name == propertyName),
                $"{key}: stale property {qualified} remains in the patch.");
        }
        return target.StaleProperties.ToArray();
    }

    private static void AuditEquivalentProperty(
        FormKey record,
        string scriptName,
        IScriptPropertyGetter expected,
        IScriptPropertyGetter actual)
    {
        Program.Require(actual.Name == expected.Name && actual.GetType() == expected.GetType(),
            $"{record}: {scriptName}.{expected.Name} identity/type changed.");
        if (expected is IScriptObjectPropertyGetter expectedObject &&
            actual is IScriptObjectPropertyGetter actualObject)
        {
            Program.Require(actualObject.Object.FormKey == expectedObject.Object.FormKey,
                $"{record}: {scriptName}.{expected.Name} object binding changed.");
            return;
        }
        if (expected is IScriptBoolPropertyGetter expectedBool &&
            actual is IScriptBoolPropertyGetter actualBool)
        {
            Program.Require(actualBool.Data == expectedBool.Data,
                $"{record}: {scriptName}.{expected.Name} bool value changed.");
            return;
        }
        throw new InvalidOperationException(
            $"{record}: unexpected VMAD property type {expected.GetType().Name} on {scriptName}.{expected.Name}.");
    }

    private static object AuditDrakrPurseAdapters(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.DrakrPursePolicy policy)
    {
        var coinMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.Coin).Mod
            ?? throw new InvalidOperationException("C.O.I.N. is not loaded.");
        var canonical = FormKey.Factory(policy.CanonicalCoin);
        var ownedBySource = new Dictionary<FormKey, FormKey>();
        var cloneReceipts = new List<object>();
        foreach (var target in policy.ChangeLists)
        {
            var sourceKey = FormKey.Factory(target.SourceFormKey);
            var ownedKey = new FormKey(plugin.ModKey, uint.Parse(target.FormId,
                System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture));
            var source = coinMod.LeveledItems.Single(record => record.FormKey == sourceKey);
            var actual = plugin.LeveledItems.Single(record => record.FormKey == ownedKey);
            Program.Require(source.EditorID == target.SourceEditorId && actual.EditorID == target.EditorId,
                $"{sourceKey}: Drakr adapter identity changed.");
            Program.Require(actual.Flags == source.Flags &&
                    (double)actual.ChanceNone == (double)source.ChanceNone &&
                    actual.Global.FormKey == source.Global.FormKey,
                $"{sourceKey}: owned Drakr change-list header differs from source.");
            var sourceEntries = source.Entries
                ?? throw new InvalidOperationException($"{sourceKey}: source Drakr change-list entries are null.");
            var actualEntries = actual.Entries
                ?? throw new InvalidOperationException($"{ownedKey}: owned Drakr change-list entries are null.");
            Program.Require(actualEntries.Count == sourceEntries.Count && actualEntries.Count == 4,
                $"{ownedKey}: owned Drakr change-list entry count changed.");
            for (var index = 0; index < sourceEntries.Count; index++)
            {
                var sourceData = sourceEntries[index].Data
                    ?? throw new InvalidOperationException($"{sourceKey}: source entry {index} is null.");
                var actualData = actualEntries[index].Data
                    ?? throw new InvalidOperationException($"{ownedKey}: owned entry {index} is null.");
                Program.Require(actualData.Level == sourceData.Level && actualData.Count == sourceData.Count &&
                        actualData.Reference.FormKey == canonical,
                    $"{ownedKey}: owned Drakr change-list entry {index} changed.");
            }
            ownedBySource.Add(sourceKey, ownedKey);
            cloneReceipts.Add(new
            {
                sourceFormKey = sourceKey.ToString(),
                ownedFormKey = ownedKey.ToString(),
                sourceEditorId = target.SourceEditorId,
                target.EditorId,
                canonicalCoin = canonical.ToString(),
            });
        }

        var expectedOwned = ownedBySource.Values.ToHashSet();
        var actualOwned = plugin.LeveledItems.Where(record => record.FormKey.ModKey == plugin.ModKey)
            .Select(record => record.FormKey).ToHashSet();
        Program.Require(actualOwned.SetEquals(expectedOwned),
            "Owned Drakr adapter LVLI set differs from policy.");

        var purseReceipts = new List<object>();
        foreach (var target in policy.Purses)
        {
            var key = FormKey.Factory(target.FormKey);
            var source = coinMod.LeveledItems.Single(record => record.FormKey == key);
            var actual = plugin.LeveledItems.Single(record => record.FormKey == key);
            Program.Require(actual.EditorID == source.EditorID && actual.EditorID == target.EditorId &&
                    actual.Flags == source.Flags &&
                    (double)actual.ChanceNone == (double)source.ChanceNone &&
                    actual.Global.FormKey == source.Global.FormKey,
                $"{key}: Drakr purse header differs from C.O.I.N.");
            var sourceEntries = source.Entries
                ?? throw new InvalidOperationException($"{key}: source Drakr purse entries are null.");
            var actualEntries = actual.Entries
                ?? throw new InvalidOperationException($"{key}: patched Drakr purse entries are null.");
            Program.Require(sourceEntries.Count == target.Entries.Count &&
                    actualEntries.Count == target.Entries.Count,
                $"{key}: Drakr purse entry count changed.");
            var mappedTargets = new List<string>();
            for (var index = 0; index < target.Entries.Count; index++)
            {
                var mapping = target.Entries[index];
                var sourceData = sourceEntries[index].Data
                    ?? throw new InvalidOperationException($"{key}: source purse entry {index} is null.");
                var actualData = actualEntries[index].Data
                    ?? throw new InvalidOperationException($"{key}: patched purse entry {index} is null.");
                var expectedTarget = mapping.TargetFormKey == "$canonical"
                    ? canonical
                    : ownedBySource[FormKey.Factory(mapping.SourceFormKey)];
                Program.Require(sourceData.Level == 1 && sourceData.Count == mapping.Count &&
                        sourceData.Reference.FormKey == FormKey.Factory(mapping.SourceFormKey) &&
                        actualData.Level == sourceData.Level && actualData.Count == sourceData.Count &&
                        actualData.Reference.FormKey == expectedTarget,
                    $"{key}: Drakr purse entry {index} differs from the pinned mapping.");
                mappedTargets.Add(expectedTarget.ToString());
            }
            purseReceipts.Add(new
            {
                formKey = key.ToString(),
                target.EditorId,
                mappedTargets,
                distributionPreserved = true,
            });
        }

        return new
        {
            canonicalCoin = canonical.ToString(),
            ownedChangeLists = cloneReceipts,
            purseOverrides = purseReceipts,
            sharedC_O_I_N_ChangeListsOverridden = false,
        };
    }

    private static object AuditDrakrPile(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.ScriptPropertyTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.Coin).Mod
            ?? throw new InvalidOperationException("C.O.I.N. is not loaded.");
        var source = sourceMod.Activators.Single(record => record.FormKey == key);
        var actual = plugin.Activators.Single(record => record.FormKey == key);
        Program.Require(actual.EditorID == source.EditorID && actual.EditorID == target.EditorId &&
                actual.Name?.String == source.Name?.String &&
                string.Equals(actual.Model?.File.ToString(), source.Model?.File.ToString(),
                    StringComparison.OrdinalIgnoreCase),
            $"{key}: Drakr pile identity/model changed.");
        var sourceScript = source.VirtualMachineAdapter?.Scripts.Single(script => script.Name == target.Script)
            ?? throw new InvalidOperationException($"{key}: source Drakr pile script is missing.");
        var actualScript = actual.VirtualMachineAdapter?.Scripts.Single(script => script.Name == target.Script)
            ?? throw new InvalidOperationException($"{key}: patched Drakr pile script is missing.");
        Program.Require(actualScript.Properties.Count == sourceScript.Properties.Count,
            $"{key}: Drakr pile property count changed.");
        foreach (var sourceProperty in sourceScript.Properties)
        {
            var actualProperty = actualScript.Properties.Single(property =>
                property.Name == sourceProperty.Name && property.GetType() == sourceProperty.GetType());
            if (sourceProperty is IScriptObjectPropertyGetter sourceObject &&
                actualProperty is IScriptObjectPropertyGetter actualObject)
            {
                var expected = sourceProperty.Name == target.Property
                    ? FormKey.Factory(target.TargetFormKey)
                    : sourceObject.Object.FormKey;
                Program.Require(actualObject.Object.FormKey == expected,
                    $"{key}: {target.Script}.{sourceProperty.Name} differs from the exact pile policy.");
            }
            else
            {
                AuditEquivalentProperty(key, target.Script, sourceProperty, actualProperty);
            }
        }
        var shipped = sourceScript.Properties.OfType<IScriptObjectPropertyGetter>()
            .Single(property => property.Name == target.Property);
        Program.Require(shipped.Object.FormKey == FormKey.Factory(target.SourceFormKey),
            $"{key}: shipped Drakr pile source no longer matches the pinned defect.");
        return new
        {
            formKey = key.ToString(),
            target.EditorId,
            script = target.Script,
            property = target.Property,
            source = target.SourceFormKey,
            target = target.TargetFormKey,
        };
    }

    private static IReadOnlyList<object> AuditAncientExchangeRecipes(
        ISkyrimModGetter plugin,
        Program.OverridePolicy policy)
    {
        var workbench = FormKey.Factory(policy.AncientExchangeWorkbench);
        var receipts = new List<object>();
        foreach (var target in policy.AncientExchangeRecipes)
        {
            var formId = uint.Parse(target.FormId,
                System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture);
            var key = new FormKey(plugin.ModKey, formId);
            var input = FormKey.Factory(target.InputFormKey);
            var output = FormKey.Factory(target.OutputFormKey);
            var recipe = plugin.ConstructibleObjects.Single(record => record.FormKey == key);
            Program.Require(!recipe.IsDeleted && recipe.EditorID == target.EditorId,
                $"{key}: owned ancient-exchange recipe identity changed.");
            Program.Require(recipe.Items is { Count: 1 },
                $"{key}: ancient-exchange recipe must have exactly one input.");
            var ingredient = recipe.Items![0].Item;
            Program.Require(ingredient.Item.FormKey == input && ingredient.Count == target.InputCount,
                $"{key}: ancient-exchange input differs from policy.");
            Program.Require(recipe.CreatedObject.FormKey == output &&
                    recipe.CreatedObjectCount == target.OutputCount &&
                    recipe.WorkbenchKeyword.FormKey == workbench,
                $"{key}: ancient-exchange output/workbench differs from policy.");
            Program.Require(recipe.Conditions.Count == 1 &&
                    recipe.Conditions[0] is IConditionFloatGetter,
                $"{key}: ancient-exchange recipe must have exactly one float condition.");
            var condition = (IConditionFloatGetter)recipe.Conditions[0];
            Program.Require(condition.CompareOperator == CompareOperator.GreaterThanOrEqualTo &&
                    condition.ComparisonValue == target.InputCount &&
                    condition.Data is IGetItemCountConditionDataGetter,
                $"{key}: ancient-exchange availability condition differs from policy.");
            var countData = (IGetItemCountConditionDataGetter)condition.Data;
            Program.Require(countData.ItemOrList.Link.FormKey == input,
                $"{key}: ancient-exchange GetItemCount target differs from policy.");
            receipts.Add(new
            {
                formKey = key.ToString(),
                editorId = target.EditorId,
                input = input.ToString(),
                inputCount = target.InputCount,
                output = output.ToString(),
                outputCount = target.OutputCount,
                workbench = workbench.ToString(),
                purpose = target.Purpose,
                oneWayCashout = true,
            });
        }
        return receipts;
    }

    private static void AuditQuest(IQuestGetter quest, ModKey pluginKey)
    {
        Program.Require(quest.FormKey == new FormKey(pluginKey, Program.RuntimeQuestId),
            "Runtime quest is not owned FormID 000800.");
        Program.Require(quest.EditorID == Program.RuntimeQuestEditorId, "Runtime quest EditorID differs.");
        Program.Require(quest.Flags.HasFlag(Quest.Flag.StartGameEnabled), "Runtime quest is not Start Game Enabled.");
        Program.Require(!quest.Flags.HasFlag(Quest.Flag.RunOnce), "Runtime quest must not be Run Once.");
        var alias = quest.Aliases.Single();
        Program.Require(alias.ID == 0 && alias.Type == QuestAlias.TypeEnum.Reference,
            "Runtime quest must own reference alias 0.");
        Program.Require(alias.ForcedReference.FormKey == PlayerRef, "Runtime alias is not forced to PlayerRef.");
        var vmadAlias = quest.VirtualMachineAdapter?.Aliases.Single()
            ?? throw new InvalidOperationException("Runtime quest alias VMAD is missing.");
        Program.Require(vmadAlias.Property.Object.FormKey == quest.FormKey && vmadAlias.Property.Alias == 0,
            "Runtime alias VMAD does not bind to alias 0.");
        var script = vmadAlias.Scripts.Single(entry => entry.Name == Program.RuntimeScriptName);
        var objectProperties = script.Properties.OfType<IScriptObjectPropertyGetter>()
            .ToDictionary(property => property.Name, property => property.Object.FormKey);
        Program.Require(objectProperties.Count == 3, "Runtime helper must expose exactly three object properties.");
        Program.Require(objectProperties.GetValueOrDefault("CoinManager") == CoinManager,
            "Runtime helper CoinManager property is wrong.");
        Program.Require(objectProperties.GetValueOrDefault("MintFramework") == MintFramework,
            "Runtime helper MintFramework property is wrong.");
        Program.Require(objectProperties.GetValueOrDefault("MintAutoConvert") == MintConvert,
            "Runtime helper MintAutoConvert property is wrong.");
    }
}
