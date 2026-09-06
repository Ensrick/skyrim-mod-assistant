using System.Text.Json;
using System.Text.Json.Serialization;
using System.Security.Cryptography;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Translations;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Synthesis;
using Noggog;

namespace Ensrick.CurrencyIntegrationPatcher;

public static class Program
{
    public const string OutputPlugin = "Ensrick Currency Integration Patch.esp";
    public const string RegionalPursePlugin = "Ensrick Currency Regional Purses.esp";
    public const string RuntimeQuestEditorId = "Ensrick_CurrencyRuntimeDefaultsQuest";
    public const string RuntimeScriptName = "Ensrick_CurrencyRuntimeDefaultsAlias";
    public const uint RuntimeQuestId = 0x800;

    public static readonly ModKey Ece = ModKey.FromNameAndExtension("exchangeCurrency_enhanced.esp");
    public static readonly ModKey Exchange = ModKey.FromNameAndExtension("SL99Exchanger.esp");
    public static readonly ModKey Coin = ModKey.FromNameAndExtension("C.O.I.N.esp");
    public static readonly ModKey Mint = ModKey.FromNameAndExtension("M.I.N.T.esp");
    public static readonly ModKey Dram = ModKey.FromNameAndExtension("MorrowindUsesDrams.esp");
    public static readonly ModKey Windhelm = ModKey.FromNameAndExtension("WindhelmUsesUlfrics.esp");
    public static readonly ModKey CoinPatch = ModKey.FromNameAndExtension("exchangeCurrency_patch_COIN.esp");
    public static readonly ModKey EceMintDram = ModKey.FromNameAndExtension("exchangeCurrency_patch_MINT_dram.esp");
    public static readonly ModKey EceMintUlfric = ModKey.FromNameAndExtension("exchangeCurrency_patch_MINT_ulfric.esp");
    public static readonly ModKey BsAssets = ModKey.FromNameAndExtension("BSAssets.esm");

    public static readonly IReadOnlyList<ModKey> RequiredMasters =
    [
        ModKey.FromNameAndExtension("Skyrim.esm"),
        ModKey.FromNameAndExtension("Update.esm"),
        ModKey.FromNameAndExtension("HearthFires.esm"),
        ModKey.FromNameAndExtension("Dragonborn.esm"),
        BsAssets,
        Exchange,
        Ece,
        Coin,
        Mint,
        Dram,
        Windhelm,
        CoinPatch,
    ];

    private static readonly FormKey PlayerRef = FormKey.Factory("000014:Skyrim.esm");
    private static readonly FormKey CoinManagerQuest = FormKey.Factory("00084B:C.O.I.N.esp");
    private static readonly FormKey MintFrameworkQuest = FormKey.Factory("000800:M.I.N.T.esp");
    private static readonly FormKey MintConvertGlobal = FormKey.Factory("DE5037:Update.esm");
    private static readonly FormKey GiftUniversallyValuable = FormKey.Factory("0A0E55:Skyrim.esm");
    private static readonly FormKey VendorNoSale = FormKey.Factory("0FF9FB:Skyrim.esm");
    private const int CompressedRecordFlag = 0x00040000;

