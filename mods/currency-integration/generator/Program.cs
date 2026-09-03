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
    public const string RuntimeQuestEditorId = "Ensrick_CurrencyRuntimeDefaultsQuest";
    public const string RuntimeScriptName = "Ensrick_CurrencyRuntimeDefaultsAlias";
    public const uint RuntimeQuestId = 0x800;
    public const string OhzerQuestEditorId = "Ensrick_OhzerCurrencyQuest";
    public const uint OhzerQuestId = 0x803;

    public static readonly ModKey Ece = ModKey.FromNameAndExtension("exchangeCurrency_enhanced.esp");
    public static readonly ModKey Exchange = ModKey.FromNameAndExtension("SL99Exchanger.esp");
    public static readonly ModKey Coin = ModKey.FromNameAndExtension("C.O.I.N.esp");
    public static readonly ModKey Mint = ModKey.FromNameAndExtension("M.I.N.T.esp");
    public static readonly ModKey Windhelm = ModKey.FromNameAndExtension("WindhelmUsesUlfrics.esp");
    public static readonly ModKey CoinPatch = ModKey.FromNameAndExtension("exchangeCurrency_patch_COIN.esp");
    public static readonly ModKey EceMintUlfric = ModKey.FromNameAndExtension("exchangeCurrency_patch_MINT_ulfric.esp");

    public static readonly IReadOnlyList<ModKey> RequiredMasters =
    [
        ModKey.FromNameAndExtension("Skyrim.esm"),
        ModKey.FromNameAndExtension("Update.esm"),
        ModKey.FromNameAndExtension("Dragonborn.esm"),
        Exchange,
        Ece,
        Coin,
        Mint,
        Windhelm,
        CoinPatch,
    ];

    private static readonly FormKey PlayerRef = FormKey.Factory("000014:Skyrim.esm");
    private static readonly FormKey CoinManagerQuest = FormKey.Factory("00084B:C.O.I.N.esp");
    private static readonly FormKey MintFrameworkQuest = FormKey.Factory("000800:M.I.N.T.esp");
    private static readonly FormKey MintConvertGlobal = FormKey.Factory("DE5037:Update.esm");
    private static readonly FormKey GiftUniversallyValuable = FormKey.Factory("0A0E55:Skyrim.esm");
    private const int CompressedRecordFlag = 0x00040000;

    public sealed class Policy
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }
        [JsonPropertyName("outputPlugin")] public string OutputPluginName { get; set; } = "";
        [JsonPropertyName("exchangeWorkbenchProvider")] public ExchangeWorkbenchProviderPolicy ExchangeWorkbenchProvider { get; set; } = new();
        [JsonPropertyName("quest")] public QuestPolicy Quest { get; set; } = new();
        [JsonPropertyName("overrides")] public OverridePolicy Overrides { get; set; } = new();
        [JsonPropertyName("disabledCurrencyToIngotRecipes")] public List<Target> DisabledRecipes { get; set; } = [];
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
        [JsonPropertyName("eceAltCurrencyQuest")] public ScriptPropertyTarget EceAltCurrencyQuest { get; set; } = new();
        [JsonPropertyName("eceInheritedAltCoinBindings")] public List<InheritedCurrencyBinding> EceAltCoinBindings { get; set; } = [];
        [JsonPropertyName("ohzerQuest")] public OhzerQuestPolicy OhzerQuest { get; set; } = new();
        [JsonPropertyName("mintMadranQuest")] public ScriptMigrationTarget MintMadranQuest { get; set; } = new();
        [JsonPropertyName("eceSeptimQuest")] public StalePropertyTarget EceSeptimQuest { get; set; } = new();
        [JsonPropertyName("drakrPurseAdapters")] public DrakrPursePolicy DrakrPurseAdapters { get; set; } = new();
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
    }

    public sealed class ScriptPropertyTarget : Target
    {
        [JsonPropertyName("script")] public string Script { get; set; } = "";
        [JsonPropertyName("property")] public string Property { get; set; } = "";
        [JsonPropertyName("sourceFormKey")] public string SourceFormKey { get; set; } = "";
        [JsonPropertyName("targetFormKey")] public string TargetFormKey { get; set; } = "";
    }

    public sealed class ScriptMigrationTarget : Target
    {
        [JsonPropertyName("aliasId")] public short AliasId { get; set; }
        [JsonPropertyName("sourceScript")] public string SourceScript { get; set; } = "";
        [JsonPropertyName("targetScript")] public string TargetScript { get; set; } = "";
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

    public sealed class DrakrPursePolicy
    {
        [JsonPropertyName("canonicalCoin")] public string CanonicalCoin { get; set; } = "";
        [JsonPropertyName("changeLists")] public List<OwnedListTarget> ChangeLists { get; set; } = [];
        [JsonPropertyName("purses")] public List<DrakrPurseTarget> Purses { get; set; } = [];
    }

    public sealed class OwnedListTarget
    {
        [JsonPropertyName("sourceFormKey")] public string SourceFormKey { get; set; } = "";
        [JsonPropertyName("sourceEditorId")] public string SourceEditorId { get; set; } = "";
        [JsonPropertyName("formId")] public string FormId { get; set; } = "";
        [JsonPropertyName("editorId")] public string EditorId { get; set; } = "";
    }

    public sealed class DrakrPurseTarget : Target
    {
        [JsonPropertyName("entries")] public List<DrakrPurseEntry> Entries { get; set; } = [];
    }

    public sealed class DrakrPurseEntry
    {
        [JsonPropertyName("sourceFormKey")] public string SourceFormKey { get; set; } = "";
        [JsonPropertyName("targetFormKey")] public string TargetFormKey { get; set; } = "";
        [JsonPropertyName("count")] public short Count { get; set; }
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
        if (args is ["--audit-links", var dataFolder, var loadOrderFile, var pluginPath])
        {
            return LinkAudit.Run(dataFolder, loadOrderFile, pluginPath);
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

        foreach (var target in policy.Overrides.CoinPurses)
        {
            PatchPurse(state, target);
        }

        PatchGold(state, policy.Overrides.Gold);
        PatchMintGlobal(state, policy.Overrides.MintAutoConvert);
        PatchEceAltCurrencyQuest(state, policy.Overrides.EceAltCurrencyQuest,
            policy.Overrides.EceAltCoinBindings);
        PatchMadranQuest(state, policy.Overrides.MintMadranQuest);
        PatchEceSeptimQuest(state, policy.Overrides.EceSeptimQuest);
        PatchDrakrPurseAdapters(state, policy.Overrides.DrakrPurseAdapters);
        PatchDrakrPile(state, policy.Overrides.DrakrPile);
        CreateAncientExchangeRecipes(state, policy.Overrides.AncientExchangeWorkbench,
            policy.Overrides.AncientExchangeRecipes);

        foreach (var target in policy.DisabledRecipes.OrderBy(item => FormKey.Factory(item.FormKey).ID))
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
            Console.WriteLine($"Disabled currency-to-ingot COBJ {key} {target.EditorId}.");
        }

        CreateRuntimeQuest(state, policy.Quest);
        CreateOhzerQuest(state, policy.Overrides.OhzerQuest);

        var records = state.PatchMod.EnumerateMajorRecords().ToArray();
        Require(records.Length == 45, $"Expected exactly 45 records, got {records.Length}.");
        Require(records.Count(record => record is IActivatorGetter) == 3,
            "Expected two pile forwards and one Drakr pile override.");
        Require(records.Count(record => record is ILeveledItemGetter) == 8,
            "Expected six LVLI purse overrides and two owned Drakr adapters.");
        Require(records.Count(record => record is IMiscItemGetter) == 1, "Expected one MISC override.");
        Require(records.Count(record => record is IGlobalGetter) == 1, "Expected one GLOB override.");
        Require(records.Count(record => record is IConstructibleObjectGetter) == 27,
            "Expected 17 disabled COBJ overrides and ten owned exchange recipes.");
        Require(records.Count(record => record is IQuestGetter) == 5,
            "Expected three compatibility QUST overrides and two owned QUSTs.");
        Require(!records.Any(record => record.IsDeleted), "Output contains a deleted record.");
        Require(records.Count(record => record.FormKey.ModKey == state.PatchMod.ModKey) == 14,
            "Only two Drakr adapter LVLIs, two runtime quests, and ten exchange recipes may use owned FormKeys.");
        Console.WriteLine("Generated 45 records: 14 semantic overrides, 17 disabled recipes, ten owned exchange recipes, two owned Drakr adapter LVLIs, and two owned runtime quests.");
    }

    private static void PatchPurse(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        PurseTarget target)
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

        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        patch.Flags = 0;
        patch.ChanceNone = new Percent(0.0);
        patch.Global.SetTo(FormKey.Null);
        patch.Entries ??= [];
        patch.Entries.Clear();
        foreach (var count in target.Counts)
        {
            var entry = new LeveledItemEntry
            {
                Data = new LeveledItemEntryData
                {
                    Level = 1,
                    Count = count,
                },
            };
            entry.Data.Reference.SetTo(FormKey.Factory("00000F:Skyrim.esm"));
            patch.Entries.Add(entry);
        }
        ClearCompression(patch);
        Console.WriteLine($"Rebuilt purse LVLI {key} {target.EditorId}: 16 equal Gold001 choices {target.Counts.Min()}..{target.Counts.Max()}.");
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

    private static void PatchMadranQuest(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        ScriptMigrationTarget target)
    {
        var key = FormKey.Factory(target.FormKey);
        var contexts = new FormLink<IQuestGetter>(key)
            .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, IQuest, IQuestGetter>(state.LinkCache)
            .ToArray();
        var winner = contexts.Single(context => context.ModKey == EceMintUlfric);
        Require(winner.ModKey == EceMintUlfric,
            $"{key}: expected ECE M.I.N.T. Ulfric patch winner, found {winner.ModKey}.");
        Require(winner.Record.EditorID == target.EditorId,
            $"{key}: Ma'dran quest EditorID is {winner.Record.EditorID}, expected {target.EditorId}.");
        var patch = winner.GetOrAddAsOverride(state.PatchMod);
        var vmad = patch.VirtualMachineAdapter
            ?? throw new InvalidOperationException($"{key}: Ma'dran quest VMAD is missing.");
        var alias = vmad.Aliases.Single(candidate => candidate.Property.Alias == target.AliasId);
        var script = alias.Scripts.Single(candidate => candidate.Name == target.SourceScript);
        var properties = script.Properties.OfType<ScriptObjectProperty>()
            .ToDictionary(property => property.Name, StringComparer.Ordinal);
        var expectedNames = new HashSet<string>(StringComparer.Ordinal)
        {
            "CurrencyFunctions", "DES_Ulfric", "DES_UlfricLocations", "DES_WindhelmPriceAdjustmentPerk",
        };
        Require(properties.Count == expectedNames.Count && properties.Keys.ToHashSet().SetEquals(expectedNames),
            $"{key}: orphan Ma'dran property set changed; review the migration.");
        Require(properties["CurrencyFunctions"].Object.FormKey == FormKey.Factory("000800:M.I.N.T.esp") &&
                properties["DES_Ulfric"].Object.FormKey == FormKey.Factory("DE5024:Update.esm") &&
                properties["DES_UlfricLocations"].Object.FormKey == FormKey.Factory("000802:WindhelmUsesUlfrics.esp") &&
                properties["DES_WindhelmPriceAdjustmentPerk"].Object.FormKey == FormKey.Factory("000800:WindhelmUsesUlfrics.esp"),
            $"{key}: orphan Ma'dran bindings changed; review the migration.");

        script.Name = target.TargetScript;
        properties["DES_Ulfric"].Name = "akCurrency";
        properties["DES_UlfricLocations"].Name = "akSwapLocations";
        properties["DES_WindhelmPriceAdjustmentPerk"].Name = "akPriceMod";
        var player = new ScriptObjectProperty { Name = "PlayerRef" };
        player.Object.SetTo(PlayerRef);
        script.Properties.Add(player);

        var questFragment = vmad.Scripts.Single(candidate =>
            candidate.Name == "QF_DES_UlfricWindhelmService_03000002");
        foreach (var propertyName in target.StaleQuestProperties)
        {
            var stale = questFragment.Properties.Single(property => property.Name == propertyName);
            questFragment.Properties.Remove(stale);
            Console.WriteLine($"Removed stale M.I.N.T./ECE quest-fragment VMAD property {propertyName}.");
        }
        ClearCompression(patch);
        Console.WriteLine($"Migrated Ma'dran alias {target.AliasId} from missing {target.SourceScript} to shipped {target.TargetScript}.");
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

    private static void PatchDrakrPurseAdapters(
        IPatcherState<ISkyrimMod, ISkyrimModGetter> state,
        DrakrPursePolicy policy)
    {
        var canonical = FormKey.Factory(policy.CanonicalCoin);
        var ownedBySource = new Dictionary<FormKey, FormKey>();
        foreach (var target in policy.ChangeLists)
        {
            var sourceKey = FormKey.Factory(target.SourceFormKey);
            var contexts = new FormLink<ILeveledItemGetter>(sourceKey)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ILeveledItem, ILeveledItemGetter>(state.LinkCache)
                .ToArray();
            var source = contexts.Single(context => context.ModKey == Coin).Record;
            Require(source.EditorID == target.SourceEditorId,
                $"{sourceKey}: Drakr change-list EditorID is {source.EditorID}, expected {target.SourceEditorId}.");
            var sourceEntries = source.Entries
                ?? throw new InvalidOperationException($"{sourceKey}: Drakr change-list entries are null.");
            Require(source.Global.IsNull && sourceEntries.Count == 4 &&
                    sourceEntries.All(entry => entry.Data?.Level == 1) &&
                    sourceEntries.All(entry => entry.Data?.Reference.FormKey == FormKey.Factory("DE5012:Update.esm")) &&
                    sourceEntries.Select(entry => entry.Data!.Count).SequenceEqual(new short[] { 1, 1, 2, 2 }),
                $"{sourceKey}: shipped Drakr change-list structure changed; review the adapter.");

            var ownedKey = new FormKey(state.PatchMod.ModKey, uint.Parse(target.FormId,
                System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture));
            var clone = new LeveledItem(ownedKey, SkyrimRelease.SkyrimSE)
            {
                EditorID = target.EditorId,
                Flags = source.Flags,
                ChanceNone = source.ChanceNone,
                Entries = [],
            };
            foreach (var sourceEntry in sourceEntries)
            {
                var entry = new LeveledItemEntry
                {
                    Data = new LeveledItemEntryData
                    {
                        Level = sourceEntry.Data!.Level,
                        Count = sourceEntry.Data.Count,
                    },
                };
                entry.Data.Reference.SetTo(canonical);
                clone.Entries.Add(entry);
            }
            state.PatchMod.LeveledItems.Add(clone);
            ownedBySource.Add(sourceKey, ownedKey);
            Console.WriteLine($"Cloned Drakr change LVLI {sourceKey} as {ownedKey} with canonical {canonical} output.");
        }

        foreach (var target in policy.Purses)
        {
            var key = FormKey.Factory(target.FormKey);
            var contexts = new FormLink<ILeveledItemGetter>(key)
                .ResolveAllContexts<ISkyrimMod, ISkyrimModGetter, ILeveledItem, ILeveledItemGetter>(state.LinkCache)
                .ToArray();
            var sourceContext = contexts.Single(context => context.ModKey == Coin);
            var source = sourceContext.Record;
            Require(source.EditorID == target.EditorId && source.Flags.HasFlag(LeveledItem.Flag.UseAll) &&
                    (double)source.ChanceNone == 0.0 && source.Global.IsNull,
                $"{key}: shipped Drakr purse header changed; review the adapter.");
            var sourceEntries = source.Entries
                ?? throw new InvalidOperationException($"{key}: source purse entries are null.");
            Require(sourceEntries.Count == target.Entries.Count,
                $"{key}: shipped Drakr purse entry count changed; review the adapter.");
            for (var index = 0; index < target.Entries.Count; index++)
            {
                var expected = target.Entries[index];
                var data = sourceEntries[index].Data
                    ?? throw new InvalidOperationException($"{key}: source purse entry {index} is null.");
                Require(data.Level == 1 && data.Count == expected.Count &&
                        data.Reference.FormKey == FormKey.Factory(expected.SourceFormKey),
                    $"{key}: source purse entry {index} changed; review the adapter.");
            }

            var patch = sourceContext.GetOrAddAsOverride(state.PatchMod);
            for (var index = 0; index < target.Entries.Count; index++)
            {
                var mapping = target.Entries[index];
                var targetKey = string.Equals(mapping.TargetFormKey, "$canonical", StringComparison.Ordinal)
                    ? canonical
                    : ownedBySource[FormKey.Factory(mapping.SourceFormKey)];
                patch.Entries![index].Data!.Reference.SetTo(targetKey);
            }
            ClearCompression(patch);
            Console.WriteLine($"Retargeted Drakr purse LVLI {key} to canonical tender without changing its distribution.");
        }
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
        Require(FormKey.Factory(policy.Overrides.EceAltCurrencyQuest.FormKey) ==
                FormKey.Factory("000827:exchangeCurrency_patch_COIN.esp"),
            "ECE alternate-currency quest target changed.");
        Require(policy.Overrides.EceAltCurrencyQuest.EditorId == "EC_altCurrencyScript" &&
                policy.Overrides.EceAltCurrencyQuest.Script == "EC_drakrsScript" &&
                policy.Overrides.EceAltCurrencyQuest.Property == "Drakr",
            "ECE Drakr VMAD policy identity changed.");
        Require(FormKey.Factory(policy.Overrides.EceAltCurrencyQuest.SourceFormKey) ==
                FormKey.Factory("DE5016:Update.esm") &&
                FormKey.Factory(policy.Overrides.EceAltCurrencyQuest.TargetFormKey) ==
                FormKey.Factory("DE5015:Update.esm"),
            "ECE Drakr VMAD policy must correct leveled DE5016 to canonical MISC DE5015.");
        var altBindings = policy.Overrides.EceAltCoinBindings;
        Require(altBindings.Count == 5 &&
                altBindings.Select(item => item.Script).SequenceEqual(new[]
                {
                    "EC_ulfricsScript",
                    "EC_dramsScript",
                    "EC_medesScript",
                    "EC_drakrsScript",
                    "EC_oshkasScript",
                }) &&
                altBindings.Select(item => FormKey.Factory(item.CurrencyFormKey)).SequenceEqual(new[]
                {
                    FormKey.Factory("DE5024:Update.esm"),
                    FormKey.Factory("DE5029:Update.esm"),
                    FormKey.Factory("DE5021:Update.esm"),
                    FormKey.Factory("DE5015:Update.esm"),
                    FormKey.Factory("000871:exchangeCurrency_patch_COIN.esp"),
                }) &&
                altBindings.Select(item => item.CurrencyProperty).SequenceEqual(new[]
                {
                    "Ulfric", "Dram", "Mede", "Drakr", "Oshka",
                }),
            "ECE inherited altCoins binding policy changed.");
        var ohzer = policy.Overrides.OhzerQuest;
        Require(ohzer.FormId.Equals(OhzerQuestId.ToString("X6"), StringComparison.OrdinalIgnoreCase) &&
                ohzer.EditorId == OhzerQuestEditorId &&
                ohzer.AliasId == 0 && ohzer.AliasName == "PlayerRef" &&
                FormKey.Factory(ohzer.TemplateQuestFormKey) ==
                    FormKey.Factory("000827:exchangeCurrency_patch_COIN.esp") &&
                ohzer.TemplateScript == "EC_oshkasScript" &&
                ohzer.Script == "Ensrick_OhzerCurrencyScript" &&
                ohzer.CurrencyProperty == "Ohzer" &&
                FormKey.Factory(ohzer.CurrencyFormKey) ==
                    FormKey.Factory("00086F:exchangeCurrency_patch_COIN.esp") &&
                ohzer.KeywordProperty == "OhzerMoneyKeyword" &&
                FormKey.Factory(ohzer.KeywordFormKey) ==
                    FormKey.Factory("000BB5:exchangeCurrency_enhanced.esp"),
            "Owned Ohzer transaction-quest policy changed.");
        Require(FormKey.Factory(policy.Overrides.MintMadranQuest.FormKey) ==
                FormKey.Factory("000002:WindhelmUsesUlfrics.esp") &&
                policy.Overrides.MintMadranQuest.EditorId == "DES_UlfricWindhelmServicesQuest" &&
                policy.Overrides.MintMadranQuest.AliasId == 5 &&
                policy.Overrides.MintMadranQuest.SourceScript == "DES_MadranSwapper" &&
                policy.Overrides.MintMadranQuest.TargetScript == "DES_CurrencyFramework_BarterExclusion" &&
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
            "Ma'dran script-migration policy changed.");
        Require(FormKey.Factory(policy.Overrides.EceSeptimQuest.FormKey) ==
                FormKey.Factory("000B63:exchangeCurrency_enhanced.esp") &&
                policy.Overrides.EceSeptimQuest.EditorId == "EC_septimsScript" &&
                policy.Overrides.EceSeptimQuest.StaleProperties.SequenceEqual(new[]
                {
                    "EC_septimsFunctions.busy",
                    "EC_septimsScript.busy",
                    "EC_septimsScript.DES_ConvertCoins",
                }),
            "ECE stale-VMAD cleanup policy changed.");
        var drakr = policy.Overrides.DrakrPurseAdapters;
        Require(FormKey.Factory(drakr.CanonicalCoin) == FormKey.Factory("DE5015:Update.esm"),
            "Drakr purse adapters must emit ECE's canonical Drakr Whale MISC.");
        Require(drakr.ChangeLists.Count == 2 && drakr.Purses.Count == 3,
            "Drakr purse policy must contain two owned change lists and three purse overrides.");
        Require(drakr.ChangeLists.Select(item => FormKey.Factory(item.SourceFormKey)).SequenceEqual(new[]
                {
                    FormKey.Factory("000D66:C.O.I.N.esp"),
                    FormKey.Factory("000D67:C.O.I.N.esp"),
                }) &&
                drakr.ChangeLists.Select(item => item.FormId).SequenceEqual(new[] { "000801", "000802" }),
            "Drakr owned change-list identities changed.");
        Require(drakr.Purses.Select(item => FormKey.Factory(item.FormKey)).SequenceEqual(new[]
                {
                    FormKey.Factory("000800:C.O.I.N.esp"),
                    FormKey.Factory("000801:C.O.I.N.esp"),
                    FormKey.Factory("000802:C.O.I.N.esp"),
                }) && drakr.Purses.All(item => item.Entries.Count == 3),
            "Drakr purse override identities changed.");
        Require(drakr.Purses.SelectMany(item => item.Entries)
                .All(entry => entry.Count > 0 &&
                    (entry.TargetFormKey == "$canonical" || entry.TargetFormKey == "$owned") &&
                    (entry.TargetFormKey == "$canonical" ||
                     drakr.ChangeLists.Any(change => change.SourceFormKey == entry.SourceFormKey))),
            "Drakr purse entry mapping is invalid.");
        Require(FormKey.Factory(policy.Overrides.DrakrPile.FormKey) ==
                FormKey.Factory("0009C6:C.O.I.N.esp") &&
                policy.Overrides.DrakrPile.EditorId == "DES_PileofDrakr" &&
                policy.Overrides.DrakrPile.Script == "DLC2GoldPileScript" &&
                policy.Overrides.DrakrPile.Property == "Gold001" &&
                FormKey.Factory(policy.Overrides.DrakrPile.SourceFormKey) ==
                    FormKey.Factory("DE5012:Update.esm") &&
                FormKey.Factory(policy.Overrides.DrakrPile.TargetFormKey) ==
                    FormKey.Factory("DE5015:Update.esm"),
            "Drakr pile canonical-tender policy changed.");
        Require(FormKey.Factory(policy.Overrides.AncientExchangeWorkbench) ==
                FormKey.Factory("000801:SL99Exchanger.esp"),
            "Ancient exchange recipes must use Exchange Currency SE's money-exchange workbench.");
        var exchangeRecipes = policy.Overrides.AncientExchangeRecipes;
        Require(exchangeRecipes.Count == 10 &&
                exchangeRecipes.Select(item => item.FormId).SequenceEqual(new[]
                {
                    "000804", "000805", "000806", "000807",
                    "000808", "000809", "00080A", "00080B",
                    "00080C", "00080D",
                }) &&
                exchangeRecipes.Select(item => item.EditorId).Distinct().Count() == 10 &&
                exchangeRecipes.All(item => item.InputCount > 0 && item.OutputCount > 0) &&
                exchangeRecipes.Take(9).All(item => item.Purpose == "coin-default-rate") &&
                exchangeRecipes[^1].Purpose == "effective-mint-core-rate" &&
                exchangeRecipes.All(item =>
                    FormKey.Factory(item.OutputFormKey) == FormKey.Factory("00000F:Skyrim.esm")),
            "Ancient one-way exchange-recipe policy changed.");
        var expectedAncientRates = new Dictionary<FormKey, (int input, ushort output)>
        {
            [FormKey.Factory("DE5012:Update.esm")] = (20, 3),
            [FormKey.Factory("DE5013:Update.esm")] = (20, 3),
            [FormKey.Factory("DE5014:Update.esm")] = (20, 3),
            [FormKey.Factory("DE5015:Update.esm")] = (20, 3),
            [FormKey.Factory("DE5019:Update.esm")] = (5, 2),
            [FormKey.Factory("DE5020:Update.esm")] = (5, 3),
            [FormKey.Factory("DE5022:Update.esm")] = (4, 1),
            [FormKey.Factory("DE5018:Update.esm")] = (5, 8),
            [FormKey.Factory("DE5017:Update.esm")] = (1, 1),
            [FormKey.Factory("DE5027:Update.esm")] = (1, 1),
        };
        Require(exchangeRecipes.All(item =>
                expectedAncientRates.GetValueOrDefault(FormKey.Factory(item.InputFormKey)) ==
                    (item.InputCount, item.OutputCount)) &&
                exchangeRecipes.Select(item => FormKey.Factory(item.InputFormKey)).ToHashSet()
                    .SetEquals(expectedAncientRates.Keys),
            "Ancient exchange ratios no longer preserve the effective installed default values.");
        Require(policy.DisabledRecipes.Count == 17, "Policy must contain exactly 17 disabled recipes.");
        Require(policy.DisabledRecipes.Select(item => FormKey.Factory(item.FormKey)).Distinct().Count() == 17,
            "Disabled-recipe FormKeys must be unique.");
        Require(policy.DisabledRecipes.All(item => FormKey.Factory(item.FormKey).ModKey == CoinPatch),
            "Every disabled recipe must originate in exchangeCurrency_patch_COIN.esp.");
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

    internal static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
