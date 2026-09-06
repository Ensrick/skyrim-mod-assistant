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
    private static readonly FormKey VendorNoSale = FormKey.Factory("0FF9FB:Skyrim.esm");

    public static int WriteSeq(string pluginPath, string seqPath)
    {
        using var plugin = SkyrimMod.CreateFromBinaryOverlay(pluginPath, SkyrimRelease.SkyrimSE);
        var quests = plugin.Quests.Where(record => record.FormKey.ModKey == plugin.ModKey &&
                record.Flags.HasFlag(Quest.Flag.StartGameEnabled))
            .OrderBy(record => record.FormKey.ID).ToArray();
        Program.Require(quests.Length == 1 &&
                quests[0].EditorID == Program.RuntimeQuestEditorId &&
                quests[0].FormKey.ID == Program.RuntimeQuestId,
            "The owned Start Game Enabled quest set differs from the sole runtime quest 000800.");
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
        Program.Require(records.Length == 1772, $"Expected exactly 1772 records, found {records.Length}.");
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

        var expectedDialogParentKeys = policy.Overrides.DisabledMintExchangeInfos
            .Select(item => FormKey.Factory(item.ParentTopicFormKey))
            .Concat(policy.Overrides.MintBackendConditionInfos
                .Select(item => FormKey.Factory(item.ParentTopicFormKey)))
            .ToHashSet();
        Program.Require(expectedDialogParentKeys.Count == 20,
            "Exact parent DIAL policy must contain twenty unique FormKeys.");
        var expectedDenominationOverrides = ExpectedDenominationOverrides(loadOrder, policy.Denominations);
        var expectedOverrideKeys = policy.Overrides.GoldPiles.Select(item => FormKey.Factory(item.FormKey))
            .Concat(policy.Overrides.CoinPurses.Select(item => FormKey.Factory(item.FormKey)))
            .Append(FormKey.Factory(policy.Overrides.Gold.FormKey))
            .Append(FormKey.Factory(policy.Overrides.MintAutoConvert.FormKey))
            .Concat(policy.Overrides.EcePlayerCurrencyQuests.Select(item => FormKey.Factory(item.FormKey)))
            .Concat(policy.Overrides.MintCostOnlyQuests.Select(item => FormKey.Factory(item.FormKey)))
            .Append(FormKey.Factory(policy.Overrides.MintMadranQuest.FormKey))
            .Concat(policy.Overrides.RegionalPurseGraph.Families
                .SelectMany(family => family.Purses)
                .Select(item => FormKey.Factory(item.FormKey)))
            .Append(FormKey.Factory(policy.Overrides.DrakrPile.FormKey))
            .Concat(expectedDenominationOverrides)
            .Concat(policy.Overrides.DisabledMintExchangeInfos.Select(item => FormKey.Factory(item.FormKey)))
            .Concat(policy.Overrides.MintBackendConditionInfos.Select(item => FormKey.Factory(item.FormKey)))
            .Concat(expectedDialogParentKeys)
            .Concat(policy.DisabledRecipes.Select(item => FormKey.Factory(item.FormKey)))
            .Concat(policy.DisabledModernBankRecipes.Select(item => FormKey.Factory(item.FormKey)))
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
            new(plugin.ModKey, 0x803),
        };
        foreach (var family in policy.Denominations.TieredFamilies)
        {
            foreach (var tier in family.Tiers.Values.Where(tier => tier.FormId is not null))
            {
                expectedOwnedKeys.Add(new FormKey(plugin.ModKey, ParseId(tier.FormId!)));
            }
        }
        foreach (var purse in policy.Overrides.CoinPurses)
        {
            foreach (var baseId in new[] { purse.CanonicalFormIdBase, purse.BreakFormIdBase, purse.SelectorFormIdBase })
            {
                var start = ParseId(baseId);
                for (uint index = 0; index < purse.Counts.Count; index++)
                {
                    expectedOwnedKeys.Add(new FormKey(plugin.ModKey, start + index));
                }
            }
        }
        expectedOwnedKeys.UnionWith(policy.Overrides.AncientExchangeRecipes.Select(target =>
            new FormKey(plugin.ModKey, uint.Parse(target.FormId,
                System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture))));
        foreach (var id in Enumerable.Range(0x990, 0x70)
                     .Concat(Enumerable.Range(0xA16, 0x52A)))
        {
            expectedOwnedKeys.Add(new FormKey(plugin.ModKey, checked((uint)id)));
        }
        var actualOwnedKeys = records.Where(record => record.FormKey.ModKey == plugin.ModKey)
            .Select(record => record.FormKey).ToHashSet();
        Program.Require(actualOwnedKeys.SetEquals(expectedOwnedKeys),
            "Owned FormKey set differs from the exact denomination/purse/ancient/runtime policy.");

        AuditPiles(plugin, loadOrder);
        var denominationReceipt = AuditDenominations(plugin, loadOrder, policy.Denominations);
        var purseReceipts = AuditPurses(plugin, policy.Overrides.CoinPurses,
            policy.Denominations.TieredFamilies.Single(family => family.Id == "septim"));

        var gold = plugin.MiscItems.Single(record => record.FormKey == Gold001);
        Program.Require(gold.Keywords?.Count(link => link.FormKey == GiftUniversallyValuable) == 1,
            "Gold001 does not forward GiftUniversallyValuable exactly once.");

        var mint = plugin.Globals.Single(record => record.FormKey == MintConvert);
        Program.Require(mint is IGlobalShortGetter, "DES_ConvertCoins is not a GlobalShort.");
        var shortGlobal = (IGlobalShortGetter)mint;
        Program.Require(shortGlobal.Data is 0, $"DES_ConvertCoins is {shortGlobal.Data}, expected 0.");

        var neutralizedQuestReceipt = AuditNeutralizedQuests(plugin, loadOrder,
            policy.Overrides.EcePlayerCurrencyQuests);
        var mintCostOnlyReceipt = AuditMintCostOnlyQuests(plugin, loadOrder,
            policy.Overrides.MintCostOnlyQuests);
        var madranReceipt = AuditMadranRemoval(plugin, loadOrder, policy.Overrides.MintMadranQuest);
        var disabledMintInfoReceipt = AuditDisabledMintExchangeInfos(plugin, loadOrder,
            policy.Overrides.DisabledMintExchangeInfos);
        var backendConditionReceipt = AuditMintBackendConditions(plugin, loadOrder,
            policy.Overrides.MintBackendConditionInfos);
        var dialogParentReceipt = AuditDialogParentScopes(plugin, loadOrder,
            policy.Overrides.DisabledMintExchangeInfos, policy.Overrides.MintBackendConditionInfos);
        var regionalPurseReceipt = AuditRegionalPurseGraph(plugin,
            policy.Overrides.RegionalPurseGraph, policy.Denominations);
        var drakrPileReceipt = AuditDrakrPile(plugin, loadOrder, policy.Overrides.DrakrPile);

        var disabled = new List<object>();
        foreach (var target in policy.DisabledRecipes.Concat(policy.DisabledModernBankRecipes))
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
        var seqBytes = File.ReadAllBytes(seqPath);
        Program.Require(seqBytes.Length == 4, $"SEQ must contain one FormID (4 bytes), found {seqBytes.Length} bytes.");
        var expectedSeqId = ((uint)actualMasters.Length << 24) | Program.RuntimeQuestId;
        var actualSeqIds = new[] { BitConverter.ToUInt32(seqBytes, 0) };
        Program.Require(actualSeqIds.SequenceEqual(new[] { expectedSeqId }),
            $"SEQ contains {string.Join(", ", actualSeqIds.Select(value => value.ToString("X8")))}, " +
            $"expected {expectedSeqId:X8}.");

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
            runtimeReasonCounters = policy.RuntimeReasonCounters,
            denominations = denominationReceipt,
            coinPurses = purseReceipts,
            neutralizedEcePlayerCurrencyQuests = neutralizedQuestReceipt,
            mintCostOnlyQuestBindings = mintCostOnlyReceipt,
            madranTransactionRemoval = madranReceipt,
            disabledMintExchangeInfos = disabledMintInfoReceipt,
            mintBackendConditionInfos = backendConditionReceipt,
            dialogParentScopes = dialogParentReceipt,
            regionalPurseGraph = regionalPurseReceipt,
            drakrPileRepair = drakrPileReceipt,
            disabledRecipeCount = disabled.Count,
            disabledCurrencyToIngotRecipeCount = policy.DisabledRecipes.Count,
            disabledModernBankRecipeCount = policy.DisabledModernBankRecipes.Count,
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

    private static uint ParseId(string value) => uint.Parse(value,
        System.Globalization.NumberStyles.HexNumber, System.Globalization.CultureInfo.InvariantCulture);

    private static IMiscItemGetter ResolvePinnedSource(
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.SourceRecordPolicy policy,
        string description)
    {
        var key = FormKey.Factory(policy.FormKey);
        var sourceModKey = ModKey.FromNameAndExtension(policy.SourcePlugin);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == sourceModKey).Mod
            ?? throw new InvalidOperationException($"{sourceModKey}: {description} provider is not loaded.");
        var source = sourceMod.MiscItems.Single(record => record.FormKey == key);
        Program.Require(source.EditorID == policy.EditorId && source.Name?.String == policy.Name &&
                source.Value == policy.SourceValue &&
                Math.Abs(source.Weight - policy.SourceWeight) < 0.0001f &&
                string.Equals(source.Model?.File.ToString(), policy.SourceModel,
                    StringComparison.OrdinalIgnoreCase),
            $"{key}: pinned {description} identity/value/weight/model changed.");
        return source;
    }

    private static Program.SourceRecordPolicy ExistingTierSource(
        Program.TieredFamilyPolicy family,
        string tierName,
        Program.TierPolicy tier) =>
        tierName == "copper"
            ? family.PrimarySource
            : new Program.SourceRecordPolicy
            {
                FormKey = tier.FormKey!,
                SourcePlugin = tier.SourcePlugin ?? string.Empty,
                EditorId = tier.EditorId,
                Name = tier.SourceName ?? tier.Name,
                SourceValue = tier.SourceValue ?? uint.MaxValue,
                SourceWeight = tier.SourceWeight ?? float.NaN,
                SourceModel = tier.SourceModel ?? string.Empty,
            };

    private static bool NeedsTierOverride(
        IMiscItemGetter source,
        Program.TierPolicy tier,
        float runtimeWeight) =>
        source.Name?.String != tier.Name || source.Value != tier.Value ||
        Math.Abs(source.Weight - runtimeWeight) >= 0.0001f ||
        !string.Equals(source.Model?.File.ToString(), tier.Model, StringComparison.OrdinalIgnoreCase) ||
        !HasKeyword(source, VendorNoSale);

    private static HashSet<FormKey> ExpectedDenominationOverrides(
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.DenominationPolicy policy)
    {
        var result = new HashSet<FormKey>();
        foreach (var family in policy.TieredFamilies)
        {
            foreach (var (tierName, tier) in family.Tiers)
            {
                if (tier.FormKey is null) continue;
                var sourcePolicy = ExistingTierSource(family, tierName, tier);
                var source = ResolvePinnedSource(loadOrder, sourcePolicy,
                    $"{family.Id}/{tierName} existing tier");
                if (NeedsTierOverride(source, tier, family.RuntimeWeight))
                {
                    result.Add(source.FormKey);
                }
            }
            foreach (var alias in family.SourceAliases)
            {
                var source = ResolvePinnedSource(loadOrder, alias, $"{family.Id} source alias");
                var tier = family.Tiers[alias.NormalizesToTier];
                if (NeedsTierOverride(source, tier, family.RuntimeWeight))
                {
                    result.Add(source.FormKey);
                }
            }
        }
        return result;
    }

    private static object AuditDenominations(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.DenominationPolicy policy)
    {
        var familyReceipts = new List<object>();
        var physicalForms = new HashSet<FormKey>();
        foreach (var family in policy.TieredFamilies)
        {
            var primary = ResolvePinnedSource(loadOrder, family.PrimarySource, $"{family.Id} primary source");
            var tierReceipts = new List<object>();
            foreach (var tierName in new[] { "copper", "silver", "gold" })
            {
                var tier = family.Tiers[tierName];
                var owned = tier.FormId is not null;
                var key = owned
                    ? new FormKey(plugin.ModKey, ParseId(tier.FormId!))
                    : FormKey.Factory(tier.FormKey!);
                var source = owned
                    ? primary
                    : ResolvePinnedSource(loadOrder, ExistingTierSource(family, tierName, tier),
                        $"{family.Id}/{tierName} existing tier");
                var item = owned || NeedsTierOverride(source, tier, family.RuntimeWeight)
                    ? plugin.MiscItems.Single(record => record.FormKey == key)
                    : source;
                var expectedKeywords = (source.Keywords?.Select(keyword => keyword.FormKey) ?? [])
                    .Append(VendorNoSale).ToHashSet();
                Program.Require(item.EditorID == tier.EditorId && item.Value == tier.Value &&
                        item.Name?.String == tier.Name &&
                        Math.Abs(item.Weight - family.RuntimeWeight) < 0.0001f &&
                        string.Equals(item.Model?.File.ToString(), tier.Model,
                            StringComparison.OrdinalIgnoreCase) &&
                        item.PickUpSound.FormKey == source.PickUpSound.FormKey &&
                        item.PutDownSound.FormKey == source.PutDownSound.FormKey &&
                        HasKeyword(item, VendorNoSale) &&
                        (item.Keywords?.Select(keyword => keyword.FormKey) ?? [])
                            .ToHashSet().SetEquals(expectedKeywords),
                    $"{key}: {family.Id} {tierName} value/name/weight/model/sound differs from policy/source.");
                Program.Require(physicalForms.Add(key),
                    $"{key}: physical denomination FormKey is duplicated across families.");
                tierReceipts.Add(new
                {
                    tier = tierName,
                    formKey = key.ToString(),
                    value = tier.Value,
                    name = tier.Name,
                    model = tier.Model,
                    owned,
                    sourcePlugin = source.FormKey.ModKey.FileName.String,
                    sourceForm = source.FormKey.ToString(),
                });
            }

            var aliasReceipts = new List<object>();
            foreach (var alias in family.SourceAliases)
            {
                var source = ResolvePinnedSource(loadOrder, alias, $"{family.Id} source alias");
                var key = source.FormKey;
                var tier = family.Tiers[alias.NormalizesToTier];
                var item = plugin.MiscItems.Single(record => record.FormKey == key);
                var expectedKeywords = (source.Keywords?.Select(keyword => keyword.FormKey) ?? [])
                    .Append(VendorNoSale).ToHashSet();
                Program.Require(item.EditorID == alias.EditorId && item.Value == tier.Value &&
                        item.Name?.String == tier.Name &&
                        Math.Abs(item.Weight - family.RuntimeWeight) < 0.0001f &&
                        string.Equals(item.Model?.File.ToString(), tier.Model,
                            StringComparison.OrdinalIgnoreCase) &&
                        item.PickUpSound.FormKey == source.PickUpSound.FormKey &&
                        item.PutDownSound.FormKey == source.PutDownSound.FormKey &&
                        HasKeyword(item, VendorNoSale) &&
                        (item.Keywords?.Select(keyword => keyword.FormKey) ?? [])
                            .ToHashSet().SetEquals(expectedKeywords),
                    $"{key}: {family.Id} source alias does not normalize exactly to {alias.NormalizesToTier}.");
                Program.Require(physicalForms.Add(key),
                    $"{key}: source alias FormKey is duplicated across families.");
                aliasReceipts.Add(new
                {
                    formKey = key.ToString(),
                    normalizesToTier = alias.NormalizesToTier,
                    canonicalFormKey = tier.FormKey ?? $"{tier.FormId}:{plugin.ModKey.FileName.String}",
                });
            }

            if (family.OwnedRouteKeywordFormId is not null)
            {
                var routeKey = new FormKey(plugin.ModKey, ParseId(family.OwnedRouteKeywordFormId));
                var route = plugin.Keywords.Single(record => record.FormKey == routeKey);
                Program.Require(route.EditorID == family.OwnedRouteKeywordEditorId,
                    $"{family.Id}: owned route keyword differs from policy.");
            }
            familyReceipts.Add(new
            {
                id = family.Id,
                family.Enabled,
                family.DisplayLabel,
                family.BackendLabel,
                perk = family.Perk,
                sourcePlugin = family.PrimarySource.SourcePlugin,
                sourceForm = family.PrimarySource.FormKey,
                sourceEditorId = family.PrimarySource.EditorId,
                sourceValue = family.PrimarySource.SourceValue,
                sourceWeight = family.PrimarySource.SourceWeight,
                runtimeWeight = family.RuntimeWeight,
                sourceModel = family.PrimarySource.SourceModel,
                tiers = tierReceipts,
                sourceAliases = aliasReceipts,
            });
        }
        Program.Require(physicalForms.Count == 55,
            $"Expected exactly 55 canonical/alias physical currency forms, found {physicalForms.Count}.");
        return new
        {
            canonicalPercent = policy.CanonicalPercent,
            variantPercent = policy.VariantPercent,
            tieredFamilies = familyReceipts,
            outputValues = new[] { 1, 10, 100 },
            vendorNoSale = VendorNoSale.ToString(),
            physicalFormsAudited = physicalForms.Count,
        };
    }

    private static bool HasKeyword(IMiscItemGetter item, FormKey keyword) =>
        item.Keywords?.Any(candidate => candidate.FormKey == keyword) == true;

    private static IReadOnlyList<object> AuditPurses(
        ISkyrimModGetter plugin,
        IReadOnlyList<Program.PurseTarget> targets,
        Program.TieredFamilyPolicy septim)
    {
        AuditDecompositionVectors();
        var forms = new Dictionary<FormKey, int>
        {
            [FormKey.Factory(septim.Tiers["copper"].FormKey!)] = 1,
            [FormKey.Factory(septim.Tiers["silver"].FormKey!)] = 10,
            [FormKey.Factory(septim.Tiers["gold"].FormKey!)] = 100,
        };
        var receipts = new List<object>();
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var purse = plugin.LeveledItems.Single(record => record.FormKey == key);
            Program.Require(purse.EditorID == target.EditorId && purse.Flags == 0 &&
                    (double)purse.ChanceNone == 0.0 && purse.Global.IsNull,
                $"{key}: purse selector header differs from policy.");
            var entries = purse.Entries ?? throw new InvalidOperationException($"{key}: purse entries are null.");
            Program.Require(entries.Count == 16 && entries.All(entry => entry.Data is { Level: 1, Count: 1 }),
                $"{key}: purse must have sixteen equal, one-count selector entries.");

            var amountReceipts = new List<object>();
            for (var index = 0; index < target.Counts.Count; index++)
            {
                var amount = target.Counts[index];
                var canonicalKey = new FormKey(plugin.ModKey, ParseId(target.CanonicalFormIdBase) + checked((uint)index));
                var breakKey = new FormKey(plugin.ModKey, ParseId(target.BreakFormIdBase) + checked((uint)index));
                var selectorKey = new FormKey(plugin.ModKey, ParseId(target.SelectorFormIdBase) + checked((uint)index));
                Program.Require(entries[index].Data!.Reference.FormKey == selectorKey,
                    $"{key}: purse selector {index} FormKey differs from policy.");
                var selector = plugin.LeveledItems.Single(record => record.FormKey == selectorKey);
                var choices = selector.Entries
                    ?? throw new InvalidOperationException($"{selectorKey}: selector entries are null.");
                Program.Require(selector.Flags == 0 && (double)selector.ChanceNone == 0.0 && selector.Global.IsNull &&
                        choices.Count == 5 && choices.All(entry => entry.Data is { Level: 1, Count: 1 }) &&
                        choices.Take(4).All(entry => entry.Data!.Reference.FormKey == canonicalKey) &&
                        choices[4].Data!.Reference.FormKey == breakKey,
                    $"{selectorKey}: selector must be exactly four canonical choices and one single-break choice.");

                var canonicalExpected = Program.DecomposeSeptims(amount, false);
                var breakExpected = Program.DecomposeSeptims(amount, true);
                var canonicalActual = AuditPurseOutcome(plugin, canonicalKey, forms);
                var breakActual = AuditPurseOutcome(plugin, breakKey, forms);
                Program.Require(canonicalActual == canonicalExpected && breakActual == breakExpected,
                    $"{selectorKey}: purse decomposition differs from the exact quotient/remainder policy.");
                amountReceipts.Add(new
                {
                    amount,
                    selector = selectorKey.ToString(),
                    canonical = new { formKey = canonicalKey.ToString(), canonicalActual.Copper, canonicalActual.Silver, canonicalActual.Gold },
                    singleBreak = new { formKey = breakKey.ToString(), breakActual.Copper, breakActual.Silver, breakActual.Gold, breakActual.BrokenTier },
                    canonicalChoices = 4,
                    singleBreakChoices = 1,
                    valueConserved = true,
                });
            }
            receipts.Add(new
            {
                formKey = key.ToString(),
                floraFormKey = target.FloraFormKey,
                target.EditorId,
                amounts = amountReceipts,
                outcomes = 16,
                canonicalPercent = 80,
                singleBreakPercent = 20,
                hiddenGold001Entries = 0,
            });
        }
        return receipts;
    }

    private static Program.DenominationCounts AuditPurseOutcome(
        ISkyrimModGetter plugin,
        FormKey key,
        IReadOnlyDictionary<FormKey, int> values)
    {
        var list = plugin.LeveledItems.Single(record => record.FormKey == key);
        Program.Require(list.Flags == LeveledItem.Flag.UseAll &&
                (double)list.ChanceNone == 0.0 && list.Global.IsNull,
            $"{key}: denomination outcome must be an unconditional UseAll list.");
        var entries = list.Entries ?? throw new InvalidOperationException($"{key}: outcome entries are null.");
        Program.Require(entries.Count is >= 1 and <= 3 &&
                entries.All(entry => entry.Data is { Level: 1, Count: > 0 }) &&
                entries.All(entry => values.ContainsKey(entry.Data!.Reference.FormKey)) &&
                entries.Select(entry => entry.Data!.Reference.FormKey).Distinct().Count() == entries.Count,
            $"{key}: outcome entries must be unique positive physical Septim tiers.");
        short count(FormKey form) => entries.SingleOrDefault(entry => entry.Data!.Reference.FormKey == form)?.Data?.Count ?? 0;
        var copper = count(values.Single(pair => pair.Value == 1).Key);
        var silver = count(values.Single(pair => pair.Value == 10).Key);
        var gold = count(values.Single(pair => pair.Value == 100).Key);
        var canonical = new Program.DenominationCounts(copper, silver, gold, null);
        var canonicalForValue = Program.DecomposeSeptims(Program.ValueOf(canonical), false);
        string? brokenTier = null;
        if (gold < canonicalForValue.Gold) brokenTier = "gold";
        else if (silver < canonicalForValue.Silver) brokenTier = "silver";
        return new Program.DenominationCounts(copper, silver, gold, brokenTier);
    }

    private static void AuditDecompositionVectors()
    {
        var vectors = new[]
        {
            (amount: 24, canonical: new Program.DenominationCounts(4, 2, 0, null), broken: new Program.DenominationCounts(14, 1, 0, "silver")),
            (amount: 100, canonical: new Program.DenominationCounts(0, 0, 1, null), broken: new Program.DenominationCounts(0, 10, 0, "gold")),
            (amount: 110, canonical: new Program.DenominationCounts(0, 1, 1, null), broken: new Program.DenominationCounts(0, 11, 0, "gold")),
        };
        foreach (var vector in vectors)
        {
            Program.Require(Program.DecomposeSeptims(vector.amount, false) == vector.canonical &&
                    Program.DecomposeSeptims(vector.amount, true) == vector.broken &&
                    Program.ValueOf(vector.canonical) == vector.amount &&
                    Program.ValueOf(vector.broken) == vector.amount,
                $"Pinned decomposition vector {vector.amount} changed.");
        }
        for (var amount = 0; amount <= short.MaxValue; amount++)
        {
            var canonical = Program.DecomposeSeptims(amount, false);
            var broken = Program.DecomposeSeptims(amount, true);
            Program.Require(Program.ValueOf(canonical) == amount && Program.ValueOf(broken) == amount &&
                    canonical.Copper >= 0 && canonical.Silver >= 0 && canonical.Gold >= 0 &&
                    broken.Copper >= 0 && broken.Silver >= 0 && broken.Gold >= 0,
                $"Exhaustive denomination invariant failed at {amount}.");
        }
    }

    private static IReadOnlyList<object> AuditNeutralizedQuests(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        IReadOnlyList<Program.QuestNeutralizationTarget> targets)
    {
        var receipts = new List<object>();
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var sourceKey = ModKey.FromNameAndExtension(target.SourcePlugin);
            var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == sourceKey).Mod
                ?? throw new InvalidOperationException($"{sourceKey}: source plugin is not loaded.");
            var source = sourceMod.Quests.Single(record => record.FormKey == key);
            var actual = plugin.Quests.Single(record => record.FormKey == key);
            Program.Require(source.EditorID == target.EditorId && actual.EditorID == source.EditorID &&
                    source.Flags.HasFlag(Quest.Flag.StartGameEnabled) &&
                    actual.Flags == (source.Flags & ~Quest.Flag.StartGameEnabled) &&
                    actual.NextAliasID == source.NextAliasID && actual.Aliases.Count == source.Aliases.Count,
                $"{key}: only StartGameEnabled may change outside the transaction alias VMAD.");
            var sourceVmad = source.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: source VMAD is missing.");
            var actualVmad = actual.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: patched VMAD is missing.");
            Program.Require(actualVmad.Scripts.Select(script => script.Name)
                    .SequenceEqual(sourceVmad.Scripts.Select(script => script.Name)) &&
                    actualVmad.Aliases.Count == sourceVmad.Aliases.Count,
                $"{key}: top-level/non-target VMAD structure changed.");
            var sourceAlias = sourceVmad.Aliases.Single(alias => alias.Property.Alias == target.AliasId);
            var actualAlias = actualVmad.Aliases.Single(alias => alias.Property.Alias == target.AliasId);
            Program.Require(sourceAlias.Scripts.Select(script => script.Name).SequenceEqual(target.TransactionScripts) &&
                    actualAlias.Property.Object.FormKey == sourceAlias.Property.Object.FormKey &&
                    actualAlias.Property.Alias == sourceAlias.Property.Alias && actualAlias.Scripts.Count == 0,
                $"{key}: exact ECE transaction scripts were not exclusively removed.");
            receipts.Add(new
            {
                formKey = key.ToString(),
                target.EditorId,
                sourcePlugin = target.SourcePlugin,
                aliasId = target.AliasId,
                removedScripts = target.TransactionScripts,
                removedStartGameEnabled = true,
                otherQuestDataPreserved = true,
                migrationOwner = "EnsrickCurrencyDenominations",
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

    private static IReadOnlyList<object> AuditMintCostOnlyQuests(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        IReadOnlyList<Program.MintCostOnlyQuestPolicy> targets)
    {
        var receipts = new List<object>();
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var originalKey = ModKey.FromNameAndExtension(target.OriginalPlugin);
            var winningKey = ModKey.FromNameAndExtension(target.WinningPlugin);
            var originalMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == originalKey).Mod
                ?? throw new InvalidOperationException($"{originalKey}: original M.I.N.T. module is not loaded.");
            var winningMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == winningKey).Mod
                ?? throw new InvalidOperationException($"{winningKey}: ECE M.I.N.T. patch is not loaded.");
            var original = originalMod.Quests.Single(record => record.FormKey == key);
            var winning = winningMod.Quests.Single(record => record.FormKey == key);
            var actual = plugin.Quests.Single(record => record.FormKey == key);
            Program.Require(original.EditorID == target.EditorId && winning.EditorID == target.EditorId &&
                    actual.EditorID == target.EditorId && actual.Flags == winning.Flags &&
                    actual.NextAliasID == winning.NextAliasID && actual.Aliases.Count == winning.Aliases.Count,
                $"{key}: non-VMAD M.I.N.T. quest data differs from the winning ECE record.");

            var originalVmad = original.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: original M.I.N.T. VMAD is missing.");
            var winningVmad = winning.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: winning ECE M.I.N.T. VMAD is missing.");
            var actualVmad = actual.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: generated M.I.N.T. VMAD is missing.");
            Program.Require(!winningVmad.Scripts.Any(script => script.Name == target.QuestScript),
                $"{key}: winning ECE record unexpectedly retains {target.QuestScript}.");
            var originalScript = originalVmad.Scripts.Single(script => script.Name == target.QuestScript);
            var actualScript = actualVmad.Scripts.Single(script => script.Name == target.QuestScript);
            Program.Require(originalScript.Properties.Select(property => property.Name)
                    .ToHashSet(StringComparer.Ordinal).SetEquals(target.CostPropertyNames) &&
                    actualScript.Properties.Count == originalScript.Properties.Count,
                $"{key}: restored cost-only script property schema differs from pinned original.");
            for (var index = 0; index < originalScript.Properties.Count; index++)
            {
                AuditEquivalentProperty(key, target.QuestScript,
                    originalScript.Properties[index], actualScript.Properties[index]);
            }
            if (target.QuestScript == "DES_DramCurrencySwapper")
            {
                Program.Require(originalScript.Properties.All(property =>
                        property is IScriptObjectPropertyGetter),
                    $"{key}: Dram cost VMAD is no longer the exact twelve scalar-object bindings.");
            }
            else
            {
                Program.Require(originalScript.Properties.Single(property =>
                            property.Name == "CostsToUpdate") is IScriptObjectListPropertyGetter &&
                        originalScript.Properties.Single(property =>
                            property.Name == "defaultCosts") is IScriptIntListPropertyGetter &&
                        originalScript.Properties.Where(property =>
                            property.Name is not ("CostsToUpdate" or "defaultCosts"))
                            .All(property => property is IScriptObjectPropertyGetter),
                    $"{key}: Ulfric cost VMAD must remain one ordered object list, one ordered int list, and seventeen scalar objects.");
            }

            var originalAlias = originalVmad.Aliases.Single(alias => alias.Property.Alias == target.PlayerAliasId);
            var actualAlias = actualVmad.Aliases.Single(alias => alias.Property.Alias == target.PlayerAliasId);
            var proxy = originalAlias.Scripts.Single(script => script.Name == target.PlayerAliasScript);
            var actualProxy = actualAlias.Scripts.Single(script => script.Name == target.PlayerAliasScript);
            Program.Require(proxy.Properties.Count == 0 && actualProxy.Properties.Count == 0 &&
                    target.RemovedAliasScripts.All(name =>
                        !actualAlias.Scripts.Any(script => script.Name == name)),
                $"{key}: transaction alias scripts were restored or the empty proxy schema changed.");
            receipts.Add(new
            {
                formKey = key.ToString(),
                target.EditorId,
                target.QuestScript,
                target.PlayerAliasId,
                target.PlayerAliasScript,
                propertyCount = actualScript.Properties.Count,
                propertyTypes = actualScript.Properties.Select(property => property.GetType().Name).ToArray(),
                absentTransactionAliasScripts = target.RemovedAliasScripts,
                pexContract = "same-name cost/stage-only replacement; no CurrencySwapper calls",
            });
        }
        return receipts;
    }

    private static object AuditMadranRemoval(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        Program.ScriptRemovalTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == Program.EceMintUlfric).Mod
            ?? throw new InvalidOperationException("ECE M.I.N.T. Ulfric patch is not loaded.");
        var source = sourceMod.Quests.Single(record => record.FormKey == key);
        var actual = plugin.Quests.Single(record => record.FormKey == key);
        var sourceVmad = source.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: source Ma'dran VMAD is missing.");
        var actualVmad = actual.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: generated Ma'dran VMAD is missing.");
        var sourceAlias = sourceVmad.Aliases.Single(alias => alias.Property.Alias == target.AliasId);
        var actualAlias = actualVmad.Aliases.Single(alias => alias.Property.Alias == target.AliasId);
        Program.Require(sourceAlias.Scripts.Count(script => script.Name == target.TransactionScript) == 1 &&
                !actualAlias.Scripts.Any(script => script.Name == target.TransactionScript) &&
                !actualAlias.Scripts.Any(script => script.Name == "DES_CurrencyFramework_BarterExclusion"),
            $"{key}: Ma'dran transaction/barter swapper remains attached.");
        var sourceFragment = sourceVmad.Scripts.Single(script =>
            script.Name == "QF_DES_UlfricWindhelmService_03000002");
        var actualFragment = actualVmad.Scripts.Single(script =>
            script.Name == "QF_DES_UlfricWindhelmService_03000002");
        foreach (var propertyName in target.StaleQuestProperties)
        {
            Program.Require(sourceFragment.Properties.Count(property => property.Name == propertyName) == 1 &&
                    !actualFragment.Properties.Any(property => property.Name == propertyName),
                $"{key}: stale Ma'dran quest-fragment property {propertyName} was not exclusively removed.");
        }
        return new
        {
            formKey = key.ToString(),
            target.AliasId,
            removedScript = target.TransactionScript,
            replacementScript = (string?)null,
            removedStaleQuestProperties = target.StaleQuestProperties,
        };
    }

    private static IReadOnlyList<object> AuditDisabledMintExchangeInfos(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        IReadOnlyList<Program.MintExchangeInfoPolicy> targets)
    {
        var receipts = new List<object>();
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == key.ModKey).Mod
                ?? throw new InvalidOperationException($"{key.ModKey}: M.I.N.T. source module is not loaded.");
            var sourceParent = sourceMod.DialogTopics.Single(topic =>
                topic.Responses.Any(response => response.FormKey == key));
            var source = sourceParent.Responses.Single(response => response.FormKey == key);
            var actual = FindInfo(plugin, key);
            Program.Require(sourceParent.FormKey == FormKey.Factory(target.ParentTopicFormKey) &&
                    sourceParent.EditorID == target.ParentTopicEditorId && string.IsNullOrEmpty(source.EditorID) &&
                    source.Conditions.Count == target.ConditionCount,
                $"{key}: pinned obsolete exchange INFO identity changed.");
            var sourceScripts = source.VirtualMachineAdapter?.Scripts.Select(script => script.Name).ToArray() ?? [];
            var actualScripts = actual.VirtualMachineAdapter?.Scripts.Select(script => script.Name).ToArray() ?? [];
            Program.Require(sourceScripts.SequenceEqual(target.TransactionScripts) && actualScripts.Length == 0,
                $"{key}: exact obsolete transaction TIF was not exclusively removed.");
            Program.Require(actual.Conditions.Count == source.Conditions.Count + 1,
                $"{key}: fail-closed gate was not added exactly once.");
            var gate = actual.Conditions[0];
            Program.Require(gate is IConditionFloatGetter gateFloat &&
                    gateFloat.CompareOperator == CompareOperator.EqualTo && gateFloat.ComparisonValue == 1.0f &&
                    gateFloat.Flags == 0 && gateFloat.Data is IGetGlobalValueConditionDataGetter gateData &&
                    gateData.Global.Link.FormKey == MintConvert,
                $"{key}: fail-closed DES_ConvertCoins == 1 gate differs from policy.");
            for (var index = 0; index < source.Conditions.Count; index++)
            {
                Program.Require(actual.Conditions[index + 1].GetType() == source.Conditions[index].GetType() &&
                        actual.Conditions[index + 1].CompareOperator == source.Conditions[index].CompareOperator &&
                        actual.Conditions[index + 1].Flags == source.Conditions[index].Flags &&
                        actual.Conditions[index + 1].Data.GetType() == source.Conditions[index].Data.GetType(),
                    $"{key}: original condition {index} type/operator/flags changed.");
            }
            receipts.Add(new
            {
                formKey = key.ToString(),
                parentTopic = sourceParent.FormKey.ToString(),
                parentEditorId = sourceParent.EditorID,
                strippedScripts = target.TransactionScripts,
                originalConditionCount = source.Conditions.Count,
                gate = "DES_ConvertCoins == 1",
                enforcedGlobalValue = 0,
            });
        }
        return receipts;
    }

    private static IReadOnlyList<object> AuditMintBackendConditions(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        IReadOnlyList<Program.MintBackendConditionPolicy> targets)
    {
        var receipts = new List<object>();
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var sourceMod = loadOrder.ListedOrder.Single(listing => listing.ModKey == key.ModKey).Mod
                ?? throw new InvalidOperationException($"{key.ModKey}: M.I.N.T. source module is not loaded.");
            var sourceParent = sourceMod.DialogTopics.Single(topic =>
                topic.Responses.Any(response => response.FormKey == key));
            var source = sourceParent.Responses.Single(response => response.FormKey == key);
            var actual = FindInfo(plugin, key);
            var sourceVmad = source.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: source horse-purchase VMAD is missing.");
            var actualVmad = actual.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: patched horse-purchase VMAD is missing.");
            var sourceScript = sourceVmad.Scripts.Single(script => script.Name == target.Script);
            var actualScript = actualVmad.Scripts.Single(script => script.Name == target.Script);
            Program.Require(sourceParent.FormKey == FormKey.Factory(target.ParentTopicFormKey) &&
                    sourceParent.EditorID == target.ParentTopicEditorId && source.Conditions.Count == target.ConditionCount &&
                    actual.Conditions.Count == source.Conditions.Count &&
                    sourceVmad.Scripts.Select(script => script.Name).SequenceEqual(new[] { target.Script }) &&
                    actualVmad.Scripts.Select(script => script.Name)
                        .SequenceEqual(sourceVmad.Scripts.Select(script => script.Name)) &&
                    Convert.ToInt32(sourceVmad.Version) == target.VmadVersion &&
                    Convert.ToInt32(sourceVmad.ObjectFormat) == target.VmadObjectFormat &&
                    actualVmad.Version == sourceVmad.Version && actualVmad.ObjectFormat == sourceVmad.ObjectFormat &&
                    sourceScript.Properties.Count == target.VmadProperties.Count &&
                    actualScript.Properties.Count == sourceScript.Properties.Count,
                $"{key}: backend-aware M.I.N.T. service INFO identity changed.");
            var sourceCondition = (IConditionGlobalGetter)source.Conditions[target.ConditionIndex];
            var actualCondition = (IConditionGlobalGetter)actual.Conditions[target.ConditionIndex];
            var sourceCount = (IGetItemCountConditionDataGetter)sourceCondition.Data;
            var actualCount = (IGetItemCountConditionDataGetter)actualCondition.Data;
            Program.Require(sourceCount.ItemOrList.Link.FormKey == FormKey.Factory(target.SourceCurrency) &&
                    actualCount.ItemOrList.Link.FormKey == FormKey.Factory(target.BackendCurrency) &&
                    sourceCondition.ComparisonValue.FormKey == FormKey.Factory(target.ComparisonGlobal) &&
                    actualCondition.ComparisonValue.FormKey == sourceCondition.ComparisonValue.FormKey &&
                    actualCondition.CompareOperator == sourceCondition.CompareOperator &&
                    actualCondition.Flags == sourceCondition.Flags && actualCount.RunOnType == sourceCount.RunOnType &&
                     actualCount.Reference.FormKey == sourceCount.Reference.FormKey,
                $"{key}: horse-purchase condition changed beyond physical-copper to Gold001 retargeting.");
            foreach (var propertyTarget in target.VmadProperties)
            {
                var sourceProperty = sourceScript.Properties.OfType<IScriptObjectPropertyGetter>()
                    .Single(property => property.Name == propertyTarget.Name);
                var actualProperty = actualScript.Properties.OfType<IScriptObjectPropertyGetter>()
                    .Single(property => property.Name == propertyTarget.Name);
                Program.Require(sourceProperty.Object.FormKey == FormKey.Factory(propertyTarget.FormKey) &&
                        Program.RawVmadAlias(sourceProperty.Alias) == propertyTarget.Alias &&
                        actualProperty.Alias == sourceProperty.Alias &&
                        actualProperty.Object.FormKey ==
                            (propertyTarget.Name == target.VmadCurrencyProperty
                                ? FormKey.Factory(target.BackendCurrency)
                                : sourceProperty.Object.FormKey),
                    $"{key}: {target.Script}.{propertyTarget.Name} changed beyond the exact Gold001 debit retarget.");
            }
            receipts.Add(new
            {
                formKey = key.ToString(),
                parentTopic = sourceParent.FormKey.ToString(),
                target.Script,
                sourceCurrency = target.SourceCurrency,
                backendCurrency = target.BackendCurrency,
                comparisonGlobal = target.ComparisonGlobal,
                debitProperty = target.VmadCurrencyProperty,
                vmadVersion = target.VmadVersion,
                vmadObjectFormat = target.VmadObjectFormat,
                preservedOtherProperties = target.VmadProperties.Count - 1,
                fragmentsPreservedByExactOverride = true,
            });
        }
        return receipts;
    }

    private static IReadOnlyList<object> AuditDialogParentScopes(
        ISkyrimModGetter plugin,
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder,
        IReadOnlyList<Program.MintExchangeInfoPolicy> disabled,
        IReadOnlyList<Program.MintBackendConditionPolicy> backend)
    {
        var expected = disabled
            .Select(target => (parent: FormKey.Factory(target.ParentTopicFormKey),
                editorId: target.ParentTopicEditorId, child: FormKey.Factory(target.FormKey)))
            .Concat(backend.Select(target => (parent: FormKey.Factory(target.ParentTopicFormKey),
                editorId: target.ParentTopicEditorId, child: FormKey.Factory(target.FormKey))))
            .GroupBy(target => (target.parent, target.editorId))
            .ToArray();
        Program.Require(expected.Length == 20 && plugin.DialogTopics.Count == expected.Length &&
                plugin.DialogTopics.Select(parent => parent.FormKey).ToHashSet()
                    .SetEquals(expected.Select(group => group.Key.parent)),
            "Serialized parent DIAL set differs from the exact forty-INFO policy.");

        var receipts = new List<object>();
        foreach (var group in expected)
        {
            var sourceMod = loadOrder.ListedOrder.Single(listing =>
                    listing.ModKey == group.Key.parent.ModKey).Mod
                ?? throw new InvalidOperationException($"{group.Key.parent.ModKey}: DIAL source is not loaded.");
            var source = sourceMod.DialogTopics.Single(parent => parent.FormKey == group.Key.parent);
            var actual = plugin.DialogTopics.Single(parent => parent.FormKey == group.Key.parent);
            Program.Require(source.EditorID == group.Key.editorId && actual.EditorID == source.EditorID &&
                    actual.FormVersion == source.FormVersion &&
                    actual.MajorRecordFlagsRaw == source.MajorRecordFlagsRaw &&
                    actual.Version2 == source.Version2 && actual.VersionControl == source.VersionControl &&
                    actual.Name?.String == source.Name?.String && actual.Priority == source.Priority &&
                    actual.Quest.FormKey == source.Quest.FormKey && actual.Branch.FormKey == source.Branch.FormKey &&
                    actual.Category == source.Category && actual.Subtype == source.Subtype &&
                    actual.SubtypeName == source.SubtypeName && actual.Timestamp == source.Timestamp &&
                    actual.TopicFlags == source.TopicFlags && actual.Unknown == source.Unknown,
                $"{group.Key.parent}: serialized DIAL metadata differs from source.");
            var expectedChildren = group.Select(target => target.child).ToHashSet();
            var actualChildren = actual.Responses.Select(response => response.FormKey).ToHashSet();
            Program.Require(actual.Responses.Count == expectedChildren.Count &&
                    actualChildren.SetEquals(expectedChildren),
                $"{group.Key.parent}: serialized DIAL contains a missing, duplicate, or sibling INFO override.");
            receipts.Add(new
            {
                formKey = group.Key.parent.ToString(),
                editorId = group.Key.editorId,
                metadataIdentical = true,
                responseFormKeys = actual.Responses.Select(response => response.FormKey.ToString()).ToArray(),
            });
        }
        return receipts;
    }

    private static IDialogResponsesGetter FindInfo(ISkyrimModGetter plugin, FormKey key) =>
        plugin.DialogTopics.SelectMany(topic => topic.Responses).Single(response => response.FormKey == key);

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
        Program.Require(actual.Name == expected.Name && actual.Flags == expected.Flags &&
                actual.GetType() == expected.GetType(),
            $"{record}: {scriptName}.{expected.Name} identity/flags/type changed.");
        if (expected is IScriptObjectPropertyGetter expectedObject &&
            actual is IScriptObjectPropertyGetter actualObject)
        {
            Program.Require(actualObject.Object.FormKey == expectedObject.Object.FormKey &&
                    actualObject.Alias == expectedObject.Alias && actualObject.Unused == expectedObject.Unused,
                $"{record}: {scriptName}.{expected.Name} object binding changed.");
            return;
        }
        if (expected is IScriptObjectListPropertyGetter expectedObjects &&
            actual is IScriptObjectListPropertyGetter actualObjects)
        {
            Program.Require(actualObjects.Objects.Count == expectedObjects.Objects.Count &&
                    actualObjects.Objects.Zip(expectedObjects.Objects).All(pair =>
                        pair.First.Object.FormKey == pair.Second.Object.FormKey &&
                        pair.First.Alias == pair.Second.Alias && pair.First.Unused == pair.Second.Unused),
                $"{record}: {scriptName}.{expected.Name} ordered object FormKey/alias list changed.");
            return;
        }
        if (expected is IScriptBoolPropertyGetter expectedBool &&
            actual is IScriptBoolPropertyGetter actualBool)
        {
            Program.Require(actualBool.Data == expectedBool.Data,
                $"{record}: {scriptName}.{expected.Name} bool value changed.");
            return;
        }
        if (expected is IScriptIntPropertyGetter expectedInt &&
            actual is IScriptIntPropertyGetter actualInt)
        {
            Program.Require(actualInt.Data == expectedInt.Data,
                $"{record}: {scriptName}.{expected.Name} int value changed.");
            return;
        }
        if (expected is IScriptFloatPropertyGetter expectedFloat &&
            actual is IScriptFloatPropertyGetter actualFloat)
        {
            Program.Require(BitConverter.SingleToInt32Bits(actualFloat.Data) ==
                    BitConverter.SingleToInt32Bits(expectedFloat.Data),
                $"{record}: {scriptName}.{expected.Name} float bits changed.");
            return;
        }
        if (expected is IScriptStringPropertyGetter expectedString &&
            actual is IScriptStringPropertyGetter actualString)
        {
            Program.Require(string.Equals(actualString.Data, expectedString.Data, StringComparison.Ordinal),
                $"{record}: {scriptName}.{expected.Name} string value changed.");
            return;
        }
        if (expected is IScriptBoolListPropertyGetter expectedBools &&
            actual is IScriptBoolListPropertyGetter actualBools)
        {
            Program.Require(actualBools.Data.SequenceEqual(expectedBools.Data),
                $"{record}: {scriptName}.{expected.Name} ordered bool list changed.");
            return;
        }
        if (expected is IScriptIntListPropertyGetter expectedInts &&
            actual is IScriptIntListPropertyGetter actualInts)
        {
            Program.Require(actualInts.Data.SequenceEqual(expectedInts.Data),
                $"{record}: {scriptName}.{expected.Name} ordered int list changed.");
            return;
        }
        if (expected is IScriptFloatListPropertyGetter expectedFloats &&
            actual is IScriptFloatListPropertyGetter actualFloats)
        {
            Program.Require(actualFloats.Data.Select(BitConverter.SingleToInt32Bits)
                    .SequenceEqual(expectedFloats.Data.Select(BitConverter.SingleToInt32Bits)),
                $"{record}: {scriptName}.{expected.Name} ordered float-bit list changed.");
            return;
        }
        if (expected is IScriptStringListPropertyGetter expectedStrings &&
            actual is IScriptStringListPropertyGetter actualStrings)
        {
            Program.Require(actualStrings.Data.SequenceEqual(expectedStrings.Data, StringComparer.Ordinal),
                $"{record}: {scriptName}.{expected.Name} ordered string list changed.");
            return;
        }
        throw new InvalidOperationException(
            $"{record}: unexpected VMAD property type {expected.GetType().Name} on {scriptName}.{expected.Name}.");
    }

    private static object AuditRegionalPurseGraph(
        ISkyrimModGetter plugin,
        Program.RegionalPurseGraphPolicy policy,
        Program.DenominationPolicy denominations)
    {
        var start = ParseId(policy.OwnedFormIdBase);
        Program.Require(start == 0x990, "Regional purse graph must start at owned FormID 000990.");
        var expectedOwned = Enumerable.Range(0x990, 0x70)
            .Concat(Enumerable.Range(0xA16, 0x52A))
            .Select(id => new FormKey(plugin.ModKey, checked((uint)id))).ToHashSet();
        var actualOwned = plugin.LeveledItems.Where(record => expectedOwned.Contains(record.FormKey)).ToArray();
        Program.Require(actualOwned.Length == expectedOwned.Count &&
                actualOwned.Select(record => record.FormKey).ToHashSet().SetEquals(expectedOwned),
            "Regional purse graph must contain exact ranges 000990-0009FF and 000A16-000F3F without colliding with A00-A15 denomination forms.");

        var denominationForms = denominations.TieredFamilies.ToDictionary(
            family => family.Id,
            family => family.Tiers.Values.Select(tier => tier.FormKey is not null
                    ? FormKey.Factory(tier.FormKey)
                    : new FormKey(plugin.ModKey, ParseId(tier.FormId!)))
                .ToHashSet(),
            StringComparer.Ordinal);
        var roots = new HashSet<FormKey>();
        var purseReceipts = new List<object>();
        foreach (var family in policy.Families)
        {
            var allowedLeaves = denominationForms[family.FamilyId];
            foreach (var purse in family.Purses)
            {
                var key = FormKey.Factory(purse.FormKey);
                var actual = plugin.LeveledItems.Single(record => record.FormKey == key);
                var entries = actual.Entries
                    ?? throw new InvalidOperationException($"{key}: rebuilt regional purse entries are null.");
                var root = entries.Count == 1 ? entries[0].Data : null;
                Program.Require(actual.EditorID == purse.EditorId && actual.Flags == LeveledItem.Flag.UseAll &&
                        (double)actual.ChanceNone == 0.0 && actual.Global.IsNull &&
                        root is { Level: 1, Count: 1 } && expectedOwned.Contains(root.Reference.FormKey),
                    $"{key}: regional purse does not point to one owned probability-DAG root.");
                roots.Add(root!.Reference.FormKey);
                purseReceipts.Add(new
                {
                    familyId = family.FamilyId,
                    formKey = key.ToString(),
                    purse.EditorId,
                    root = root.Reference.FormKey.ToString(),
                    purse.BaseCoinCount,
                    purse.PrimaryChangeRolls,
                    purse.SecondaryChangeRolls,
                    allowedLeaves = allowedLeaves.Select(form => form.ToString()).Order().ToArray(),
                });
            }
        }
        Program.Require(roots.Count == 24, "Regional purse graph must expose exactly 24 distinct purse roots.");

        var byKey = actualOwned.ToDictionary(record => record.FormKey);
        var reachable = new HashSet<FormKey>();
        var owners = new Dictionary<FormKey, string>();
        var distributionReceipts = new List<object>();

        static int Gcd(int left, int right)
        {
            left = Math.Abs(left);
            right = Math.Abs(right);
            while (right != 0) (left, right) = (right, left % right);
            return left;
        }

        static IReadOnlyList<(short amount, long weight)> SourceOptions(
            Program.RegionalChangeListPolicy change)
        {
            var raw = new Dictionary<short, int>
            {
                [0] = checked(change.ChanceNonePercent * change.Counts.Count),
            };
            foreach (var amount in change.Counts)
                raw[amount] = raw.GetValueOrDefault(amount) + (100 - change.ChanceNonePercent);
            var divisor = raw.Values.Where(value => value > 0).Aggregate(Gcd);
            return raw.Where(pair => pair.Value > 0).OrderBy(pair => pair.Key)
                .Select(pair => (pair.Key, (long)(pair.Value / divisor))).ToArray();
        }

        static Dictionary<int, long> ApplyRoll(
            IReadOnlyDictionary<int, long> current,
            IReadOnlyList<(short amount, long weight)> options)
        {
            var result = new Dictionary<int, long>();
            foreach (var state in current)
            foreach (var option in options)
            {
                var amount = checked(state.Key + option.amount);
                result[amount] = checked(result.GetValueOrDefault(amount) +
                    checked(state.Value * option.weight));
            }
            return result;
        }

        static Dictionary<int, long> ExpectedTotals(
            Program.RegionalPurseTarget purse,
            Program.RegionalPurseFamilyPolicy family)
        {
            IReadOnlyDictionary<int, long> result = new Dictionary<int, long>
            {
                [purse.BaseCoinCount] = 1,
            };
            var primary = SourceOptions(family.PrimaryChange);
            for (var roll = 0; roll < purse.PrimaryChangeRolls; roll++)
                result = ApplyRoll(result, primary);
            var secondary = SourceOptions(family.SecondaryChange);
            return ApplyRoll(result, secondary);
        }

        static Dictionary<(short copper, short silver, short gold), long> ExpectedVectors(
            IReadOnlyDictionary<int, long> totals)
        {
            var result = new Dictionary<(short copper, short silver, short gold), long>();
            foreach (var total in totals)
            {
                var canonical = Program.DecomposeSeptims(total.Key, false);
                var broken = Program.DecomposeSeptims(total.Key, true);
                var canonicalKey = (canonical.Copper, canonical.Silver, canonical.Gold);
                var brokenKey = (broken.Copper, broken.Silver, broken.Gold);
                if (canonicalKey == brokenKey)
                {
                    result[canonicalKey] = checked(result.GetValueOrDefault(canonicalKey) +
                        checked(total.Value * 5));
                }
                else
                {
                    result[canonicalKey] = checked(result.GetValueOrDefault(canonicalKey) +
                        checked(total.Value * 4));
                    result[brokenKey] = checked(result.GetValueOrDefault(brokenKey) + total.Value);
                }
            }
            return result;
        }

        void Visit(
            FormKey key,
            string familyId,
            HashSet<FormKey> allowedLeaves,
            HashSet<FormKey> familyReachable,
            HashSet<FormKey> visiting)
        {
            if (!expectedOwned.Contains(key))
            {
                Program.Require(allowedLeaves.Contains(key), $"{key}: purse graph reached another family's denomination.");
                return;
            }
            if (familyReachable.Contains(key)) return;
            Program.Require(visiting.Add(key), $"{key}: regional purse graph contains a cycle.");
            Program.Require(!owners.TryGetValue(key, out var owner) || owner == familyId,
                $"{key}: regional purse graph node is shared by {owner} and {familyId}.");
            owners[key] = familyId;
            var record = byKey[key];
            var entries = record.Entries
                ?? throw new InvalidOperationException($"{key}: owned purse graph node has null entries.");
            Program.Require(record.Global.IsNull && (double)record.ChanceNone == 0.0 && entries.Count > 0 &&
                    (record.Flags == 0 || record.Flags == LeveledItem.Flag.UseAll) &&
                    entries.All(entry => entry.Data is { Level: 1, Count: > 0 }),
                $"{key}: owned purse graph node has an invalid header or entry.");
            foreach (var entry in entries)
                Visit(entry.Data!.Reference.FormKey, familyId, allowedLeaves, familyReachable, visiting);
            visiting.Remove(key);
            familyReachable.Add(key);
            reachable.Add(key);
        }
        foreach (var family in policy.Families)
        {
            var leaves = denominationForms[family.FamilyId];
            var tierVectors = new Dictionary<FormKey, (short copper, short silver, short gold)>
            {
                [denominations.TieredFamilies.Single(item => item.Id == family.FamilyId).Tiers["copper"].FormKey is { } copper
                    ? FormKey.Factory(copper)
                    : new FormKey(plugin.ModKey, ParseId(denominations.TieredFamilies.Single(item => item.Id == family.FamilyId).Tiers["copper"].FormId!))] = (1, 0, 0),
                [denominations.TieredFamilies.Single(item => item.Id == family.FamilyId).Tiers["silver"].FormKey is { } silver
                    ? FormKey.Factory(silver)
                    : new FormKey(plugin.ModKey, ParseId(denominations.TieredFamilies.Single(item => item.Id == family.FamilyId).Tiers["silver"].FormId!))] = (0, 1, 0),
                [denominations.TieredFamilies.Single(item => item.Id == family.FamilyId).Tiers["gold"].FormKey is { } gold
                    ? FormKey.Factory(gold)
                    : new FormKey(plugin.ModKey, ParseId(denominations.TieredFamilies.Single(item => item.Id == family.FamilyId).Tiers["gold"].FormId!))] = (0, 0, 1),
            };
            var familyReachable = new HashSet<FormKey>();
            var visiting = new HashSet<FormKey>();
            var probabilityCache = new Dictionary<FormKey,
                Dictionary<(short copper, short silver, short gold), double>>();

            Dictionary<(short copper, short silver, short gold), double> Evaluate(FormKey key)
            {
                if (tierVectors.TryGetValue(key, out var physical))
                    return new Dictionary<(short, short, short), double> { [physical] = 1.0 };
                if (probabilityCache.TryGetValue(key, out var cached)) return cached;
                var record = byKey[key];
                var entries = record.Entries!;
                var result = new Dictionary<(short copper, short silver, short gold), double>();
                if (record.Flags == LeveledItem.Flag.UseAll)
                {
                    short copper = 0, silver = 0, gold = 0;
                    foreach (var entry in entries)
                    {
                        var data = entry.Data!;
                        Program.Require(tierVectors.TryGetValue(data.Reference.FormKey, out var part),
                            $"{key}: deterministic denomination vector contains a nested/non-family target.");
                        copper = checked((short)(copper + checked(part.copper * data.Count)));
                        silver = checked((short)(silver + checked(part.silver * data.Count)));
                        gold = checked((short)(gold + checked(part.gold * data.Count)));
                    }
                    result[(copper, silver, gold)] = 1.0;
                }
                else
                {
                    var choiceProbability = 1.0 / entries.Count;
                    foreach (var entry in entries)
                    {
                        var data = entry.Data!;
                        if (tierVectors.TryGetValue(data.Reference.FormKey, out var part))
                        {
                            var vector = (checked((short)(part.copper * data.Count)),
                                checked((short)(part.silver * data.Count)),
                                checked((short)(part.gold * data.Count)));
                            result[vector] = result.GetValueOrDefault(vector) + choiceProbability;
                            continue;
                        }
                        Program.Require(data.Count == 1,
                            $"{key}: probabilistic nested list count must be one for exact audit evaluation.");
                        foreach (var outcome in Evaluate(data.Reference.FormKey))
                            result[outcome.Key] = result.GetValueOrDefault(outcome.Key) +
                                (choiceProbability * outcome.Value);
                    }
                }
                probabilityCache.Add(key, result);
                return result;
            }

            foreach (var purse in family.Purses)
            {
                var root = plugin.LeveledItems.Single(record => record.FormKey == FormKey.Factory(purse.FormKey))
                    .Entries!.Single().Data!.Reference.FormKey;
                Visit(root, family.FamilyId, leaves, familyReachable, visiting);
                var expectedTotals = ExpectedTotals(purse, family);
                var expectedVectors = ExpectedVectors(expectedTotals);
                var denominator = checked(expectedTotals.Values.Sum() * 5);
                var actualVectors = Evaluate(root);
                Program.Require(actualVectors.Keys.ToHashSet().SetEquals(expectedVectors.Keys) &&
                        expectedVectors.All(pair => Math.Abs(actualVectors[pair.Key] -
                            ((double)pair.Value / denominator)) < 1e-12),
                    $"{purse.FormKey}: serialized purse DAG probability distribution differs from the pinned source/80-20 policy.");
                Program.Require(expectedTotals.Keys.Where(value => value >= 10).All(value =>
                        Program.DecomposeSeptims(value, false).Silver > 0 ||
                        Program.DecomposeSeptims(value, false).Gold > 0) &&
                    expectedTotals.Keys.Where(value => value >= 100).All(value =>
                        Program.DecomposeSeptims(value, false).Gold > 0),
                    $"{purse.FormKey}: canonical denomination threshold coverage failed.");
                distributionReceipts.Add(new
                {
                    familyId = family.FamilyId,
                    formKey = purse.FormKey,
                    purse.EditorId,
                    sourceTotalWeight = expectedTotals.Values.Sum(),
                    sourceTotals = expectedTotals.OrderBy(pair => pair.Key).Select(pair => new
                    {
                        value = pair.Key,
                        weight = pair.Value,
                    }).ToArray(),
                    denominationWeightDenominator = denominator,
                    denominationOutcomes = expectedVectors
                        .OrderBy(pair => Program.ValueOf(new Program.DenominationCounts(
                            pair.Key.copper, pair.Key.silver, pair.Key.gold, null)))
                        .ThenBy(pair => pair.Key.gold).ThenBy(pair => pair.Key.silver)
                        .Select(pair => new
                        {
                            value = Program.ValueOf(new Program.DenominationCounts(
                                pair.Key.copper, pair.Key.silver, pair.Key.gold, null)),
                            pair.Key.copper,
                            pair.Key.silver,
                            pair.Key.gold,
                            weight = pair.Value,
                            probabilityPercent = Math.Round(100.0 * pair.Value / denominator, 12),
                        }).ToArray(),
                });
            }
        }
        Program.Require(reachable.SetEquals(expectedOwned),
            $"Regional purse graph reachability differs: reached {reachable.Count}/{expectedOwned.Count} nodes.");
        Program.Require(owners.Count == expectedOwned.Count,
            "Every owned regional purse graph node must belong to exactly one currency family.");
        return new
        {
            ownedFormIdRanges = new[] { new[] { "000990", "0009FF" }, new[] { "000A16", "000F3F" } },
            ownedNodes = expectedOwned.Count,
            purseOverrides = purseReceipts,
            flattenedDistributions = distributionReceipts,
            exactSourceProbabilityDag = true,
            wholePurseCanonicalPercent = 80,
            wholePurseSingleBreakPercent = 20,
            noCrossFamilyLeaves = true,
            noCrossFamilyNodes = true,
            acyclic = true,
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