    public sealed class Policy
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonPropertyName("outputPlugin")] public string OutputPluginName { get; set; } = "";
        [JsonPropertyName("runtimeReasonCounters")] public List<string> RuntimeReasonCounters { get; set; } = [];
        [JsonPropertyName("exchangeWorkbenchProvider")] public ExchangeWorkbenchProviderPolicy ExchangeWorkbenchProvider { get; set; } = new();
        [JsonPropertyName("quest")] public QuestPolicy Quest { get; set; } = new();
        [JsonPropertyName("denominations")] public DenominationPolicy Denominations { get; set; } = new();
        [JsonPropertyName("overrides")] public OverridePolicy Overrides { get; set; } = new();
        [JsonPropertyName("disabledCurrencyToIngotRecipes")] public List<Target> DisabledRecipes { get; set; } = [];
        [JsonPropertyName("disabledModernBankRecipes")] public List<Target> DisabledModernBankRecipes { get; set; } = [];
    }

    public sealed class ExchangeWorkbenchProviderPolicy
    {
        [JsonPropertyName("plugin")] public string Plugin { get; set; } = "";
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("sha256")] public string Sha256 { get; set; } = "";
        [JsonPropertyName("bytes")] public long Bytes { get; set; }
        [JsonPropertyName("records")] public int Records { get; set; }
        [JsonPropertyName("requiresSmallFlag")] public bool RequiresSmallFlag { get; set; }
    }

    public sealed class QuestPolicy
    {
        [JsonPropertyName("formId")] public string FormId { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("aliasId")] public uint AliasId { get; set; }
        [JsonPropertyName("aliasName")] public string AliasName { get; set; } = "";
        [JsonPropertyName("script")] public string Script { get; set; } = "";
    }

    public sealed class OverridePolicy
    {
        [JsonPropertyName("dragonbornGoldPiles")] public List<Target> GoldPiles { get; set; } = [];
        [JsonPropertyName("coinPurses")] public List<PurseTarget> CoinPurses { get; set; } = [];
        [JsonPropertyName("gold001")] public KeywordTarget Gold { get; set; } = new();
        [JsonPropertyName("mintAutoConvert")] public GlobalTarget MintAutoConvert { get; set; } = new();
        [JsonPropertyName("ecePlayerCurrencyQuests")] public List<QuestNeutralizationTarget> EcePlayerCurrencyQuests { get; set; } = [];
        [JsonPropertyName("mintCostOnlyQuests")] public List<MintCostOnlyQuestPolicy> MintCostOnlyQuests { get; set; } = [];
        [JsonPropertyName("mintMadranQuest")] public ScriptRemovalTarget MintMadranQuest { get; set; } = new();
        [JsonPropertyName("disabledMintExchangeInfos")] public List<MintExchangeInfoPolicy> DisabledMintExchangeInfos { get; set; } = [];
        [JsonPropertyName("mintBackendConditionInfos")] public List<MintBackendConditionPolicy> MintBackendConditionInfos { get; set; } = [];
        [JsonPropertyName("regionalPurseGraph")] public RegionalPurseGraphPolicy RegionalPurseGraph { get; set; } = new();
        [JsonPropertyName("regionalPurseCompanion")] public RegionalPurseCompanionPolicy RegionalPurseCompanion { get; set; } = new();
        [JsonPropertyName("drakrPile")] public ScriptPropertyTarget DrakrPile { get; set; } = new();
        [JsonPropertyName("ancientExchangeWorkbench")] public string AncientExchangeWorkbench { get; set; } = "";
        [JsonPropertyName("ancientExchangeRecipes")] public List<ExchangeRecipePolicy> AncientExchangeRecipes { get; set; } = [];
    }

    public class Target
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
    }

    public sealed class KeywordTarget : Target
    {
        [JsonPropertyName("requiredKeyword")] public string RequiredKeyword { get; set; } = "";
    }

    public sealed class GlobalTarget : Target
    {
        [JsonPropertyName("value")] public short Value { get; set; }
    }

    public sealed class PurseTarget : Target
    {
        [JsonPropertyName("counts")] public List<short> Counts { get; set; } = [];
        [JsonPropertyName("floraFormKey")] public string FloraFormKey { get; set; } = "";
        [JsonPropertyName("floraEditorId")] public string FloraEditorId { get; set; } = "";
        [JsonPropertyName("canonicalFormIdBase")] public string CanonicalFormIdBase { get; set; } = "";
        [JsonPropertyName("breakFormIdBase")] public string BreakFormIdBase { get; set; } = "";
        [JsonPropertyName("selectorFormIdBase")] public string SelectorFormIdBase { get; set; } = "";
    }

    public sealed class DenominationPolicy
    {
        [JsonPropertyName("canonicalPercent")] public int CanonicalPercent { get; set; }
        [JsonPropertyName("variantPercent")] public int VariantPercent { get; set; }
        [JsonPropertyName("tieredFamilies")] public List<TieredFamilyPolicy> TieredFamilies { get; set; } = [];
    }

    public class SourceRecordPolicy
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("sourcePlugin")] public string SourcePlugin { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("name")] public string Name { get; set; } = "";
        [JsonPropertyName("sourceValue")] public uint SourceValue { get; set; }
        [JsonPropertyName("sourceWeight")] public float SourceWeight { get; set; }
        [JsonPropertyName("sourceModel")] public string SourceModel { get; set; } = "";
    }

    public sealed class SourceAliasPolicy : SourceRecordPolicy
    {
        [JsonPropertyName("normalizesToTier")] public string NormalizesToTier { get; set; } = "";
    }

    public sealed class TierPolicy
    {
        [JsonPropertyName("formKey")] public string? FormKey { get; set; }
        [JsonPropertyName("formId")] public string? FormId { get; set; }
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("name")] public string Name { get; set; } = "";
        [JsonPropertyName("value")] public uint Value { get; set; }
        [JsonPropertyName("model")] public string Model { get; set; } = "";
        [JsonPropertyName("sourcePlugin")] public string? SourcePlugin { get; set; }
        [JsonPropertyName("sourceName")] public string? SourceName { get; set; }
        [JsonPropertyName("sourceValue")] public uint? SourceValue { get; set; }
        [JsonPropertyName("sourceWeight")] public float? SourceWeight { get; set; }
        [JsonPropertyName("sourceModel")] public string? SourceModel { get; set; }
    }

    public sealed class TieredFamilyPolicy
    {
        [JsonPropertyName("id")] public string Id { get; set; } = "";
        [JsonPropertyName("enabled")] public bool Enabled { get; set; }
        [JsonPropertyName("displayLabel")] public string DisplayLabel { get; set; } = "";
        [JsonPropertyName("backendLabel")] public string BackendLabel { get; set; } = "";
        [JsonPropertyName("ownedRouteKeywordFormId")] public string? OwnedRouteKeywordFormId { get; set; }
        [JsonPropertyName("ownedRouteKeywordEditorId")] public string? OwnedRouteKeywordEditorId { get; set; }
        [JsonPropertyName("perk")] public string? Perk { get; set; }
        [JsonPropertyName("salt")] public string Salt { get; set; } = "";
        [JsonPropertyName("runtimeWeight")] public float RuntimeWeight { get; set; }
        [JsonPropertyName("primarySource")] public SourceRecordPolicy PrimarySource { get; set; } = new();
        [JsonPropertyName("sourceAliases")] public List<SourceAliasPolicy> SourceAliases { get; set; } = [];
        [JsonPropertyName("tiers")] public Dictionary<string, TierPolicy> Tiers { get; set; } = [];
    }

    public sealed class QuestNeutralizationTarget : Target
    {
        [JsonPropertyName("sourcePlugin")] public string SourcePlugin { get; set; } = "";
        [JsonPropertyName("aliasId")] public short AliasId { get; set; }
        [JsonPropertyName("transactionScripts")] public List<string> TransactionScripts { get; set; } = [];
    }

    public sealed class ScriptPropertyTarget : Target
    {
        [JsonPropertyName("script")] public string Script { get; set; } = "";
        [JsonPropertyName("property")] public string Property { get; set; } = "";
        [JsonPropertyName("sourceFormKey")] public string SourceFormKey { get; set; } = "";
        [JsonPropertyName("targetFormKey")] public string TargetFormKey { get; set; } = "";
    }

    public sealed class MintCostOnlyQuestPolicy : Target
    {
        [JsonPropertyName("originalPlugin")] public string OriginalPlugin { get; set; } = "";
        [JsonPropertyName("winningPlugin")] public string WinningPlugin { get; set; } = "";
        [JsonPropertyName("questScript")] public string QuestScript { get; set; } = "";
        [JsonPropertyName("playerAliasId")] public short PlayerAliasId { get; set; }
        [JsonPropertyName("playerAliasScript")] public string PlayerAliasScript { get; set; } = "";
        [JsonPropertyName("removedAliasScripts")] public List<string> RemovedAliasScripts { get; set; } = [];
        [JsonPropertyName("costPropertyNames")] public List<string> CostPropertyNames { get; set; } = [];
    }

    public sealed class ScriptRemovalTarget : Target
    {
        [JsonPropertyName("aliasId")] public short AliasId { get; set; }
        [JsonPropertyName("transactionScript")] public string TransactionScript { get; set; } = "";
        [JsonPropertyName("staleQuestProperties")] public List<string> StaleQuestProperties { get; set; } = [];
    }

    public sealed class InheritedCurrencyBinding
    {
        [JsonPropertyName("script")] public string Script { get; set; } = "";
        [JsonPropertyName("currencyProperty")] public string CurrencyProperty { get; set; } = "";
        [JsonPropertyName("currencyFormKey")] public string CurrencyFormKey { get; set; } = "";
    }

    public sealed class OhzerQuestPolicy
    {
        [JsonPropertyName("formId")] public string FormId { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("aliasId")] public short AliasId { get; set; }
        [JsonPropertyName("aliasName")] public string AliasName { get; set; } = "";
        [JsonPropertyName("templateQuestFormKey")] public string TemplateQuestFormKey { get; set; } = "";
        [JsonPropertyName("templateScript")] public string TemplateScript { get; set; } = "";
        [JsonPropertyName("script")] public string Script { get; set; } = "";
        [JsonPropertyName("currencyProperty")] public string CurrencyProperty { get; set; } = "";
        [JsonPropertyName("currencyFormKey")] public string CurrencyFormKey { get; set; } = "";
        [JsonPropertyName("keywordProperty")] public string KeywordProperty { get; set; } = "";
        [JsonPropertyName("keywordFormKey")] public string KeywordFormKey { get; set; } = "";
    }

    public sealed class StalePropertyTarget : Target
    {
        [JsonPropertyName("staleProperties")] public List<string> StaleProperties { get; set; } = [];
    }

    public sealed class RegionalPurseGraphPolicy
    {
        [JsonPropertyName("ownedFormIdBase")] public string OwnedFormIdBase { get; set; } = "";
        [JsonPropertyName("families")] public List<RegionalPurseFamilyPolicy> Families { get; set; } = [];
    }

    public sealed class RegionalPurseFamilyPolicy
    {
        [JsonPropertyName("familyId")] public string FamilyId { get; set; } = "";
        [JsonPropertyName("sourcePlugin")] public string SourcePlugin { get; set; } = "";
        [JsonPropertyName("primaryCoinFormKey")] public string PrimaryCoinFormKey { get; set; } = "";
        [JsonPropertyName("primaryChange")] public RegionalChangeListPolicy PrimaryChange { get; set; } = new();
        [JsonPropertyName("secondaryChange")] public RegionalChangeListPolicy SecondaryChange { get; set; } = new();
        [JsonPropertyName("purses")] public List<RegionalPurseTarget> Purses { get; set; } = [];
    }

    public sealed class RegionalChangeListPolicy : Target
    {
        [JsonPropertyName("sourceCoinFormKey")] public string SourceCoinFormKey { get; set; } = "";
        [JsonPropertyName("chanceNonePercent")] public int ChanceNonePercent { get; set; }
        [JsonPropertyName("calculateFromAllLevelsLessThanOrEqualPlayer")] public bool CalculateFromAllLevelsLessThanOrEqualPlayer { get; set; }
        [JsonPropertyName("calculateForEachItemInCount")] public bool CalculateForEachItemInCount { get; set; }
        [JsonPropertyName("counts")] public List<short> Counts { get; set; } = [];
    }

    public sealed class RegionalPurseTarget : Target
    {
        [JsonPropertyName("baseCoinCount")] public short BaseCoinCount { get; set; }
        [JsonPropertyName("primaryChangeRolls")] public short PrimaryChangeRolls { get; set; }
        [JsonPropertyName("secondaryChangeRolls")] public short SecondaryChangeRolls { get; set; }
    }

    public sealed class RegionalPurseCompanionPolicy
    {
        [JsonPropertyName("outputPlugin")] public string OutputPlugin { get; set; } = "";
        [JsonPropertyName("terminalFormIdBase")] public string TerminalFormIdBase { get; set; } = "";
        [JsonPropertyName("families")] public List<RegionalPurseCloneFamilyPolicy> Families { get; set; } = [];
    }

    public sealed class RegionalPurseCloneFamilyPolicy
    {
        [JsonPropertyName("familyId")] public string FamilyId { get; set; } = "";
        [JsonPropertyName("floraFormIdBase")] public string FloraFormIdBase { get; set; } = "";
        [JsonPropertyName("budgetFormIdBase")] public string BudgetFormIdBase { get; set; } = "";
    }

    public sealed class ExchangeRecipePolicy
    {
        [JsonPropertyName("formId")] public string FormId { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
        [JsonPropertyName("inputFormKey")] public string InputFormKey { get; set; } = "";
        [JsonPropertyName("inputCount")] public int InputCount { get; set; }
        [JsonPropertyName("outputFormKey")] public string OutputFormKey { get; set; } = "";
        [JsonPropertyName("outputCount")] public ushort OutputCount { get; set; }
        [JsonPropertyName("purpose")] public string Purpose { get; set; } = "";
    }

    public static async Task<int> Main(string[] args)
    {
        try
        {
            return await RunMainAsync(args);
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static async Task<int> RunMainAsync(string[] args)
    {
        if (args is ["--audit-links", var dataFolder, var loadOrderFile, var pluginPath])
        {
            return LinkAudit.Run(dataFolder, loadOrderFile, pluginPath);
        }
        if (args is ["--audit-links", var supportDataFolder, var supportLoadOrderFile,
            var supportPluginPath, var supportPath])
        {
            return LinkAudit.Run(supportDataFolder, supportLoadOrderFile, supportPluginPath, supportPath);
        }
        if (args is ["--write-seq", var seqPluginPath, var seqPath])
        {
            return CurrencyAudit.WriteSeq(seqPluginPath, seqPath);
        }
        if (args is ["--audit-plugin", var auditData, var auditLoadOrder, var auditPlugin,
            var auditPolicy, var auditSeq, var auditOutput])
        {
            return CurrencyAudit.Run(auditData, auditLoadOrder, auditPlugin, auditPolicy, auditSeq, auditOutput);
        }
        if (args is ["--build-regional-purses", var purseData, var mainPlugin,
            var pursePolicy, var purseOutput])
        {
            return RegionalPurseCompanion.Build(purseData, mainPlugin, pursePolicy, purseOutput);
        }

        var result = await SynthesisPipeline.Instance
            .AddPatch<ISkyrimMod, ISkyrimModGetter>(RunPatch, new PatcherPreferences
            {
                ExclusionMods = [ModKey.FromNameAndExtension(OutputPlugin)],
            })
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
        var policyDirectory = state.ExtraSettingsDataPath
            ?? throw new InvalidOperationException("--ExtraDataFolder must point at policy.json.");
        var policy = ReadPolicy(Path.Combine(policyDirectory, "policy.json"));
        ValidatePolicy(policy);
        var providerListing = state.LoadOrder.ListedOrder.Single(listing => listing.ModKey == Exchange);
        var provider = providerListing.Mod
            ?? throw new InvalidOperationException($"{Exchange}: active source plugin could not be loaded.");
        ValidateExchangeWorkbenchProvider(
            provider,
            Path.Combine(state.DataFolderPath.Path, policy.ExchangeWorkbenchProvider.Plugin),
            policy.ExchangeWorkbenchProvider);

        state.PatchMod.ModHeader.Author = "Ensrick";
        state.PatchMod.ModHeader.Description =
            "Owned regional-currency integration: weighted physical tender, regional fixes, safe ancient-coin bank exchange, and disabled coin-smelting recipes.";
        state.PatchMod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small;

        foreach (var target in policy.Overrides.GoldPiles)
        {
            var key = FormKey.Factory(target.FormKey);
            var contexts = new FormLink<IActivatorGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IActivator, IActivatorGetter>(state.LinkCache)
                .ToArray();
            var ece = contexts.Single(context => context.ModKey == Ece);
            Require(ece.Record.EditorID == target.EditorId,
                $"{key}: ECE EditorID is {ece.Record.EditorID}, expected {target.EditorId}.");
            var patch = ece.GetOrAddAsOverride(state.PatchMod);
            ClearCompression(patch);
            Console.WriteLine($"Forwarded ECE activator {key} {target.EditorId}.");
        }

        var denominationForms = CreateDenominationRecords(state, policy.Denominations);
        foreach (var target in policy.Overrides.CoinPurses)
        {
            PatchPurse(state, target, denominationForms["septim"]);
        }

        PatchGold(state, policy.Overrides.Gold);
        PatchMintGlobal(state, policy.Overrides.MintAutoConvert);
        NeutralizeEcePlayerCurrencyQuests(state, policy.Overrides.EcePlayerCurrencyQuests);
        RestoreMintCostOnlyQuestBindings(state, policy.Overrides.MintCostOnlyQuests);
        RemoveMadranTransactionScript(state, policy.Overrides.MintMadranQuest);
        DisableMintExchangeInfos(state, policy.Overrides.DisabledMintExchangeInfos);
        RetargetMintBackendConditions(state, policy.Overrides.MintBackendConditionInfos);
        PatchRegionalPurseGraph(state, policy.Overrides.RegionalPurseGraph,
            policy.Denominations, denominationForms);
        PatchDrakrPile(state, policy.Overrides.DrakrPile);
        CreateAncientExchangeRecipes(state, policy.Overrides.AncientExchangeWorkbench,
            policy.Overrides.AncientExchangeRecipes);

        foreach (var target in policy.DisabledRecipes.Concat(policy.DisabledModernBankRecipes)
                     .OrderBy(item => FormKey.Factory(item.FormKey).ID))
        {
            var key = FormKey.Factory(target.FormKey);
            var contexts = new FormLink<IConstructibleObjectGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IConstructibleObject, IConstructibleObjectGetter>(state.LinkCache)
                .ToArray();
            var source = contexts.Single(context => context.ModKey == CoinPatch);
            Require(source.Record.EditorID == target.EditorId,
                $"{key}: recipe EditorID is {source.Record.EditorID}, expected {target.EditorId}.");
            Require(!source.Record.WorkbenchKeyword.IsNull,
                $"{key} {target.EditorId}: source recipe is already disabled; review policy.");
            var patch = source.GetOrAddAsOverride(state.PatchMod);
            patch.WorkbenchKeyword.SetTo(FormKey.Null);
            ClearCompression(patch);
            Console.WriteLine($"Disabled legacy currency COBJ {key} {target.EditorId}.");
        }

        CreateRuntimeQuest(state, policy.Quest);
        ValidateDialogParentScopes(state, policy.Overrides.DisabledMintExchangeInfos,
            policy.Overrides.MintBackendConditionInfos);

        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        Require(records.Length == 1772, $"Expected exactly 1772 records, got {records.Length}.");
        Require(records.Count(record => record is IActivatorGetter) == 3,
            "Expected two pile forwards and one Drakr pile override.");
        Require(records.Count(record => record is ILeveledItemGetter) == 1605,
            "Expected 27 purse overrides, 144 owned Septim purse lists, and 1434 owned regional probability-DAG lists.");
        Require(records.Count(record => record is IMiscItemGetter) == 55,
            "Expected Gold001 plus all changed, owned, and alias-backed tier MISC records.");
        Require(records.Count(record => record is IGlobalGetter) == 1, "Expected one GLOB override.");
        Require(records.Count(record => record is IConstructibleObjectGetter) == 42,
            "Expected 33 disabled COBJ overrides and nine owned ancient exchange recipes.");
        Require(records.Count(record => record is IQuestGetter) == 5,
            "Expected four compatibility QUST overrides and one owned runtime QUST.");
        Require(records.Count(record => record is IKeywordGetter) == 1,
            "Expected one owned Sancar route keyword.");
        Require(records.Count(record => record is IDialogTopicGetter) == 20,
            "Expected exactly twenty scoped parent DIAL overrides for the forty INFO overrides.");
        Require(records.Count(record => record is IDialogResponsesGetter) == 40,
            "Expected 38 disabled obsolete M.I.N.T. exchange INFOs and two backend-aware horse conditions.");
        Require(!records.Any(record => record.IsDeleted), "Output contains a deleted record.");
        Require(records.Count(record => record.FormKey.ModKey == state.PatchMod.ModKey) == 1623,
            "Owned FormKey count differs from 1578 purse graph/list records, thirty-four denominations, nine recipes, one route keyword, and one runtime quest.");
        Console.WriteLine("Generated 1772 records: all eighteen coin designs have exact 1/10/100 tiers; 24 authored regional purses preserve their full source total-value distribution and use whole-purse 80/20 denomination outcomes; nine ancient exchanges are value-parity; 33 legacy recipes are disabled; and ECE/M.I.N.T. transaction owners remain neutralized.");
    }

    public sealed class MintExchangeInfoPolicy
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("parentTopicFormKey")] public string ParentTopicFormKey { get; set; } = "";
        [JsonPropertyName("parentTopicEditorId")] public string ParentTopicEditorId { get; set; } = "";
        [JsonPropertyName("transactionScripts")] public List<string> TransactionScripts { get; set; } = [];
        [JsonPropertyName("conditionCount")] public int ConditionCount { get; set; }
    }

    public sealed class MintBackendConditionPolicy
    {
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("parentTopicFormKey")] public string ParentTopicFormKey { get; set; } = "";
        [JsonPropertyName("parentTopicEditorId")] public string ParentTopicEditorId { get; set; } = "";
        [JsonPropertyName("script")] public string Script { get; set; } = "";
        [JsonPropertyName("conditionIndex")] public int ConditionIndex { get; set; }
        [JsonPropertyName("sourceCurrency")] public string SourceCurrency { get; set; } = "";
        [JsonPropertyName("backendCurrency")] public string BackendCurrency { get; set; } = "";
        [JsonPropertyName("comparisonGlobal")] public string ComparisonGlobal { get; set; } = "";
        [JsonPropertyName("conditionCount")] public int ConditionCount { get; set; }
        [JsonPropertyName("vmadVersion")] public int VmadVersion { get; set; }
        [JsonPropertyName("vmadObjectFormat")] public int VmadObjectFormat { get; set; }
        [JsonPropertyName("vmadCurrencyProperty")] public string VmadCurrencyProperty { get; set; } = "";
        [JsonPropertyName("vmadProperties")] public List<MintVmadObjectPropertyPolicy> VmadProperties { get; set; } = [];
    }

    public sealed class MintVmadObjectPropertyPolicy
    {
        [JsonPropertyName("name")] public string Name { get; set; } = "";
        [JsonPropertyName("formKey")] public string FormKey { get; set; } = "";
        [JsonPropertyName("alias")] public int Alias { get; set; }
    }

    internal readonly record struct DenominationCounts(short Copper, short Silver, short Gold, string? BrokenTier);

    internal static DenominationCounts DecomposeSeptims(int amount, bool singleBreak)
    {
        Require(amount >= 0 && amount <= short.MaxValue, $"Purse amount {amount} is outside LVLI count range.");
        var gold = amount / 100;
        var remainder = amount % 100;
        var silver = remainder / 10;
        var copper = remainder % 10;
        string? brokenTier = null;
        if (singleBreak && gold > 0)
        {
            gold--;
            silver += 10;
            brokenTier = "gold";
        }
        else if (singleBreak && silver > 0)
        {
            silver--;
            copper += 10;
            brokenTier = "silver";
        }
        var result = new DenominationCounts(
            checked((short)copper), checked((short)silver), checked((short)gold), brokenTier);
        Require(ValueOf(result) == amount, $"Denomination decomposition failed to conserve {amount}.");
        return result;
    }

    internal static int ValueOf(DenominationCounts counts) =>
        checked(counts.Copper + (10 * counts.Silver) + (100 * counts.Gold));

    private static uint ParseOwnedId(string value) => uint.Parse(value,
        System.Globalization.NumberStyles.HexNumber, System.Globalization.CultureInfo.InvariantCulture);

    private static LeveledItem NewLeveledList(FormKey key, string editorId, LeveledItem.Flag flags) =>
        new(key, SkyrimRelease.SkyrimSE)
        {
            EditorID = editorId,
            Flags = flags,
            ChanceNone = new Percent(0.0),
            Entries = [],
        };

    private static void AddLeveledEntry(ILeveledItem list, FormKey form, short count)
    {
        list.Entries ??= [];
        var entry = new LeveledItemEntry
        {
            Data = new LeveledItemEntryData { Level = 1, Count = count },
        };
        entry.Data.Reference.SetTo(form);
        list.Entries.Add(entry);
    }

    private static void CreateUseAllPurseList(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        FormKey key,
        string editorId,
        DenominationCounts counts,
        IReadOnlyDictionary<string, FormKey> forms)
    {
        var list = NewLeveledList(key, editorId, LeveledItem.Flag.UseAll);
        if (counts.Copper > 0) AddLeveledEntry(list, forms["copper"], counts.Copper);
        if (counts.Silver > 0) AddLeveledEntry(list, forms["silver"], counts.Silver);
        if (counts.Gold > 0) AddLeveledEntry(list, forms["gold"], counts.Gold);
        Require(list.Entries is { Count: > 0 }, $"{key}: a positive purse amount produced an empty list.");
        state.PatchMod.LeveledItems.Add(list);
    }

    private static IReadOnlyDictionary<string, IReadOnlyDictionary<string, FormKey>> CreateDenominationRecords(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        DenominationPolicy policy)
    {
        var expectedTiers = new[] { "copper", "silver", "gold" };
        var expectedValues = new Dictionary<string, uint>(StringComparer.Ordinal)
        {
            ["copper"] = 1,
            ["silver"] = 10,
            ["gold"] = 100,
        };
        var physicalForms = new HashSet<FormKey>();
        var familyForms = new Dictionary<string, IReadOnlyDictionary<string, FormKey>>(StringComparer.Ordinal);

        foreach (var family in policy.TieredFamilies)
        {
            if (family.OwnedRouteKeywordFormId is not null)
            {
                Require(!string.IsNullOrWhiteSpace(family.OwnedRouteKeywordEditorId),
                    $"{family.Id}: owned route keyword EditorID is absent.");
                var routeKey = new FormKey(state.PatchMod.ModKey,
                    ParseOwnedId(family.OwnedRouteKeywordFormId));
                state.PatchMod.Keywords.Add(new Keyword(routeKey, SkyrimRelease.SkyrimSE)
                {
                    EditorID = family.OwnedRouteKeywordEditorId,
                });
            }

            Require(family.Tiers.Keys.Order(StringComparer.Ordinal)
                    .SequenceEqual(expectedTiers.Order(StringComparer.Ordinal)),
                $"{family.Id}: policy must define copper, silver, and gold exactly once.");
            var primary = ResolvePinnedSource(state, family.PrimarySource, $"{family.Id} primary source");
            var tierForms = new Dictionary<string, FormKey>(StringComparer.Ordinal);
            foreach (var tierName in expectedTiers)
            {
                var tier = family.Tiers[tierName];
                Require(tier.Value == expectedValues[tierName] &&
                        tier.Name == $"{char.ToUpperInvariant(tierName[0])}{tierName[1..]} {family.DisplayLabel}" &&
                        !string.IsNullOrWhiteSpace(tier.Model),
                    $"{family.Id}/{tierName}: exact tier value/name/model contract changed.");
                Require((tier.FormKey is null) != (tier.FormId is null),
                    $"{family.Id}/{tierName}: exactly one of formKey or formId is required.");

                FormKey tierKey;
                if (tier.FormKey is not null)
                {
                    tierKey = FormKey.Factory(tier.FormKey);
                    var sourcePolicy = tierName == "copper"
                        ? family.PrimarySource
                        : new SourceRecordPolicy
                        {
                            FormKey = tier.FormKey,
                            SourcePlugin = tier.SourcePlugin ?? string.Empty,
                            EditorId = tier.EditorId,
                            Name = tier.SourceName ?? tier.Name,
                            SourceValue = tier.SourceValue ?? uint.MaxValue,
                            SourceWeight = tier.SourceWeight ?? float.NaN,
                            SourceModel = tier.SourceModel ?? string.Empty,
                        };
                    var sourceContext = ResolvePinnedSource(state, sourcePolicy,
                        $"{family.Id}/{tierName} existing tier");
                    var source = sourceContext.Record;
                    var needsOverride = source.Name?.String != tier.Name || source.Value != tier.Value ||
                        Math.Abs(source.Weight - family.RuntimeWeight) >= 0.0001f ||
                        !string.Equals(source.Model?.File.ToString(), tier.Model,
                            StringComparison.OrdinalIgnoreCase) || !HasKeyword(source, VendorNoSale);
                    if (needsOverride)
                    {
                        var patch = sourceContext.GetOrAddAsOverride(state.PatchMod);
                        ApplyTierFields(patch, tier, family.RuntimeWeight);
                    }
                }
                else
                {
                    tierKey = new FormKey(state.PatchMod.ModKey, ParseOwnedId(tier.FormId!));
                    CreateOwnedTier(state, primary.Record, family, tierName, tierKey, tier);
                }
                Require(physicalForms.Add(tierKey),
                    $"{family.Id}/{tierName}: physical FormKey is duplicated across currency designs.");
                tierForms.Add(tierName, tierKey);
            }

            foreach (var alias in family.SourceAliases)
            {
                Require(expectedValues.ContainsKey(alias.NormalizesToTier),
                    $"{family.Id}: alias names unknown tier {alias.NormalizesToTier}.");
                var aliasContext = ResolvePinnedSource(state, alias, $"{family.Id} source alias");
                var tier = family.Tiers[alias.NormalizesToTier];
                ApplyTierFields(aliasContext.GetOrAddAsOverride(state.PatchMod), tier,
                    family.RuntimeWeight);
                Require(physicalForms.Add(aliasContext.Record.FormKey),
                    $"{family.Id}: source alias FormKey is duplicated across currency designs.");
            }
            familyForms.Add(family.Id, tierForms);
            Console.WriteLine($"Created exact 1/10/100 {family.Id} family from {family.PrimarySource.FormKey}.");
        }

        return familyForms;
    }

    private static IModContext<ISkyrimMod, ISkyrimModGetter, IMiscItem, IMiscItemGetter>
        ResolvePinnedSource(
            IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
            SourceRecordPolicy policy,
            string description)
    {
        var key = FormKey.Factory(policy.FormKey);
        var sourceMod = ModKey.FromNameAndExtension(policy.SourcePlugin);
        var contexts = new FormLink<IMiscItemGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IMiscItem, IMiscItemGetter>(state.LinkCache)
                .ToArray();
        var sourceContext = contexts.Single(context => context.ModKey == sourceMod);
        var source = sourceContext.Record;
        Require(source.EditorID == policy.EditorId && source.Name?.String == policy.Name &&
                source.Value == policy.SourceValue &&
                Math.Abs(source.Weight - policy.SourceWeight) < 0.0001f &&
                string.Equals(source.Model?.File.ToString(), policy.SourceModel,
                    StringComparison.OrdinalIgnoreCase),
            $"{key}: pinned {description} identity/value/weight/model changed.");
        return sourceContext;
    }

    private static void CreateOwnedTier(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IMiscItemGetter source,
        TieredFamilyPolicy family,
        string tier,
        FormKey key,
        TierPolicy policy)
    {
        var item = new MiscItem(key, SkyrimRelease.SkyrimSE)
        {
            EditorID = policy.EditorId,
            Name = policy.Name,
            Value = policy.Value,
            Weight = family.RuntimeWeight,
            ObjectBounds = source.ObjectBounds.DeepCopy(),
            Model = source.Model?.DeepCopy(),
            Icons = source.Icons?.DeepCopy(),
            Destructible = source.Destructible?.DeepCopy(),
        };
        if (item.Model is null) item.Model = new Model();
        item.Model.File = policy.Model;
        item.PickUpSound.SetTo(source.PickUpSound.FormKey);
        item.PutDownSound.SetTo(source.PutDownSound.FormKey);
        if (source.Keywords is not null)
        {
            item.Keywords = [];
            foreach (var keyword in source.Keywords)
            {
                item.Keywords.Add(new FormLink<IKeywordGetter>(keyword.FormKey));
            }
        }
        EnsureKeyword(item, VendorNoSale);
        state.PatchMod.MiscItems.Add(item);
        Console.WriteLine($"Created {tier} {family.Id} {key} ({policy.Value}) using {policy.Model}.");
    }

    private static void ApplyTierFields(IMiscItem item, TierPolicy tier, float runtimeWeight)
    {
        item.Name = tier.Name;
        item.Value = tier.Value;
        item.Weight = runtimeWeight;
        item.Model ??= new Model();
        item.Model.File = tier.Model;
        EnsureKeyword(item, VendorNoSale);
        ClearCompression(item);
    }

    private static bool HasKeyword(IMiscItemGetter item, FormKey keyword) =>
        item.Keywords?.Any(candidate => candidate.FormKey == keyword) == true;

    private static void EnsureKeyword(IMiscItem item, FormKey keyword)
    {
        item.Keywords ??= [];
        if (!item.Keywords.Any(candidate => candidate.FormKey == keyword))
        {
            item.Keywords.Add(new FormLink<IKeywordGetter>(keyword));
        }
    }

    private static void PatchPurse(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        PurseTarget target,
        IReadOnlyDictionary<string, FormKey> septimForms)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<ILeveledItemGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ILeveledItem, ILeveledItemGetter>(state.LinkCache)
            .ToArray();
        Require(contexts.Any(context => context.ModKey == Ece),
            $"{key}: ECE purse override is absent from the active load order.");
        // ResolveAllContexts is priority ordered: the active winner is first.
        var winner = contexts[0];
        Require(winner.Record.EditorID == target.EditorId,
            $"{key}: winning purse EditorID is {winner.Record.EditorID}, expected {target.EditorId}.");
        Require(target.Counts.Count == 16 && target.Counts.Distinct().Count() == 16,
            $"{key}: purse policy must contain 16 unique counts.");

        var floraKey = FormKey.Factory(target.FloraFormKey);
        var flora = state.LinkCache.Resolve<IFloraGetter>(floraKey);
        Require(flora.EditorID == target.FloraEditorId && flora.Ingredient.FormKey == key,
            $"{floraKey}: purse FLOR must be {target.FloraEditorId} and harvest {key}.");

        var canonicalBase = ParseOwnedId(target.CanonicalFormIdBase);
        var breakBase = ParseOwnedId(target.BreakFormIdBase);
        var selectorBase = ParseOwnedId(target.SelectorFormIdBase);
        var selectors = new List<FormKey>();
        for (var index = 0; index < target.Counts.Count; index++)
        {
            var amount = target.Counts[index];
            var canonical = DecomposeSeptims(amount, false);
            var broken = DecomposeSeptims(amount, true);
            var canonicalKey = new FormKey(state.PatchMod.ModKey, canonicalBase + checked((uint)index));
            var breakKey = new FormKey(state.PatchMod.ModKey, breakBase + checked((uint)index));
            var selectorKey = new FormKey(state.PatchMod.ModKey, selectorBase + checked((uint)index));
            CreateUseAllPurseList(state, canonicalKey,
                $"Ensrick_SeptimPurse_{target.EditorId}_{amount:D2}_Canonical", canonical, septimForms);
            CreateUseAllPurseList(state, breakKey,
                $"Ensrick_SeptimPurse_{target.EditorId}_{amount:D2}_SingleBreak", broken, septimForms);

            var selector = NewLeveledList(selectorKey,
                $"Ensrick_SeptimPurse_{target.EditorId}_{amount:D2}_80_20", 0);
            for (var choice = 0; choice < 5; choice++)
            {
                AddLeveledEntry(selector, choice < 4 ? canonicalKey : breakKey, 1);
            }
            state.PatchMod.LeveledItems.Add(selector);
            selectors.Add(selectorKey);
            Require(ValueOf(canonical) == amount && ValueOf(broken) == amount,
                $"{key}: purse amount {amount} does not conserve value.");
        }

        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.Flags = 0;
        patch.ChanceNone = new Percent(0.0);
        patch.Global.SetTo(FormKey.Null);
        patch.Entries ??= [];
        patch.Entries.Clear();
        foreach (var selector in selectors)
        {
            AddLeveledEntry(patch, selector, 1);
        }
        ClearCompression(patch);
        Console.WriteLine($"Rebuilt purse LVLI {key} {target.EditorId}: 16 equal amount selectors, each with four canonical and one single-break value-conserving outcomes.");
    }

    private static void PatchGold(IPatcherState<ISkyrimMod, ISkyrimModGetter> state, KeywordTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IMiscItemGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IMiscItem, IMiscItemGetter>(state.LinkCache)
            .ToArray();
        Require(contexts.Length > 0, $"{key}: missing Gold001.");
        // Preserve every field from the active winning Gold001 record.
        var winner = contexts[0];
        Require(winner.Record.EditorID == target.EditorId,
            $"{key}: winning EditorID is {winner.Record.EditorID}, expected {target.EditorId}.");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.Keywords ??= [];
        var keyword = FormKey.Factory(target.RequiredKeyword);
        if (!patch.Keywords.Any(link => link.FormKey == keyword))
        {
            patch.Keywords.Add(new FormLink<IKeywordGetter>(keyword));
        }
        ClearCompression(patch);
        Require(patch.Keywords.Count(link => link.FormKey == GiftUniversallyValuable) == 1,
            "Gold001 must contain GiftUniversallyValuable exactly once.");
    }

    private static void PatchMintGlobal(IPatcherState<ISkyrimMod, ISkyrimModGetter> state, GlobalTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IGlobalGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IGlobal, IGlobalGetter>(state.LinkCache)
            .ToArray();
        Require(contexts.Length > 0, $"{key}: missing DES_ConvertCoins.");
        var winner = contexts[0];
        Require(winner.Record.EditorID == target.EditorId,
            $"{key}: winning EditorID is {winner.Record.EditorID}, expected {target.EditorId}.");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        Require(patch is GlobalShort, "DES_ConvertCoins must remain a GlobalShort.");
        var shortGlobal = (GlobalShort)patch;
        shortGlobal.Data = target.Value;
        ClearCompression(shortGlobal);
    }

    private static void NeutralizeEcePlayerCurrencyQuests(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyList<QuestNeutralizationTarget> targets)
    {
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var sourceMod = ModKey.FromNameAndExtension(target.SourcePlugin);
            var contexts = new FormLink<IQuestGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
                .ToArray();
            var winner = contexts[0];
            Require(winner.ModKey == sourceMod,
                $"{key}: winning ECE player-currency quest is {winner.ModKey}, expected {sourceMod}.");
            Require(winner.Record.EditorID == target.EditorId &&
                    winner.Record.Flags.HasFlag(Quest.Flag.StartGameEnabled),
                $"{key}: pinned ECE quest identity/start flag changed.");
            var patch = winner.GetOrAddAsOverride(state.PatchMod);
            var vmad = patch.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: ECE quest VMAD is missing.");
            var alias = vmad.Aliases.Single(candidate => candidate.Property.Alias == target.AliasId);
            var actualNames = alias.Scripts.Select(script => script.Name).ToArray();
            Require(actualNames.SequenceEqual(target.TransactionScripts),
                $"{key}: ECE transaction script set/order changed ({string.Join(", ", actualNames)}).");
            foreach (var scriptName in target.TransactionScripts)
            {
                var script = alias.Scripts.Single(candidate => candidate.Name == scriptName);
                alias.Scripts.Remove(script);
            }
            patch.Flags &= ~Quest.Flag.StartGameEnabled;
            ClearCompression(patch);
            Require(alias.Scripts.Count == 0 && !patch.Flags.HasFlag(Quest.Flag.StartGameEnabled),
                $"{key}: ECE player currency alias was not fully neutralized.");
            Console.WriteLine($"Neutralized ECE player-currency quest {key}: removed {target.TransactionScripts.Count} exact scripts and StartGameEnabled only.");
        }
    }

    private static void PatchEceAltCurrencyQuest(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        ScriptPropertyTarget target,
        IReadOnlyList<InheritedCurrencyBinding> bindings)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IQuestGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
            .ToArray();
        var source = contexts.Single(context => context.ModKey == CoinPatch);
        Require(source.Record.EditorID == target.EditorId,
            $"{key}: ECE quest EditorID is {source.Record.EditorID}, expected {target.EditorId}.");
        var patch = source.GetOrAddAsOverride(state.PatchMod);
        var vmad = patch.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: ECE quest VMAD is missing.");
        var alias = vmad.Aliases.Single(candidate =>
            candidate.Scripts.Any(script => script.Name == target.Script));
        var script = alias.Scripts.Single(candidate => candidate.Name == target.Script);
        var property = script.Properties.OfType<ScriptObjectProperty>()
            .Single(candidate => candidate.Name == target.Property);
        var expectedSource = FormKey.Factory(target.SourceFormKey);
        var expectedTarget = FormKey.Factory(target.TargetFormKey);
        Require(property.Object.FormKey == expectedSource,
            $"{key}: {target.Script}.{target.Property} is {property.Object.FormKey}, expected shipped {expectedSource}.");
        property.Object.SetTo(expectedTarget);

        foreach (var binding in bindings)
        {
            var currencyScript = alias.Scripts.Single(candidate => candidate.Name == binding.Script);
            Require(!currencyScript.Properties.Any(candidate => candidate.Name == "altCoins"),
                $"{key}: vendor now binds {binding.Script}.altCoins; review the owned repair.");
            var currencyProperty = currencyScript.Properties.OfType<ScriptObjectProperty>()
                .Single(candidate => candidate.Name == binding.CurrencyProperty);
            var currencyFormKey = FormKey.Factory(binding.CurrencyFormKey);
            Require(currencyProperty.Object.FormKey == currencyFormKey,
                $"{key}: {binding.Script}.{binding.CurrencyProperty} is {currencyProperty.Object.FormKey}, expected {currencyFormKey}.");
            var inherited = new ScriptObjectProperty { Name = "altCoins" };
            inherited.Object.SetTo(currencyFormKey);
            currencyScript.Properties.Add(inherited);
            Console.WriteLine($"Bound inherited {binding.Script}.altCoins to {currencyFormKey} before first regional transition.");
        }
        ClearCompression(patch);
        Console.WriteLine($"Corrected ECE VMAD {key} {target.Script}.{target.Property}: {expectedSource} -> {expectedTarget}.");
    }

    private static void CreateOhzerQuest(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        OhzerQuestPolicy target)
    {
        var templateKey = FormKey.Factory(target.TemplateQuestFormKey);
        var contexts = new FormLink<IQuestGetter>(templateKey)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
            .ToArray();
        var source = contexts.Single(context => context.ModKey == CoinPatch).Record;
        var sourceAlias = source.VirtualMachineAdapter?.Aliases.Single(alias => alias.Property.Alias == 0)
            ?? throw new InvalidOperationException($"{templateKey}: ECE currency alias VMAD is missing.");
        var template = sourceAlias.Scripts.Single(script => script.Name == target.TemplateScript);
        Require(template.Properties.All(property => property is ScriptObjectProperty) &&
                template.Properties.Count == 15,
            $"{templateKey}: ECE Ohzer template property structure changed; review the owned quest.");
        var templateObjects = template.Properties.OfType<ScriptObjectProperty>()
            .ToDictionary(property => property.Name, StringComparer.Ordinal);
        Require(templateObjects["Oshka"].Object.FormKey == FormKey.Factory("000871:exchangeCurrency_patch_COIN.esp") &&
                templateObjects["OshkaPerk"].Object.FormKey == FormKey.Factory("000872:exchangeCurrency_patch_COIN.esp"),
            $"{templateKey}: ECE Ohzer template-specific bindings changed.");

        var questId = uint.Parse(target.FormId, System.Globalization.NumberStyles.HexNumber,
            System.Globalization.CultureInfo.InvariantCulture);
        var questKey = new FormKey(state.PatchMod.ModKey, questId);
        var quest = new Quest(questKey, SkyrimRelease.SkyrimSE)
        {
            EditorID = target.EditorId,
            Flags = Quest.Flag.StartGameEnabled,
            Priority = 0,
            QuestFormVersion = 65,
            Type = Quest.TypeEnum.None,
            NextAliasID = 1,
            VirtualMachineAdapter = new QuestAdapter(),
        };
        var alias = new QuestAlias
        {
            ID = checked((uint)target.AliasId),
            Type = QuestAlias.TypeEnum.Reference,
            Name = target.AliasName,
            Flags = 0,
        };
        alias.ForcedReference.SetTo(PlayerRef);
        quest.Aliases.Add(alias);

        var aliasAdapter = new QuestFragmentAlias();
        aliasAdapter.Property.Object.SetTo(questKey);
        aliasAdapter.Property.Alias = target.AliasId;
        var script = new ScriptEntry { Name = target.Script };
        foreach (var property in template.Properties.OfType<ScriptObjectProperty>())
        {
            if (property.Name is "Oshka" or "OshkaPerk") continue;
            var copy = new ScriptObjectProperty { Name = property.Name };
            copy.Object.SetTo(property.Object.FormKey);
            script.Properties.Add(copy);
        }
        var currency = new ScriptObjectProperty { Name = target.CurrencyProperty };
        currency.Object.SetTo(FormKey.Factory(target.CurrencyFormKey));
        script.Properties.Add(currency);
        var keyword = new ScriptObjectProperty { Name = target.KeywordProperty };
        keyword.Object.SetTo(FormKey.Factory(target.KeywordFormKey));
        script.Properties.Add(keyword);
        Require(script.Properties.Count == 15,
            $"{questKey}: owned Ohzer script must expose 13 inherited bindings, its currency, and its keyword.");
        aliasAdapter.Scripts.Add(script);
        quest.VirtualMachineAdapter.Aliases.Add(aliasAdapter);
        state.PatchMod.Quests.Add(quest);
        Console.WriteLine($"Created owned neutral-rate Ohzer transaction quest {questKey} with script {target.Script}.");
    }

    private static void RestoreMintCostOnlyQuestBindings(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyList<MintCostOnlyQuestPolicy> targets)
    {
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var originalMod = ModKey.FromNameAndExtension(target.OriginalPlugin);
            var winningMod = ModKey.FromNameAndExtension(target.WinningPlugin);
            var contexts = new FormLink<IQuestGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
                .ToArray();
            var original = contexts.Single(context => context.ModKey == originalMod).Record;
            // Select the immutable input baseline by its named provider. A prior pass may
            // already have created the output override, which then appears first in the
            // mutable link cache and must not become the provenance record.
            var winningInput = contexts.Single(context => context.ModKey == winningMod);
            Require(original.EditorID == target.EditorId && winningInput.Record.EditorID == target.EditorId,
                $"{key}: M.I.N.T. quest identity changed.");

            var originalVmad = original.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: original M.I.N.T. quest VMAD is missing.");
            var originalQuestScript = originalVmad.Scripts.Single(script => script.Name == target.QuestScript);
            if (target.CostPropertyNames.Count > 0)
            {
                Require(originalQuestScript.Properties.Select(property => property.Name).ToHashSet(StringComparer.Ordinal)
                        .SetEquals(target.CostPropertyNames),
                    $"{key}: {target.QuestScript} property schema changed.");
            }
            var originalAlias = originalVmad.Aliases.Single(alias =>
                alias.Property.Alias == target.PlayerAliasId);
            var originalAliasNames = originalAlias.Scripts.Select(script => script.Name).ToHashSet(StringComparer.Ordinal);
            Require(originalAliasNames.Contains(target.PlayerAliasScript) &&
                    target.RemovedAliasScripts.All(originalAliasNames.Contains),
                $"{key}: original player-alias currency script set changed.");

            var patch = winningInput.GetOrAddAsOverride(state.PatchMod);
            var vmad = patch.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: winning M.I.N.T. quest VMAD is missing.");
            Require(!vmad.Scripts.Any(script => script.Name == target.QuestScript),
                $"{key}: winning patch unexpectedly retains {target.QuestScript}; review single-owner scope.");
            vmad.Scripts.Add(originalQuestScript.DeepCopy());

            var alias = vmad.Aliases.SingleOrDefault(candidate =>
                candidate.Property.Alias == target.PlayerAliasId);
            if (alias is null)
            {
                alias = new QuestFragmentAlias();
                alias.Property.Object.SetTo(key);
                alias.Property.Alias = target.PlayerAliasId;
                vmad.Aliases.Add(alias);
            }
            Require(!alias.Scripts.Any(script => script.Name == target.PlayerAliasScript) &&
                    target.RemovedAliasScripts.All(name => !alias.Scripts.Any(script => script.Name == name)),
                $"{key}: winning patch unexpectedly retains a M.I.N.T. transaction alias script.");
            alias.Scripts.Add(originalAlias.Scripts.Single(script =>
                script.Name == target.PlayerAliasScript).DeepCopy());
            ClearCompression(patch);
            Console.WriteLine($"Restored cost-only binding {target.QuestScript} and proxy {target.PlayerAliasScript} on {key}; transaction aliases remain absent.");
        }
    }

    private static void RemoveMadranTransactionScript(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        ScriptRemovalTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IQuestGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
            .ToArray();
        // RestoreMintCostOnlyQuestBindings touches this same QUST first, so the patch
        // context can already be the mutable cache winner. Keep the reviewed vendor
        // baseline explicit and merge this removal into the existing output override.
        var winningInput = contexts.Single(context => context.ModKey == EceMintUlfric);
        Require(winningInput.Record.EditorID == target.EditorId,
            $"{key}: expected ECE M.I.N.T. Ulfric input {target.EditorId}, found {winningInput.Record.EditorID}.");
        var patch = winningInput.GetOrAddAsOverride(state.PatchMod);
        var vmad = patch.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: Ma'dran quest VMAD is missing.");
        var alias = vmad.Aliases.Single(candidate => candidate.Property.Alias == target.AliasId);
        var script = alias.Scripts.Single(candidate => candidate.Name == target.TransactionScript);
        alias.Scripts.Remove(script);

        var questFragment = vmad.Scripts.Single(candidate =>
            candidate.Name == "QF_DES_UlfricWindhelmService_03000002");
        foreach (var propertyName in target.StaleQuestProperties)
        {
            var stale = questFragment.Properties.Single(property => property.Name == propertyName);
            questFragment.Properties.Remove(stale);
            Console.WriteLine($"Removed stale M.I.N.T./ECE quest-fragment VMAD property {propertyName}.");
        }
        ClearCompression(patch);
        Require(alias.Scripts.All(candidate => candidate.Name != target.TransactionScript),
            $"{key}: Ma'dran transaction script remains attached.");
        Console.WriteLine($"Removed Ma'dran alias {target.AliasId} transaction script {target.TransactionScript}; no barter swapper was substituted.");
    }

    private static void DisableMintExchangeInfos(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyList<MintExchangeInfoPolicy> targets)
    {
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var sourceMod = state.LoadOrder.ListedOrder.Single(listing => listing.ModKey == key.ModKey).Mod
                ?? throw new InvalidOperationException($"{key.ModKey}: M.I.N.T. module is not loaded.");
            var parent = sourceMod.DialogTopics.Single(topic =>
                topic.Responses.Any(response => response.FormKey == key));
            Require(parent.FormKey == FormKey.Factory(target.ParentTopicFormKey) &&
                    parent.EditorID == target.ParentTopicEditorId,
                $"{key}: parent M.I.N.T. exchange topic changed.");

            var contexts = new FormLink<IDialogResponsesGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IDialogResponses, IDialogResponsesGetter>(state.LinkCache)
                .ToArray();
            var winner = contexts[0];
            Require(winner.ModKey == key.ModKey && string.IsNullOrEmpty(winner.Record.EditorID) &&
                    winner.Record.Conditions.Count == target.ConditionCount,
                $"{key}: pinned M.I.N.T. exchange INFO identity/condition count changed.");
            var sourceScripts = winner.Record.VirtualMachineAdapter?.Scripts.Select(script => script.Name).ToArray()
                ?? [];
            Require(sourceScripts.SequenceEqual(target.TransactionScripts),
                $"{key}: transaction TIF/fragment set changed ({string.Join(", ", sourceScripts)}).");

            var patch = winner.GetOrAddAsOverride(state.PatchMod);
            if (patch.VirtualMachineAdapter is not null)
            {
                foreach (var scriptName in target.TransactionScripts)
                {
                    var script = patch.VirtualMachineAdapter.Scripts.Single(entry => entry.Name == scriptName);
                    patch.VirtualMachineAdapter.Scripts.Remove(script);
                }
                Require(patch.VirtualMachineAdapter.Scripts.Count == 0,
                    $"{key}: obsolete M.I.N.T. exchange callback remains.");
            }

            var data = new GetGlobalValueConditionData();
            data.Global.Link.SetTo(MintConvertGlobal);
            patch.Conditions.Insert(0, new ConditionFloat
            {
                CompareOperator = CompareOperator.EqualTo,
                ComparisonValue = 1.0f,
                Flags = 0,
                Data = data,
            });
            ClearCompression(patch);
            Console.WriteLine($"Disabled obsolete M.I.N.T. exchange INFO {key}: stripped exact TIF and gated on DES_ConvertCoins == 1 while global is forced 0.");
        }
    }

    private static void RetargetMintBackendConditions(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyList<MintBackendConditionPolicy> targets)
    {
        foreach (var target in targets)
        {
            var key = FormKey.Factory(target.FormKey);
            var sourceMod = state.LoadOrder.ListedOrder.Single(listing => listing.ModKey == key.ModKey).Mod
                ?? throw new InvalidOperationException($"{key.ModKey}: M.I.N.T. module is not loaded.");
            var parent = sourceMod.DialogTopics.Single(topic =>
                topic.Responses.Any(response => response.FormKey == key));
            Require(parent.FormKey == FormKey.Factory(target.ParentTopicFormKey) &&
                    parent.EditorID == target.ParentTopicEditorId,
                $"{key}: parent M.I.N.T. service topic changed.");
            var contexts = new FormLink<IDialogResponsesGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IDialogResponses, IDialogResponsesGetter>(state.LinkCache)
                .ToArray();
            var winner = contexts[0];
            var vmadScripts = winner.Record.VirtualMachineAdapter?.Scripts.Select(script => script.Name).ToArray()
                ?? [];
            var sourceVmad = winner.Record.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: pinned horse-purchase VMAD is missing.");
            var sourceScript = sourceVmad.Scripts.Single(script => script.Name == target.Script);
            var sourceProperties = sourceScript.Properties.OfType<IScriptObjectPropertyGetter>().ToArray();
            Require(winner.ModKey == key.ModKey && string.IsNullOrEmpty(winner.Record.EditorID) &&
                    winner.Record.Conditions.Count == target.ConditionCount &&
                    vmadScripts.SequenceEqual(new[] { target.Script }) &&
                    Convert.ToInt32(sourceVmad.Version) == target.VmadVersion &&
                    Convert.ToInt32(sourceVmad.ObjectFormat) == target.VmadObjectFormat &&
                    sourceScript.Properties.Count == target.VmadProperties.Count &&
                    sourceProperties.Length == target.VmadProperties.Count,
                $"{key}: pinned M.I.N.T. service INFO identity changed.");
            foreach (var propertyTarget in target.VmadProperties)
            {
                var sourceProperty = sourceProperties.SingleOrDefault(property => property.Name == propertyTarget.Name);
                Require(sourceProperty is not null &&
                        sourceProperty.Object.FormKey == FormKey.Factory(propertyTarget.FormKey) &&
                        RawVmadAlias(sourceProperty.Alias) == propertyTarget.Alias,
                    $"{key}: pinned {target.Script}.{propertyTarget.Name} binding changed.");
            }
            var sourceCurrencyProperty = sourceProperties.Single(property =>
                property.Name == target.VmadCurrencyProperty);
            Require(sourceCurrencyProperty.Object.FormKey == FormKey.Factory(target.SourceCurrency),
                $"{key}: pinned horse payment VMAD does not debit the reviewed source currency.");
            Require(target.ConditionIndex >= 0 && target.ConditionIndex < winner.Record.Conditions.Count,
                $"{key}: backend condition index is out of range.");
            var sourceCondition = winner.Record.Conditions[target.ConditionIndex];
            Require(sourceCondition is IConditionGlobalGetter sourceGlobal &&
                    sourceGlobal.CompareOperator == CompareOperator.GreaterThanOrEqualTo &&
                    sourceGlobal.ComparisonValue.FormKey == FormKey.Factory(target.ComparisonGlobal) &&
                    sourceGlobal.Data is IGetItemCountConditionDataGetter sourceCount &&
                    sourceCount.ItemOrList.Link.FormKey == FormKey.Factory(target.SourceCurrency) &&
                    sourceCount.RunOnType == Condition.RunOnType.Reference &&
                    sourceCount.Reference.FormKey == PlayerRef,
                $"{key}: pinned M.I.N.T. global-backed GetItemCount condition changed.");

            var patch = winner.GetOrAddAsOverride(state.PatchMod);
            var condition = (ConditionGlobal)patch.Conditions[target.ConditionIndex];
            var count = (GetItemCountConditionData)condition.Data!;
            count.ItemOrList.Link.SetTo(FormKey.Factory(target.BackendCurrency));
            var patchedVmad = patch.VirtualMachineAdapter
                ?? throw new InvalidOperationException($"{key}: copied horse-purchase VMAD is missing.");
            var patchedScript = patchedVmad.Scripts.Single(script => script.Name == target.Script);
            var patchedCurrencyProperty = patchedScript.Properties.OfType<ScriptObjectProperty>()
                .Single(property => property.Name == target.VmadCurrencyProperty);
            patchedCurrencyProperty.Object.SetTo(FormKey.Factory(target.BackendCurrency));
            ClearCompression(patch);
            Console.WriteLine($"Retargeted M.I.N.T. service INFO {key} budget check and {target.Script}.{target.VmadCurrencyProperty} debit from {target.SourceCurrency} to backend {target.BackendCurrency}; preserved comparison global, five other VMAD bindings, and fragments.");
        }
    }

    private static void ValidateDialogParentScopes(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        IReadOnlyList<MintExchangeInfoPolicy> disabled,
        IReadOnlyList<MintBackendConditionPolicy> backend)
    {
        var expected = disabled
            .Select(target => (parent: FormKey.Factory(target.ParentTopicFormKey),
                editorId: target.ParentTopicEditorId, child: FormKey.Factory(target.FormKey)))
            .Concat(backend.Select(target => (parent: FormKey.Factory(target.ParentTopicFormKey),
                editorId: target.ParentTopicEditorId, child: FormKey.Factory(target.FormKey))))
            .GroupBy(target => (target.parent, target.editorId))
            .ToArray();
        Require(expected.Length == 20, $"Expected twenty policy DIAL parents, got {expected.Length}.");
        var actualParents = state.PatchMod.DialogTopics.ToArray();
        Require(actualParents.Length == expected.Length &&
                actualParents.Select(parent => parent.FormKey).ToHashSet()
                    .SetEquals(expected.Select(group => group.Key.parent)),
            "Generated parent DIAL FormKey set differs from the exact INFO policy.");

        foreach (var group in expected)
        {
            var sourceMod = state.LoadOrder.ListedOrder.Single(listing =>
                    listing.ModKey == group.Key.parent.ModKey).Mod
                ?? throw new InvalidOperationException($"{group.Key.parent.ModKey}: DIAL source is not loaded.");
            var source = sourceMod.DialogTopics.Single(parent => parent.FormKey == group.Key.parent);
            var actual = actualParents.Single(parent => parent.FormKey == group.Key.parent);
            Require(source.EditorID == group.Key.editorId && actual.EditorID == source.EditorID &&
                    actual.FormVersion == source.FormVersion &&
                    actual.MajorRecordFlagsRaw == source.MajorRecordFlagsRaw &&
                    actual.Version2 == source.Version2 && actual.VersionControl == source.VersionControl &&
                    actual.Name?.String == source.Name?.String && actual.Priority == source.Priority &&
                    actual.Quest.FormKey == source.Quest.FormKey && actual.Branch.FormKey == source.Branch.FormKey &&
                    actual.Category == source.Category && actual.Subtype == source.Subtype &&
                    actual.SubtypeName == source.SubtypeName && actual.Timestamp == source.Timestamp &&
                    actual.TopicFlags == source.TopicFlags && actual.Unknown == source.Unknown,
                $"{group.Key.parent}: generated DIAL metadata differs from its immutable source.");
            var expectedChildren = group.Select(target => target.child).ToHashSet();
            var actualChildren = actual.Responses.Select(response => response.FormKey).ToHashSet();
            Require(actual.Responses.Count == expectedChildren.Count && actualChildren.SetEquals(expectedChildren),
                $"{group.Key.parent}: parent DIAL contains a missing, duplicate, or sibling INFO override.");
        }
    }

    private static void PatchEceSeptimQuest(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        StalePropertyTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IQuestGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
            .ToArray();
        var winner = contexts.Single(context => context.ModKey == Ece);
        Require(winner.ModKey == Ece,
            $"{key}: expected ECE septim quest winner, found {winner.ModKey}.");
        Require(winner.Record.EditorID == target.EditorId,
            $"{key}: ECE septim quest EditorID is {winner.Record.EditorID}, expected {target.EditorId}.");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        var alias = patch.VirtualMachineAdapter?.Aliases.Single()
            ?? throw new InvalidOperationException($"{key}: ECE septim alias VMAD is missing.");
        foreach (var qualified in target.StaleProperties)
        {
            var separator = qualified.LastIndexOf('.');
            Require(separator > 0 && separator < qualified.Length - 1,
                $"Malformed stale-property policy: {qualified}.");
            var scriptName = qualified[..separator];
            var propertyName = qualified[(separator + 1)..];
            var script = alias.Scripts.Single(candidate => candidate.Name == scriptName);
            var stale = script.Properties.Single(candidate => candidate.Name == propertyName);
            script.Properties.Remove(stale);
            Console.WriteLine($"Removed stale ECE VMAD property {scriptName}.{propertyName}.");
        }
        ClearCompression(patch);
    }

    private readonly record struct WeightedAmount(short Amount, int Weight);
    private readonly record struct ItemOutcome(FormKey Form, short Count);

    private static void PatchRegionalPurseGraph(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        RegionalPurseGraphPolicy graph,
        DenominationPolicy denominations,
        IReadOnlyDictionary<string, IReadOnlyDictionary<string, FormKey>> denominationForms)
    {
        var nextOwnedId = ParseOwnedId(graph.OwnedFormIdBase);
        var graphStart = nextOwnedId;
        FormKey Allocate(string description)
        {
            // A00-A15 are the frozen physical silver/gold tier records for the
            // eleven non-modern designs. Keep their save/runtime identities
            // stable and continue the purse DAG immediately after them.
            if (nextOwnedId == 0xA00) nextOwnedId = 0xA16;
            Require(nextOwnedId <= 0xFFF,
                $"Regional purse graph exhausted ESL FormIDs while allocating {description}.");
            return new FormKey(state.PatchMod.ModKey, nextOwnedId++);
        }

        static int GreatestCommonDivisor(int left, int right)
        {
            left = Math.Abs(left);
            right = Math.Abs(right);
            while (right != 0) (left, right) = (right, left % right);
            return left;
        }

        static IReadOnlyList<WeightedAmount> WeightedOptions(RegionalChangeListPolicy change)
        {
            var raw = new Dictionary<short, int> { [0] = checked(change.ChanceNonePercent * change.Counts.Count) };
            foreach (var amount in change.Counts)
            {
                raw[amount] = raw.GetValueOrDefault(amount) + (100 - change.ChanceNonePercent);
            }
            var divisor = raw.Values.Aggregate(GreatestCommonDivisor);
            return raw.Where(pair => pair.Value > 0).OrderBy(pair => pair.Key)
                .Select(pair => new WeightedAmount(pair.Key, pair.Value / divisor)).ToArray();
        }

        foreach (var familyPolicy in graph.Families)
        {
            var family = denominations.TieredFamilies.Single(item => item.Id == familyPolicy.FamilyId);
            var forms = denominationForms[family.Id];
            var sourceModKey = ModKey.FromNameAndExtension(familyPolicy.SourcePlugin);
            var primaryCoin = FormKey.Factory(familyPolicy.PrimaryCoinFormKey);
            Require(primaryCoin == FormKey.Factory(family.PrimarySource.FormKey),
                $"{family.Id}: purse primary coin differs from the denomination catalog.");

            RegionalChangeListPolicy ValidateChange(RegionalChangeListPolicy change)
            {
                var key = FormKey.Factory(change.FormKey);
                var context = new FormLink<ILeveledItemGetter>(key)
                    .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ILeveledItem, ILeveledItemGetter>(state.LinkCache)
                    .Single(item => item.ModKey == sourceModKey);
                var source = context.Record;
                var expectedFlags = (LeveledItem.Flag)0;
                if (change.CalculateFromAllLevelsLessThanOrEqualPlayer)
                    expectedFlags |= LeveledItem.Flag.CalculateFromAllLevelsLessThanOrEqualPlayer;
                if (change.CalculateForEachItemInCount)
                    expectedFlags |= LeveledItem.Flag.CalculateForEachItemInCount;
                var entries = source.Entries
                    ?? throw new InvalidOperationException($"{key}: regional change-list entries are null.");
                Require(source.EditorID == change.EditorId && source.Flags == expectedFlags && source.Global.IsNull &&
                        Math.Abs(((double)source.ChanceNone * 100.0) - change.ChanceNonePercent) < 0.0001 &&
                        entries.Count == change.Counts.Count &&
                        entries.All(entry => entry.Data?.Level == 1 &&
                            entry.Data.Reference.FormKey == FormKey.Factory(change.SourceCoinFormKey)) &&
                        entries.Select(entry => entry.Data!.Count).SequenceEqual(change.Counts),
                    $"{key}: pinned regional change-list distribution changed.");
                return change;
            }

            var primaryChange = ValidateChange(familyPolicy.PrimaryChange);
            var secondaryChange = ValidateChange(familyPolicy.SecondaryChange);
            Require(primaryChange.CalculateForEachItemInCount && secondaryChange.CalculateForEachItemInCount,
                $"{family.Id}: purse probability graph requires per-item rolls from both source change lists.");
            var primaryOptions = WeightedOptions(primaryChange);
            var secondaryOptions = WeightedOptions(secondaryChange);

            var terminalCache = new Dictionary<int, ItemOutcome>();
            var secondaryCache = new Dictionary<int, FormKey>();
            var primaryCache = new Dictionary<(int rolls, int total), FormKey>();

            ItemOutcome CreateVectorOutcome(int amount, bool singleBreak, string label)
            {
                var vector = DecomposeSeptims(amount, singleBreak);
                var parts = new[]
                {
                    (form: forms["copper"], count: vector.Copper),
                    (form: forms["silver"], count: vector.Silver),
                    (form: forms["gold"], count: vector.Gold),
                }.Where(item => item.count > 0).ToArray();
                Require(parts.Length > 0 && ValueOf(vector) == amount,
                    $"{family.Id}: purse terminal {amount} failed value conservation.");
                if (parts.Length == 1) return new ItemOutcome(parts[0].form, parts[0].count);
                var key = Allocate($"{family.Id} {label} {amount}");
                CreateUseAllPurseList(state, key,
                    $"Ensrick_RP_{family.Id}_{amount}_{label}", vector, forms);
                return new ItemOutcome(key, 1);
            }

            ItemOutcome Terminal(int amount)
            {
                if (terminalCache.TryGetValue(amount, out var cached)) return cached;
                var canonical = CreateVectorOutcome(amount, false, "Canonical");
                var brokenCounts = DecomposeSeptims(amount, true);
                if (brokenCounts == DecomposeSeptims(amount, false))
                {
                    terminalCache.Add(amount, canonical);
                    return canonical;
                }
                var broken = CreateVectorOutcome(amount, true, "SingleBreak");
                var selectorKey = Allocate($"{family.Id} terminal selector {amount}");
                var selector = NewLeveledList(selectorKey,
                    $"Ensrick_RP_{family.Id}_{amount}_80_20", 0);
                for (var choice = 0; choice < 5; choice++)
                {
                    var outcome = choice < 4 ? canonical : broken;
                    AddLeveledEntry(selector, outcome.Form, outcome.Count);
                }
                state.PatchMod.LeveledItems.Add(selector);
                var result = new ItemOutcome(selectorKey, 1);
                terminalCache.Add(amount, result);
                return result;
            }

            FormKey SecondaryState(int total)
            {
                if (secondaryCache.TryGetValue(total, out var cached)) return cached;
                var key = Allocate($"{family.Id} secondary state {total}");
                secondaryCache.Add(total, key);
                var selector = NewLeveledList(key, $"Ensrick_RP_{family.Id}_B_{total}", 0);
                foreach (var option in secondaryOptions)
                {
                    var outcome = Terminal(total + option.Amount);
                    for (var weight = 0; weight < option.Weight; weight++)
                        AddLeveledEntry(selector, outcome.Form, outcome.Count);
                }
                state.PatchMod.LeveledItems.Add(selector);
                return key;
            }

            FormKey PrimaryState(int rolls, int total)
            {
                if (rolls == 0) return SecondaryState(total);
                var cacheKey = (rolls, total);
                if (primaryCache.TryGetValue(cacheKey, out var cached)) return cached;
                var key = Allocate($"{family.Id} primary state {rolls}/{total}");
                primaryCache.Add(cacheKey, key);
                var selector = NewLeveledList(key, $"Ensrick_RP_{family.Id}_A{rolls}_{total}", 0);
                foreach (var option in primaryOptions)
                {
                    var next = PrimaryState(rolls - 1, total + option.Amount);
                    for (var weight = 0; weight < option.Weight; weight++)
                        AddLeveledEntry(selector, next, 1);
                }
                state.PatchMod.LeveledItems.Add(selector);
                return key;
            }

            foreach (var purse in familyPolicy.Purses)
            {
                Require(purse.SecondaryChangeRolls == 1,
                    $"{family.Id}/{purse.EditorId}: only the pinned one secondary roll is supported.");
                var key = FormKey.Factory(purse.FormKey);
                var context = new FormLink<ILeveledItemGetter>(key)
                    .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ILeveledItem, ILeveledItemGetter>(state.LinkCache)
                    .Single(item => item.ModKey == sourceModKey);
                var source = context.Record;
                var entries = source.Entries
                    ?? throw new InvalidOperationException($"{key}: regional purse entries are null.");
                Require(source.EditorID == purse.EditorId && source.Flags == LeveledItem.Flag.UseAll &&
                        (double)source.ChanceNone == 0.0 && source.Global.IsNull && entries.Count == 3 &&
                        entries[0].Data is { Level: 1 } direct && direct.Count == purse.BaseCoinCount &&
                            direct.Reference.FormKey == primaryCoin &&
                        entries[1].Data is { Level: 1 } first && first.Count == purse.PrimaryChangeRolls &&
                            first.Reference.FormKey == FormKey.Factory(primaryChange.FormKey) &&
                        entries[2].Data is { Level: 1 } second && second.Count == purse.SecondaryChangeRolls &&
                            second.Reference.FormKey == FormKey.Factory(secondaryChange.FormKey),
                    $"{key}: pinned regional purse composition changed.");
                var root = PrimaryState(purse.PrimaryChangeRolls, purse.BaseCoinCount);
                var patch = context.GetOrAddAsOverride(state.PatchMod);
                patch.Flags = LeveledItem.Flag.UseAll;
                patch.ChanceNone = new Percent(0.0);
                patch.Global.SetTo(FormKey.Null);
                patch.Entries ??= [];
                patch.Entries.Clear();
                AddLeveledEntry(patch, root, 1);
                ClearCompression(patch);
                Console.WriteLine($"Rebuilt {family.Id} purse {key} as an exact source-probability DAG with whole-purse 80/20 denomination output.");
            }
        }
        Require(nextOwnedId == 0xF40,
            $"Regional purse graph ended at {nextOwnedId - 1:X6}; expected 1434 records across 000990-0009FF and 000A16-000F3F.");
    }

    private static void PatchDrakrPile(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        ScriptPropertyTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IActivatorGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IActivator, IActivatorGetter>(state.LinkCache)
            .ToArray();
        var source = contexts.Single(context => context.ModKey == Coin);
        Require(source.Record.EditorID == target.EditorId,
            $"{key}: Drakr pile EditorID is {source.Record.EditorID}, expected {target.EditorId}.");
        var patch = source.GetOrAddAsOverride(state.PatchMod);
        var script = patch.VirtualMachineAdapter?.Scripts.Single(candidate => candidate.Name == target.Script)
            ?? throw new InvalidOperationException($"{key}: Drakr pile script {target.Script} is missing.");
        var property = script.Properties.OfType<ScriptObjectProperty>()
            .Single(candidate => candidate.Name == target.Property);
        var expectedSource = FormKey.Factory(target.SourceFormKey);
        var expectedTarget = FormKey.Factory(target.TargetFormKey);
        Require(property.Object.FormKey == expectedSource,
            $"{key}: {target.Script}.{target.Property} is {property.Object.FormKey}, expected {expectedSource}.");
        property.Object.SetTo(expectedTarget);
        ClearCompression(patch);
        Console.WriteLine($"Retargeted Drakr pile pickup {key} from {expectedSource} to canonical tender {expectedTarget}.");
    }

    private static void CreateAncientExchangeRecipes(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        string workbenchFormKey,
        IReadOnlyList<ExchangeRecipePolicy> targets)
    {
        var workbench = FormKey.Factory(workbenchFormKey);
        foreach (var target in targets)
        {
            var formId = uint.Parse(target.FormId,
                System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture);
            var input = FormKey.Factory(target.InputFormKey);
            var output = FormKey.Factory(target.OutputFormKey);
            var recipe = new ConstructibleObject(new FormKey(state.PatchMod.ModKey, formId),
                SkyrimRelease.SkyrimSE)
            {
                EditorID = target.EditorId,
                Items =
                [
                    new ContainerEntry
                    {
                        Item = new ContainerItem
                        {
                            Count = target.InputCount,
                        },
                    },
                ],
                Conditions =
                [
                    new ConditionFloat
                    {
                        CompareOperator = CompareOperator.GreaterThanOrEqualTo,
                        ComparisonValue = target.InputCount,
                        Data = new GetItemCountConditionData(),
                    },
                ],
                CreatedObjectCount = target.OutputCount,
            };
            recipe.Items[0].Item.Item.SetTo(input);
            ((GetItemCountConditionData)recipe.Conditions[0].Data!).ItemOrList.Link.SetTo(input);
            recipe.CreatedObject.SetTo(output);
            recipe.WorkbenchKeyword.SetTo(workbench);
            state.PatchMod.ConstructibleObjects.Add(recipe);
            Console.WriteLine($"Created one-way exchange {recipe.FormKey} {target.EditorId}: " +
                $"{target.InputCount}x {input} -> {target.OutputCount}x {output} ({target.Purpose}).");
        }
    }

    private static void CreateRuntimeQuest(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        QuestPolicy policy)
    {
        var questKey = new FormKey(state.PatchMod.ModKey, RuntimeQuestId);
        var quest = new Quest(questKey, SkyrimRelease.SkyrimSE)
        {
            EditorID = policy.EditorId,
            Flags = Quest.Flag.StartGameEnabled,
            Priority = 0,
            QuestFormVersion = 65,
            Type = Quest.TypeEnum.None,
            NextAliasID = 1,
            VirtualMachineAdapter = new QuestAdapter(),
        };

        var alias = new QuestAlias
        {
            ID = policy.AliasId,
            Type = QuestAlias.TypeEnum.Reference,
            Name = policy.AliasName,
            Flags = 0,
        };
        alias.ForcedReference.SetTo(PlayerRef);
        quest.Aliases.Add(alias);

        var aliasAdapter = new QuestFragmentAlias();
        aliasAdapter.Property.Object.SetTo(questKey);
        aliasAdapter.Property.Alias = checked((short)policy.AliasId);
        var script = new ScriptEntry { Name = policy.Script };

        var coinManager = new ScriptObjectProperty { Name = "CoinManager" };
        coinManager.Object.SetTo(CoinManagerQuest);
        script.Properties.Add(coinManager);

        var mintConvert = new ScriptObjectProperty { Name = "MintAutoConvert" };
        mintConvert.Object.SetTo(MintConvertGlobal);
        script.Properties.Add(mintConvert);

        var mintFramework = new ScriptObjectProperty { Name = "MintFramework" };
        mintFramework.Object.SetTo(MintFrameworkQuest);
        script.Properties.Add(mintFramework);

        aliasAdapter.Scripts.Add(script);
        quest.VirtualMachineAdapter.Aliases.Add(aliasAdapter);
        state.PatchMod.Quests.Add(quest);
    }

    public static Policy ReadPolicy(string path) =>
        JsonSerializer.Deserialize<Policy>(File.ReadAllText(path))
        ?? throw new InvalidOperationException($"Could not read {path}.");

    public static void ValidatePolicy(Policy policy)
    {
        Require(policy.SchemaVersion == 1, "policy.json schemaVersion must be 1.");
        Require(policy.OutputPluginName == OutputPlugin, "policy outputPlugin mismatch.");
        Require(policy.RuntimeReasonCounters.SequenceEqual(new[]
                {
                    "player-task-interface-unavailable", "player-reconcile-failed",
                    "source-invalid-count", "source-ambiguous-dual-accounting", "source-empty",
                    "source-already-broken", "source-already-canonical", "source-value-out-of-range",
                    "source-apply-failed", "source-converted-container", "source-converted-actor",
                    "source-reference-safety-rejected",
                    "source-actor-safety-rejected", "source-container-safety-rejected",
                }),
            "Runtime telemetry reason-counter contract changed.");
        var provider = policy.ExchangeWorkbenchProvider;
        Require(ModKey.FromNameAndExtension(provider.Plugin) == Exchange &&
                FormKey.Factory(provider.FormKey) == FormKey.Factory("000801:SL99Exchanger.esp") &&
                provider.EditorId == "SL99CraftingExchangeBank" &&
                provider.Sha256 == "C9342F1B669A3AE1F4A51E0CA8FBD9CDA3AEC915D36DC4CC9A0798B09E5B2446" &&
                provider.Bytes == 159056 && provider.Records == 470 && provider.RequiresSmallFlag,
            "Exchange workbench provider pin changed; review the exact compact ECE-bundled SL99Exchanger.esp.");
        Require(policy.Quest.FormId.Equals(RuntimeQuestId.ToString("X6"), StringComparison.OrdinalIgnoreCase),
            "Runtime quest form ID must be 000800.");
        Require(policy.Quest.EditorId == RuntimeQuestEditorId, "Runtime quest EditorID mismatch.");
        Require(policy.Quest.Script == RuntimeScriptName, "Runtime script name mismatch.");
        Require(policy.Overrides.CoinPurses.Count == 3, "Policy must contain exactly three coin purses.");
        Require(policy.Overrides.CoinPurses.All(item => item.Counts.Count == 16 &&
                item.Counts.Distinct().Count() == 16 && item.Counts.All(count => count > 0)),
            "Each purse must contain exactly 16 unique positive counts.");
        var expectedPurseForms = new[]
        {
            (lvli: "0D790B:Skyrim.esm", flora: "0D790C:Skyrim.esm", floraEditorId: "CoinPurseSmall", canonical: "000900", broken: "000910", selector: "000920"),
            (lvli: "0D8E7D:Skyrim.esm", flora: "0D8E7F:Skyrim.esm", floraEditorId: "CoinPurseMedium", canonical: "000930", broken: "000940", selector: "000950"),
            (lvli: "0D8E7E:Skyrim.esm", flora: "0D8E80:Skyrim.esm", floraEditorId: "CoinPurseLarge", canonical: "000960", broken: "000970", selector: "000980"),
        };
        Require(policy.Overrides.CoinPurses.Zip(expectedPurseForms).All(pair =>
                FormKey.Factory(pair.First.FormKey) == FormKey.Factory(pair.Second.lvli) &&
                FormKey.Factory(pair.First.FloraFormKey) == FormKey.Factory(pair.Second.flora) &&
                pair.First.FloraEditorId == pair.Second.floraEditorId &&
                pair.First.CanonicalFormIdBase == pair.Second.canonical &&
                pair.First.BreakFormIdBase == pair.Second.broken &&
                pair.First.SelectorFormIdBase == pair.Second.selector),
            "Purse FLOR/LVLI relationship or owned adapter ranges changed.");

        var denomination = policy.Denominations;
        Require(denomination.CanonicalPercent == 80 && denomination.VariantPercent == 20 &&
                denomination.CanonicalPercent + denomination.VariantPercent == 100,
            "Purse distribution must be exactly 80% canonical / 20% single-break.");
        var families = denomination.TieredFamilies;
        var expectedFamilyIds = new[]
        {
            "septim", "mede", "ulfric", "dram", "oshka", "ohzer", "varken",
            "drakr_dragon", "drakr_moth", "drakr_owl", "drakr_whale",
            "gibber_dementia", "gibber_mania", "mala", "mallari", "nchuark",
            "sancar", "bruma_ayleid_mala",
        };
        Require(families.Count == expectedFamilyIds.Length &&
                families.Select(item => item.Id).SequenceEqual(expectedFamilyIds) &&
                families.All(item => item.Enabled),
            "Tiered currency policy must contain the exact eighteen enabled installed designs.");
        Require(families.SelectMany(item => item.Tiers.Values)
                .Count(item => item.FormId is not null) == 34 &&
                families.SelectMany(item => item.Tiers.Values)
                    .Where(item => item.FormId is not null)
                    .Select(item => ParseOwnedId(item.FormId!)).Distinct().Count() == 34,
            "Expected exactly thirty-four unique owned silver/gold denomination FormIDs.");
        Require(families.Take(7).Skip(1)
                .SelectMany(item => new[] { item.Tiers["silver"].FormId, item.Tiers["gold"].FormId })
                .SequenceEqual(new[]
                {
                    "000820", "000821", "000822", "000823", "000824", "000825",
                    "000826", "000827", "000828", "000829", "00082A", "00082B",
                }),
            "Existing modern denomination FormIDs changed.");
        Require(families.Skip(7)
                .SelectMany(item => new[] { item.Tiers["silver"].FormId, item.Tiers["gold"].FormId })
                .Select(item => ParseOwnedId(item!))
                .SequenceEqual(Enumerable.Range(0xA00, 0x16).Select(item => (uint)item)),
            "New ancient/Sancar/Bruma denomination FormIDs must occupy A00-A15 exactly.");
        var expectedPrimaryForms = new[]
        {
            "000B6D:exchangeCurrency_enhanced.esp", "DE5021:Update.esm",
            "DE5024:Update.esm", "DE5029:Update.esm",
            "000871:exchangeCurrency_patch_COIN.esp", "00086F:exchangeCurrency_patch_COIN.esp",
            "000870:exchangeCurrency_patch_COIN.esp", "DE5012:Update.esm",
            "DE5013:Update.esm", "DE5014:Update.esm", "DE5015:Update.esm",
            "DE5017:Update.esm", "DE5018:Update.esm", "DE5019:Update.esm",
            "DE5020:Update.esm", "DE5022:Update.esm", "DE5023:Update.esm",
            "6028DC:BSAssets.esm",
        }.Select(value => FormKey.Factory(value));
        Require(families.Select(item => FormKey.Factory(item.PrimarySource.FormKey))
                .SequenceEqual(expectedPrimaryForms),
            "Installed primary currency-design catalog changed.");
        Require(families.All(family =>
                family.Tiers.Keys.ToHashSet(StringComparer.Ordinal)
                    .SetEquals(new[] { "copper", "silver", "gold" }) &&
                family.Tiers["copper"].Value == 1 && family.Tiers["silver"].Value == 10 &&
                family.Tiers["gold"].Value == 100 &&
                family.Tiers.All(pair => pair.Value.Name ==
                    $"{char.ToUpperInvariant(pair.Key[0])}{pair.Key[1..]} {family.DisplayLabel}") &&
                family.Tiers.Select(pair => pair.Value.Model)
                    .Distinct(StringComparer.OrdinalIgnoreCase).Count() == 3),
            "Every installed currency design must have distinct named copper/silver/gold models worth 1/10/100.");
        Require(families.Sum(item => item.SourceAliases.Count) == 1 &&
                families.Single(item => item.Id == "gibber_mania").SourceAliases.Single() is var maniaAlias &&
                FormKey.Factory(maniaAlias.FormKey) == FormKey.Factory("DE5027:Update.esm") &&
                maniaAlias.SourcePlugin == Mint.FileName.String &&
                maniaAlias.NormalizesToTier == "copper",
            "Unified M.I.N.T. Gibber must remain the sole copper input alias for Mania Gibber.");
        var sancar = families.Single(item => item.Id == "sancar");
        Require(sancar.OwnedRouteKeywordFormId == "000803" &&
                sancar.OwnedRouteKeywordEditorId == "Ensrick_IsSancarMoney" && sancar.Perk is null,
            "Sancar owned route keyword changed.");
        Require(families.Where(item => item.Id.StartsWith("drakr_", StringComparison.Ordinal))
                .All(item => FormKey.Factory(item.Perk!) ==
                    FormKey.Factory("00082C:exchangeCurrency_patch_COIN.esp")),
            "All four Drakr designs must retain the reviewed regional-price perk.");

        var neutralized = policy.Overrides.EcePlayerCurrencyQuests;
        Require(neutralized.Count == 2 &&
                FormKey.Factory(neutralized[0].FormKey) == FormKey.Factory("000B63:exchangeCurrency_enhanced.esp") &&
                neutralized[0].SourcePlugin == Ece.FileName.String && neutralized[0].AliasId == 0 &&
                neutralized[0].TransactionScripts.SequenceEqual(new[] { "EC_septimsFunctions", "EC_septimsScript" }) &&
                FormKey.Factory(neutralized[1].FormKey) == FormKey.Factory("000827:exchangeCurrency_patch_COIN.esp") &&
                neutralized[1].SourcePlugin == CoinPatch.FileName.String && neutralized[1].AliasId == 0 &&
                neutralized[1].TransactionScripts.SequenceEqual(new[]
                {
                    "EC_altCurrencyFunctions", "EC_ulfricsScript", "EC_dramsScript",
                    "EC_medesScript", "EC_drakrsScript", "EC_oshkasScript",
                }),
            "ECE player currency quest neutralization set changed.");
        var mintCostOnly = policy.Overrides.MintCostOnlyQuests;
        Require(mintCostOnly.Count == 2 &&
                FormKey.Factory(mintCostOnly[0].FormKey) == FormKey.Factory("00000D:MorrowindUsesDrams.esp") &&
                mintCostOnly[0].EditorId == "DES_DramMorrowindServicesQuest" &&
                mintCostOnly[0].OriginalPlugin == Dram.FileName.String &&
                mintCostOnly[0].WinningPlugin == EceMintDram.FileName.String &&
                mintCostOnly[0].QuestScript == "DES_DramCurrencySwapper" &&
                mintCostOnly[0].PlayerAliasId == 1 &&
                mintCostOnly[0].PlayerAliasScript == "DES_DramCurrencySwapperAlias" &&
                mintCostOnly[0].RemovedAliasScripts.ToHashSet(StringComparer.Ordinal).SetEquals(new[]
                    { "DES_CurrencyFramework_RegisterEvents", "DES_CurrencyFramework_GoldConverter" }) &&
                FormKey.Factory(mintCostOnly[1].FormKey) == FormKey.Factory("000002:WindhelmUsesUlfrics.esp") &&
                mintCostOnly[1].EditorId == "DES_UlfricWindhelmServicesQuest" &&
                mintCostOnly[1].OriginalPlugin == Windhelm.FileName.String &&
                mintCostOnly[1].WinningPlugin == EceMintUlfric.FileName.String &&
                mintCostOnly[1].QuestScript == "DES_UlfricCurrencySwapper" &&
                mintCostOnly[1].PlayerAliasId == 4 &&
                mintCostOnly[1].PlayerAliasScript == "DES_UlfricCurrencySwapperAlias" &&
                mintCostOnly[1].RemovedAliasScripts.ToHashSet(StringComparer.Ordinal).SetEquals(new[]
                    { "DES_CurrencyFramework_RegisterEvents", "DES_CurrencyFramework_GoldConverter" }),
            "M.I.N.T. cost-only quest binding set changed.");
        Require(mintCostOnly[0].CostPropertyNames.Count == 12 && mintCostOnly[1].CostPropertyNames.Count == 19,
            "M.I.N.T. cost-only quest property pins changed.");

        Require(FormKey.Factory(policy.Overrides.MintMadranQuest.FormKey) ==
                FormKey.Factory("000002:WindhelmUsesUlfrics.esp") &&
                policy.Overrides.MintMadranQuest.EditorId == "DES_UlfricWindhelmServicesQuest" &&
                policy.Overrides.MintMadranQuest.AliasId == 5 &&
                policy.Overrides.MintMadranQuest.TransactionScript == "DES_MadranSwapper" &&
                policy.Overrides.MintMadranQuest.StaleQuestProperties.SequenceEqual(new[]
                {
                    "Alias_Brunwulf",
                    "Alias_Nilsine",
                    "Alias_Oengul",
                    "Alias_Tova",
                    "Alias_Torsten",
                    "Alias_CaptainLonelyGale",
                    "Alias_Torbjorn",
                    "Alias_Jora",
                }),
            "Ma'dran transaction-script removal policy changed.");
        var disabledMintInfos = policy.Overrides.DisabledMintExchangeInfos;
        var expectedDisabledMintInfoKeys = new[]
        {
            "000017:MorrowindUsesDrams.esp", "000019:MorrowindUsesDrams.esp",
            "00001B:MorrowindUsesDrams.esp", "00001D:MorrowindUsesDrams.esp",
            "00001F:MorrowindUsesDrams.esp", "000025:MorrowindUsesDrams.esp",
            "000027:MorrowindUsesDrams.esp", "000029:MorrowindUsesDrams.esp",
            "00002B:MorrowindUsesDrams.esp", "000032:MorrowindUsesDrams.esp",
            "000034:MorrowindUsesDrams.esp", "000036:MorrowindUsesDrams.esp",
            "000038:MorrowindUsesDrams.esp", "00003A:MorrowindUsesDrams.esp",
            "000064:MorrowindUsesDrams.esp", "000065:MorrowindUsesDrams.esp",
            "000066:MorrowindUsesDrams.esp", "000007:MorrowindUsesDrams.esp",
            "000067:MorrowindUsesDrams.esp", "000068:MorrowindUsesDrams.esp",
            "000069:MorrowindUsesDrams.esp", "00006A:MorrowindUsesDrams.esp",
            "000009:MorrowindUsesDrams.esp", "000053:WindhelmUsesUlfrics.esp",
            "000054:WindhelmUsesUlfrics.esp", "000055:WindhelmUsesUlfrics.esp",
            "000056:WindhelmUsesUlfrics.esp", "000057:WindhelmUsesUlfrics.esp",
            "000058:WindhelmUsesUlfrics.esp", "000059:WindhelmUsesUlfrics.esp",
            "00005A:WindhelmUsesUlfrics.esp", "00005B:WindhelmUsesUlfrics.esp",
            "00001F:WindhelmUsesUlfrics.esp", "00005C:WindhelmUsesUlfrics.esp",
            "00005D:WindhelmUsesUlfrics.esp", "000093:WindhelmUsesUlfrics.esp",
            "000095:WindhelmUsesUlfrics.esp", "000092:WindhelmUsesUlfrics.esp",
        }.Select(value => FormKey.Factory(value)).ToArray();
        Require(disabledMintInfos.Count == 38 &&
                disabledMintInfos.Select(item => FormKey.Factory(item.FormKey))
                    .SequenceEqual(expectedDisabledMintInfoKeys) &&
                disabledMintInfos.Select(item => FormKey.Factory(item.FormKey)).Distinct().Count() == 38 &&
                disabledMintInfos.All(item =>
                    FormKey.Factory(item.ParentTopicFormKey).ModKey == FormKey.Factory(item.FormKey).ModKey &&
                    !string.IsNullOrWhiteSpace(item.ParentTopicEditorId) &&
                    item.ConditionCount is >= 2 and <= 5 &&
                    item.TransactionScripts.Count <= 1 &&
                    item.TransactionScripts.All(script => script.StartsWith("TIF__", StringComparison.Ordinal))),
            "Obsolete M.I.N.T. exchange/failure INFO disable set changed.");
        var backendInfos = policy.Overrides.MintBackendConditionInfos;
        var expectedHorseProperties = new (string name, FormKey formKey, int alias)[]
        {
            ("Gold001", FormKey.Factory("DE5024:Update.esm"), 65535),
            ("PlayerHorseFaction", FormKey.Factory("068D78:Skyrim.esm"), 65535),
            ("PlayersHorse", FormKey.Factory("068D73:Skyrim.esm"), 40),
            ("Alias_Horse", FormKey.Factory("068D73:Skyrim.esm"), 31),
            ("HorseCost", FormKey.Factory("0000C9:WindhelmUsesUlfrics.esp"), 65535),
            ("PlayerFaction", FormKey.Factory("000DB1:Skyrim.esm"), 65535),
        };
        Require(backendInfos.Count == 2 &&
                backendInfos.Select(item => FormKey.Factory(item.FormKey)).SequenceEqual(new[]
                {
                    FormKey.Factory("00000A:WindhelmUsesUlfrics.esp"),
                    FormKey.Factory("00000C:WindhelmUsesUlfrics.esp"),
                }) &&
                backendInfos.All(item =>
                    FormKey.Factory(item.ParentTopicFormKey) == FormKey.Factory("000006:WindhelmUsesUlfrics.esp") &&
                    item.ParentTopicEditorId == "DES_UlfricBuyHorseTopic" && item.ConditionIndex == 0 &&
                    FormKey.Factory(item.SourceCurrency) == FormKey.Factory("DE5024:Update.esm") &&
                    FormKey.Factory(item.BackendCurrency) == FormKey.Factory("00000F:Skyrim.esm") &&
                    FormKey.Factory(item.ComparisonGlobal) == FormKey.Factory("0000C9:WindhelmUsesUlfrics.esp") &&
                    item.ConditionCount == 2 && item.VmadVersion == 5 && item.VmadObjectFormat == 2 &&
                    item.VmadCurrencyProperty == "Gold001" && item.VmadProperties.Count == 6 &&
                    item.VmadProperties.Zip(expectedHorseProperties).All(pair =>
                        pair.First.Name == pair.Second.name &&
                        FormKey.Factory(pair.First.FormKey) == pair.Second.formKey &&
                        pair.First.Alias == pair.Second.alias)) &&
                backendInfos.Select(item => item.Script).SequenceEqual(new[]
                {
                    "TIF__0009841D", "TIF__00098422",
                }),
            "M.I.N.T. backend-aware horse-purchase condition/payment set changed.");
        var purseGraph = policy.Overrides.RegionalPurseGraph;
        var expectedPurseFamilies = new[]
        {
            "drakr_dragon", "nchuark", "mallari", "mala", "gibber_mania", "dram", "sancar", "ulfric",
        };
        Require(purseGraph.OwnedFormIdBase == "000990" && purseGraph.Families.Count == 8 &&
                purseGraph.Families.Select(item => item.FamilyId).SequenceEqual(expectedPurseFamilies) &&
                purseGraph.Families.SelectMany(item => item.Purses).Count() == 24,
            "Regional purse graph must cover the exact eight authored three-size families from owned FormID 000990.");
        var expectedPurseKeys = new[]
        {
            "000800:C.O.I.N.esp", "000801:C.O.I.N.esp", "000802:C.O.I.N.esp",
            "00080B:C.O.I.N.esp", "00080C:C.O.I.N.esp", "00080A:C.O.I.N.esp",
            "000937:C.O.I.N.esp", "000938:C.O.I.N.esp", "000939:C.O.I.N.esp",
            "000940:C.O.I.N.esp", "000941:C.O.I.N.esp", "000942:C.O.I.N.esp",
            "000C61:C.O.I.N.esp", "000C62:C.O.I.N.esp", "000C63:C.O.I.N.esp",
            "000F2B:M.I.N.T.esp", "000F2C:M.I.N.T.esp", "000F2D:M.I.N.T.esp",
            "000F2E:M.I.N.T.esp", "000F2F:M.I.N.T.esp", "000F30:M.I.N.T.esp",
            "000F31:M.I.N.T.esp", "000F32:M.I.N.T.esp", "000F33:M.I.N.T.esp",
        }.Select(value => FormKey.Factory(value));
        Require(purseGraph.Families.SelectMany(item => item.Purses)
                .Select(item => FormKey.Factory(item.FormKey)).SequenceEqual(expectedPurseKeys) &&
                purseGraph.Families.All(item => item.Purses.Select(purse => purse.PrimaryChangeRolls)
                    .SequenceEqual(new short[] { 1, 2, 3 }) &&
                    item.Purses.All(purse => purse.SecondaryChangeRolls == 1)) &&
                purseGraph.Families.Where(item => item.FamilyId != "dram")
                    .All(item => item.Purses.Select(purse => purse.BaseCoinCount)
                        .SequenceEqual(new short[] { 5, 10, 20 })) &&
                purseGraph.Families.Single(item => item.FamilyId == "dram").Purses
                    .Select(purse => purse.BaseCoinCount).SequenceEqual(new short[] { 15, 30, 60 }),
            "Regional purse roots/base amounts/roll counts changed.");
        var expectedChangeKeys = new[]
        {
            "000D66:C.O.I.N.esp", "000D67:C.O.I.N.esp", "000808:C.O.I.N.esp", "000809:C.O.I.N.esp",
            "000860:C.O.I.N.esp", "00093C:C.O.I.N.esp", "000943:C.O.I.N.esp", "000944:C.O.I.N.esp",
            "000C64:C.O.I.N.esp", "000C65:C.O.I.N.esp", "000F25:M.I.N.T.esp", "000F26:M.I.N.T.esp",
            "000F27:M.I.N.T.esp", "000F28:M.I.N.T.esp", "000F29:M.I.N.T.esp", "000F2A:M.I.N.T.esp",
        }.Select(value => FormKey.Factory(value));
        Require(purseGraph.Families.SelectMany(item => new[] { item.PrimaryChange, item.SecondaryChange })
                .Select(item => FormKey.Factory(item.FormKey)).SequenceEqual(expectedChangeKeys) &&
                purseGraph.Families.All(item => item.PrimaryChange.CalculateForEachItemInCount &&
                    item.SecondaryChange.CalculateForEachItemInCount && item.SecondaryChange.ChanceNonePercent == 75) &&
                purseGraph.Families.Where(item => item.FamilyId != "mallari")
                    .All(item => item.PrimaryChange.ChanceNonePercent == 10) &&
                purseGraph.Families.Single(item => item.FamilyId == "mallari").PrimaryChange.ChanceNonePercent == 75,
            "Regional purse source-change probability contract changed.");
        var purseCompanion = policy.Overrides.RegionalPurseCompanion;
        Require(purseCompanion.OutputPlugin == RegionalPursePlugin &&
                purseCompanion.TerminalFormIdBase == "000820" &&
                purseCompanion.Families.Select(item => item.FamilyId).SequenceEqual(new[]
                {
                    "mede", "oshka", "ohzer", "varken", "bruma_ayleid_mala",
                }) &&
                purseCompanion.Families.Select(item => item.FloraFormIdBase).SequenceEqual(new[]
                {
                    "000800", "000803", "000806", "000809", "00080C",
                }) &&
                purseCompanion.Families.Select(item => item.BudgetFormIdBase).SequenceEqual(new[]
                {
                    "000810", "000813", "000816", "000819", "00081C",
                }),
            "Regional purse companion identity/FormID allocation changed.");
        Require(FormKey.Factory(policy.Overrides.DrakrPile.FormKey) ==
                FormKey.Factory("0009C6:C.O.I.N.esp") &&
                policy.Overrides.DrakrPile.EditorId == "DES_PileofDrakr" &&
                policy.Overrides.DrakrPile.Script == "DLC2GoldPileScript" &&
                policy.Overrides.DrakrPile.Property == "Gold001" &&
                FormKey.Factory(policy.Overrides.DrakrPile.SourceFormKey) ==
                    FormKey.Factory("DE5012:Update.esm") &&
                FormKey.Factory(policy.Overrides.DrakrPile.TargetFormKey) ==
                    FormKey.Factory("DE5012:Update.esm"),
            "Drakr pile canonical-tender policy changed.");
        Require(FormKey.Factory(policy.Overrides.AncientExchangeWorkbench) ==
                FormKey.Factory("000801:SL99Exchanger.esp"),
            "Ancient exchange recipes must use Exchange Currency SE's money-exchange workbench.");
        var exchangeRecipes = policy.Overrides.AncientExchangeRecipes;
        Require(exchangeRecipes.Count == 9 &&
                exchangeRecipes.Select(item => item.FormId).SequenceEqual(new[]
                {
                    "000804", "000805", "000806",
                    "000808", "000809", "00080A", "00080B",
                    "00080C", "00080D",
                }) &&
                exchangeRecipes.Select(item => item.EditorId).Distinct().Count() == 9 &&
                exchangeRecipes.All(item => item.InputCount == 1 && item.OutputCount == 1 &&
                    item.Purpose == "tier-value-parity") &&
                exchangeRecipes.All(item =>
                    FormKey.Factory(item.OutputFormKey) == FormKey.Factory("00000F:Skyrim.esm")),
            "Ancient one-way exchange-recipe policy changed.");
        var expectedAncientRates = new Dictionary<FormKey, (int input, ushort output)>
        {
            [FormKey.Factory("DE5012:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5013:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5014:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5019:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5020:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5022:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5018:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5017:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5027:Update.esm")] = (1, 1),
        };
        Require(exchangeRecipes.All(item =>
                expectedAncientRates.GetValueOrDefault(FormKey.Factory(item.InputFormKey)) ==
                    (item.InputCount, item.OutputCount)) &&
                exchangeRecipes.Select(item => FormKey.Factory(item.InputFormKey)).ToHashSet()
                    .SetEquals(expectedAncientRates.Keys),
            "Ancient exchange recipes must preserve exact tier value parity.");
        Require(policy.DisabledRecipes.Count == 17, "Policy must contain exactly 17 disabled recipes.");
        Require(policy.DisabledRecipes.Select(item => FormKey.Factory(item.FormKey)).Distinct().Count() == 17,
            "Disabled-recipe FormKeys must be unique.");
        Require(policy.DisabledRecipes.All(item => FormKey.Factory(item.FormKey).ModKey == CoinPatch),
            "Every disabled recipe must originate in exchangeCurrency_patch_COIN.esp.");
        var expectedBankIds = new uint[]
        {
            0x82D, 0x82E, 0x82F, 0x830, 0x834, 0x835, 0x84B, 0x84C,
            0x84D, 0x84F, 0x853, 0x854, 0x873, 0x874, 0x875, 0x876,
        };
        Require(policy.DisabledModernBankRecipes.Count == 16 &&
                policy.DisabledModernBankRecipes.Select(item => FormKey.Factory(item.FormKey).ID)
                    .SequenceEqual(expectedBankIds) &&
                policy.DisabledModernBankRecipes.All(item => FormKey.Factory(item.FormKey).ModKey == CoinPatch),
            "Modern non-parity bank-recipe disable set changed.");
        Require(policy.DisabledRecipes.Concat(policy.DisabledModernBankRecipes)
                .Select(item => FormKey.Factory(item.FormKey)).Distinct().Count() == 33,
            "All disabled legacy COBJ FormKeys must be unique.");
    }

    public static void ValidateExchangeWorkbenchProvider(
        ISkyrimModGetter provider,
        string providerPath,
        ExchangeWorkbenchProviderPolicy policy)
    {
        var expectedKey = ModKey.FromNameAndExtension(policy.Plugin);
        Require(provider.ModKey == expectedKey,
            $"Exchange workbench provider is {provider.ModKey}, expected {expectedKey}.");
        Require(!policy.RequiresSmallFlag ||
                provider.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small),
            $"{policy.Plugin}: the winning provider is not the required compact ESL-flagged build.");
        var records = provider.EnumerateMajorRecords().ToArray();
        Require(records.Length == policy.Records,
            $"{policy.Plugin}: winning provider has {records.Length} records, expected {policy.Records}.");
        var key = FormKey.Factory(policy.FormKey);
        var workbench = provider.Keywords.SingleOrDefault(record => record.FormKey == key);
        Require(workbench is not null && workbench.EditorID == policy.EditorId,
            $"{key}: winning provider lacks the pinned {policy.EditorId} keyword.");
        Require(File.Exists(providerPath), $"Winning provider binary is missing: {providerPath}");
        var info = new FileInfo(providerPath);
        Require(info.Length == policy.Bytes,
            $"{policy.Plugin}: winning binary is {info.Length} bytes, expected {policy.Bytes}.");
        var hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(providerPath)));
        Require(hash.Equals(policy.Sha256, StringComparison.OrdinalIgnoreCase),
            $"{policy.Plugin}: winning binary SHA-256 is {hash}, expected {policy.Sha256}.");
    }

    private static void EnforceHardMasters(string outputPath)
    {
        var plugin = SkyrimMod.CreateFromBinary(outputPath, SkyrimRelease.SkyrimSE);
        var derivedMasters = plugin.EnumerateMajorRecords()
            .Select(record => record.FormKey.ModKey)
            .Concat(plugin.EnumerateMajorRecords().SelectMany(record => record.EnumerateFormLinks())
                .Where(link => !link.FormKey.IsNull)
                .Select(link => link.FormKey.ModKey))
            .Where(master => master != plugin.ModKey)
            .ToHashSet();
        Require(derivedMasters.SetEquals(RequiredMasters),
            $"Refusing hard-master rewrite: derived link closure is " +
            $"[{string.Join(", ", derivedMasters.Select(key => key.FileName.String).Order())}], " +
            $"required contract is [{string.Join(", ", RequiredMasters.Select(key => key.FileName.String))}].");
        plugin.ModHeader.MasterReferences.Clear();
        foreach (var master in RequiredMasters)
        {
            plugin.ModHeader.MasterReferences.Add(new MasterReference { Master = master });
        }
        var temporary = outputPath + ".masters.tmp";
        if (File.Exists(temporary)) File.Delete(temporary);
        try
        {
            plugin.BeginWrite
                .ToPath(temporary)
                .WithLoadOrder(RequiredMasters)
                .WithKnownMasters([])
                .NoMastersListContentCheck()
                .NoModKeySync()
                .Write();
            using (var check = SkyrimMod.CreateFromBinaryOverlay(
                       new ModPath(plugin.ModKey, temporary), SkyrimRelease.SkyrimSE))
            {
                Require(check.ModHeader.MasterReferences.Select(reference => reference.Master)
                        .SequenceEqual(RequiredMasters) &&
                        check.EnumerateMajorRecords().Count() == 1772,
                    "Temporary hard-master rewrite failed its identity/count check; original output retained.");
            }
            File.Move(temporary, outputPath, true);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
        Console.WriteLine($"Declared {RequiredMasters.Count} hard masters.");
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

    // VMAD serializes the no-alias sentinel as unsigned FFFF, while Mutagen
    // exposes that same two-byte value as signed Int16 -1. Compare the raw
    // 16-bit identity so FFFF remains distinct from every real alias ID.
    internal static int RawVmadAlias(short alias) => unchecked((ushort)alias);

    internal static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
