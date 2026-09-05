using System.Text.Json;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using WeaponBalancePatcher;
using PatcherProgram = WeaponBalancePatcher.Program;

var failures = new List<string>();
void Check(bool condition, string failure)
{
    if (!condition) failures.Add(failure);
}

PatcherProgram.ConfigureLocalizationSemantics();

var expected = new Dictionary<WeaponBalanceClass, (float Damage, float Index)>
{
    [WeaponBalanceClass.Dagger] = (12.0f, 15.0f),
    [WeaponBalanceClass.Sword] = (15.0f, 15.0f),
    [WeaponBalanceClass.Longsword] = (20.0f, 20.0f),
    [WeaponBalanceClass.WarAxe] = (16.0f, 15.0f),
    [WeaponBalanceClass.Mace] = (17.0f, 15.0f),
    [WeaponBalanceClass.Greatsword] = (25.0f, 20.0f),
    [WeaponBalanceClass.Battleaxe] = (26.0f, 20.0f),
    [WeaponBalanceClass.Warhammer] = (28.0f, 20.0f),
};

BalanceRules.Defaults.Validate();
foreach (var (weaponClass, target) in expected)
{
    var actualIndex = target.Damage * BalanceRules.Defaults.For(weaponClass);
    Check(Math.Abs(actualIndex - target.Index) <= 0.0001f,
        $"{weaponClass}: expected record index {target.Index}, got {actualIndex}");
}

foreach (var name in Enum.GetNames<WeaponBalanceClass>())
{
    Check(BalanceRules.TryParseClass(name.ToLowerInvariant(), out var parsed) &&
            string.Equals(parsed.ToString(), name, StringComparison.Ordinal),
        $"case-insensitive class parse failed: {name}");
}

var fixtureKey = new FormKey(ModKey.FromNameAndExtension("Fixture.esp"), 0x800);
Weapon FixtureAt(FormKey formKey, params string[] keywordFormKeys)
{
    var weapon = new Weapon(formKey, SkyrimRelease.SkyrimSE)
    {
        EditorID = "WeaponBalanceFixture",
        BasicStats = new WeaponBasicStats
        {
            Damage = 17,
            Value = 321,
            Weight = 12.5f,
        },
        Data = new WeaponData
        {
            AnimationType = WeaponAnimationType.OneHandSword,
            Skill = Skill.OneHanded,
            Speed = 0.81f,
            Reach = 1.07f,
            Stagger = 0.42f,
        },
    };
    weapon.Keywords ??= [];
    foreach (var value in keywordFormKeys)
    {
        weapon.Keywords.Add(new FormLink<IKeywordGetter>(FormKey.Factory(value)));
    }
    return weapon;
}
Weapon Fixture(params string[] keywordFormKeys) => FixtureAt(fixtureKey, keywordFormKeys);

foreach (var (keyword, weaponClass) in PatcherProgram.StandardKeywords)
{
    var classification = Policy.ClassifyByStandardKeyword(Fixture(keyword.ToString()));
    Check(!classification.Ambiguous && classification.WeaponClass == weaponClass,
        $"actual standard keyword fixture {keyword} did not resolve to {weaponClass}");
}

var steelOnly = Fixture(PatcherProgram.SteelMaterialKeyword.ToString());
var steelClassification = Policy.ClassifyByStandardKeyword(steelOnly);
Check(!steelClassification.Ambiguous && steelClassification.WeaponClass is null,
    "WeapMaterialSteel was misclassified as a weapon type");
var conventionalSteelSword = Fixture(
    PatcherProgram.SteelMaterialKeyword.ToString(), "01E711:Skyrim.esm");
var conventionalSteelPlan = Policy.Plan(
    conventionalSteelSword, fixtureKey.ModKey, new Settings(), BalanceRules.Defaults,
    new Dictionary<FormKey, ParsedRecordRule>());
Check(conventionalSteelPlan.WeaponClass == WeaponBalanceClass.Sword &&
        conventionalSteelPlan.TargetSpeed == BalanceRules.Defaults.Sword,
    "ordinary steel weapon was excluded instead of classified by WeapTypeSword");
var unkeyworded = Fixture();
Check(Policy.ClassifyByStandardKeyword(unkeyworded).WeaponClass is null,
    "unkeyworded animation fallback leaked back into generic selection");
var multiple = Fixture("01E711:Skyrim.esm", "01E714:Skyrim.esm");
Check(Policy.ClassifyByStandardKeyword(multiple).Ambiguous,
    "multiple standard keywords were not rejected as ambiguous");
var mismatched = Fixture("01E711:Skyrim.esm");
mismatched.Data!.AnimationType = WeaponAnimationType.OneHandMace;
var mismatchPlan = Policy.Plan(
    mismatched, fixtureKey.ModKey, new Settings(), BalanceRules.Defaults,
    new Dictionary<FormKey, ParsedRecordRule>());
Check(mismatchPlan.TargetSpeed is null &&
        mismatchPlan.Source == "weapon-type-keyword-animation-mismatch",
    "keyword/animation mismatch was not default-denied");

var before = Fixture("01E714:Skyrim.esm");
var beforeSnapshot = before.DeepCopy();
PatcherProgram.ApplySpeedOnly(before, BalanceRules.Defaults.Mace);
Check(Math.Abs(before.Data!.Speed - BalanceRules.Defaults.Mace) <= PatcherProgram.SpeedTolerance,
    "ApplySpeedOnly did not change WEAP.DNAM.Speed");
var restored = before.DeepCopy();
restored.Data!.Speed = beforeSnapshot.Data!.Speed;
Check(restored.Equals(beforeSnapshot),
    "ApplySpeedOnly changed a field other than WEAP.DNAM.Speed");

var localizedValues = new Dictionary<Language, string>
{
    [Language.Chinese] = "鲁尼克的匕首",
    [Language.Japanese] = "ルルニクのダガー",
    [Language.Polish] = "Sztylet Rulnika",
    [Language.Russian] = "Кинжал Ралника",
    [Language.French] = "Dague de Rulnik",
    [Language.English] = "Rulnik's Dagger",
    [Language.German] = "Rulniks Dolch",
    [Language.Spanish] = "Daga de Rulnik",
    [Language.Italian] = "Pugnale di Rulnik",
};
var localizedOutputKey = ModKey.FromNameAndExtension("LocalizedBalanceFixture.esp");
var localizedWeapon = FixtureAt(new FormKey(localizedOutputKey, 0x800), "01E713:Skyrim.esm");
localizedWeapon.Name = new TranslatedString(Language.English, localizedValues);
localizedWeapon.Description = new TranslatedString(
    Language.English, Array.Empty<KeyValuePair<Language, string>>());
var embeddedWeapon = FixtureAt(new FormKey(localizedOutputKey, 0x801), "01E713:Skyrim.esm");
embeddedWeapon.Name = new TranslatedString(Language.English, "Embedded English fallback");
embeddedWeapon.Description = new TranslatedString(Language.English, string.Empty);
var partialLocalizedWeapon = FixtureAt(
    new FormKey(localizedOutputKey, 0x802), "01E713:Skyrim.esm");
partialLocalizedWeapon.Name = new TranslatedString(
    Language.English,
    new Dictionary<Language, string> { [Language.English] = "Localized English only" });
partialLocalizedWeapon.Description = null;
var descriptionCarrierWeapon = FixtureAt(
    new FormKey(localizedOutputKey, 0x803), "01E713:Skyrim.esm");
descriptionCarrierWeapon.Name = new TranslatedString(
    Language.English, "Description carrier");
descriptionCarrierWeapon.Description = new TranslatedString(
    Language.English, "Nonempty description keeps DLSTRINGS populated");
var outputLanguages = LocalizationPolicy.DetermineOutputLanguages(
    new IWeaponGetter[]
    {
        localizedWeapon, embeddedWeapon, partialLocalizedWeapon, descriptionCarrierWeapon,
    });
LocalizationPolicy.PrepareForLocalizedOutput(
    localizedWeapon, sourceUsesLocalization: true, outputLanguages);
LocalizationPolicy.PrepareForLocalizedOutput(
    embeddedWeapon, sourceUsesLocalization: false, outputLanguages);
LocalizationPolicy.PrepareForLocalizedOutput(
    partialLocalizedWeapon, sourceUsesLocalization: true, outputLanguages);
LocalizationPolicy.PrepareForLocalizedOutput(
    descriptionCarrierWeapon, sourceUsesLocalization: false, outputLanguages);
Check(outputLanguages.ToHashSet().SetEquals(localizedValues.Keys),
    "mixed localized/embedded fixture did not retain the exact nine-language union");
Check(localizedValues.All(pair => localizedWeapon.Name!.TryLookup(pair.Key, out var value) &&
        value == pair.Value),
    "source-provided localized values changed during output preparation");
var nonEnglishTamper = localizedWeapon.DeepCopy();
nonEnglishTamper.Name!.Set(Language.French, "traduction altérée");
Check(!localizedWeapon.Equals(nonEnglishTamper),
    "WEAP semantic equality ignored a non-English translation change");
Check(localizedWeapon.Description is not null &&
        !localizedWeapon.Description.Any() && localizedWeapon.Description.String is null,
    "localized null/ID-0 description was materialized as explicit empty text");
Check(outputLanguages.All(language =>
        embeddedWeapon.Name!.TryLookup(language, out var value) &&
        value == "Embedded English fallback"),
    "embedded English text was not represented as the same fallback in every output language");
Check(outputLanguages.All(language =>
        embeddedWeapon.Description!.TryLookup(language, out var value) && value == string.Empty),
    "explicit embedded empty description did not remain explicit in every output language");

var roundTripRoot = Path.Combine(
    Path.GetTempPath(), "WeaponBalancePatcher.Tests", Guid.NewGuid().ToString("N"));
try
{
    Directory.CreateDirectory(roundTripRoot);
    var roundTripPath = Path.Combine(roundTripRoot, localizedOutputKey.FileName.String);
    var localizedOutput = new SkyrimMod(localizedOutputKey, SkyrimRelease.SkyrimSE)
    {
        UsingLocalization = true,
    };
    localizedOutput.Weapons.Add(localizedWeapon);
    localizedOutput.Weapons.Add(embeddedWeapon);
    localizedOutput.Weapons.Add(partialLocalizedWeapon);
    localizedOutput.Weapons.Add(descriptionCarrierWeapon);
    // Exceed Mutagen's default 100-record parallel cut size.  The production
    // writer must remain byte-identical even when enough translated records
    // exist for the ordinary parallel writer to schedule several tasks.
    for (uint index = 0; index < 420; index++)
    {
        var stressWeapon = FixtureAt(
            new FormKey(localizedOutputKey, 0x900 + index), "01E713:Skyrim.esm");
        stressWeapon.Name = new TranslatedString(
            Language.English, $"Deterministic translated weapon {index:D3}");
        stressWeapon.Description = new TranslatedString(
            Language.English, $"Deterministic description {index:D3}");
        LocalizationPolicy.PrepareForLocalizedOutput(
            stressWeapon, sourceUsesLocalization: false, outputLanguages);
        localizedOutput.Weapons.Add(stressWeapon);
    }

    var deterministicTwin = new SkyrimMod(localizedOutputKey, SkyrimRelease.SkyrimSE)
    {
        UsingLocalization = true,
    };
    foreach (var weapon in localizedOutput.Weapons)
    {
        deterministicTwin.Weapons.Add(weapon.DeepCopy());
    }

    var skyrimMaster = new SkyrimMod(
        ModKey.FromNameAndExtension("Skyrim.esm"), SkyrimRelease.SkyrimSE);
    skyrimMaster.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
    var firstLoadOrder = new LoadOrder<IModListingGetter<ISkyrimModGetter>>(
        [
            new ModListing<ISkyrimModGetter>(skyrimMaster, enabled: true),
            new ModListing<ISkyrimModGetter>(localizedOutput, enabled: true),
        ],
        disposeItems: false);
    var secondLoadOrder = new LoadOrder<IModListingGetter<ISkyrimModGetter>>(
        [
            new ModListing<ISkyrimModGetter>(skyrimMaster, enabled: true),
            new ModListing<ISkyrimModGetter>(deterministicTwin, enabled: true),
        ],
        disposeItems: false);

    PatcherProgram.WriteDeterministically(
        localizedOutput, roundTripPath, firstLoadOrder);
    var deterministicRoot = Path.Combine(roundTripRoot, "determinism");
    var deterministicPath = Path.Combine(
        deterministicRoot, localizedOutputKey.FileName.String);
    PatcherProgram.WriteDeterministically(
        deterministicTwin, deterministicPath, secondLoadOrder);

    Check(File.ReadAllBytes(roundTripPath).SequenceEqual(
            File.ReadAllBytes(deterministicPath)),
        "single-thread localized plugin output is not byte-for-byte deterministic");
    var firstStringsDirectory = Path.Combine(roundTripRoot, "Strings");
    var secondStringsDirectory = Path.Combine(deterministicRoot, "Strings");
    var firstSidecarNames = Directory.EnumerateFiles(firstStringsDirectory)
        .Select(Path.GetFileName)
        .OrderBy(value => value, StringComparer.OrdinalIgnoreCase)
        .ToArray();
    var secondSidecarNames = Directory.EnumerateFiles(secondStringsDirectory)
        .Select(Path.GetFileName)
        .OrderBy(value => value, StringComparer.OrdinalIgnoreCase)
        .ToArray();
    Check(firstSidecarNames.SequenceEqual(secondSidecarNames,
            StringComparer.OrdinalIgnoreCase),
        "single-thread localized writes emitted different sidecar sets");
    foreach (var fileName in firstSidecarNames)
    {
        Check(File.ReadAllBytes(Path.Combine(firstStringsDirectory, fileName!))
                .SequenceEqual(File.ReadAllBytes(
                    Path.Combine(secondStringsDirectory, fileName!))),
            $"single-thread localized sidecar is not deterministic: {fileName}");
    }

    var stringsDirectory = Path.Combine(roundTripRoot, "Strings");
    var sidecars = Directory.EnumerateFiles(stringsDirectory).ToArray();
    Check(sidecars.Length == outputLanguages.Length * 3,
        $"localized writer emitted {sidecars.Length} sidecars instead of {outputLanguages.Length * 3}");
    foreach (var language in outputLanguages)
    {
        foreach (var source in new[] { StringsSource.Normal, StringsSource.IL, StringsSource.DL })
        {
            var fileName = StringsUtility.GetFileName(
                StringsLanguageFormat.FullName, localizedOutputKey, language, source);
            Check(File.Exists(Path.Combine(stringsDirectory, fileName)),
                $"localized writer omitted {fileName}");
        }
    }

    var resourceInventory = LocalizationResourceInventory.Create(
        roundTripRoot,
        [new LocalizationProviderSpec(localizedOutputKey.FileName.String, outputLanguages)]);
    Check(resourceInventory.SchemaVersion == 1 &&
            resourceInventory.Providers.Count == 1 &&
            resourceInventory.Providers[0].CandidateRelativePaths.Count ==
                outputLanguages.Length * 3,
        "localized input-resource inventory did not emit the complete search contract");
    Check(resourceInventory.LooseFiles.Count == outputLanguages.Length * 3 &&
            resourceInventory.Archives.Count == 0 &&
            resourceInventory.Resolutions.All(item =>
                item.Resolution == "loose" && item.SelectedContainer is not null),
        "localized input-resource inventory did not identify all loose winners");
    var repeatInventory = LocalizationResourceInventory.Create(
        roundTripRoot,
        [new LocalizationProviderSpec(localizedOutputKey.FileName.String, outputLanguages)]);
    Check(resourceInventory.Sha256 == repeatInventory.Sha256,
        "localized input-resource inventory is not deterministic");

    using var roundTrip = SkyrimMod.CreateFromBinaryOverlay(
        roundTripPath, SkyrimRelease.SkyrimSE);
    Check(roundTrip.UsingLocalization, "localized round-trip cleared the TES4 Localized flag");
    var localizedRoundTrip = roundTrip.Weapons.Single(record => record.FormKey.ID == 0x800);
    var embeddedRoundTrip = roundTrip.Weapons.Single(record => record.FormKey.ID == 0x801);
    var partialLocalizedRoundTrip = roundTrip.Weapons.Single(record => record.FormKey.ID == 0x802);
    Check(TranslatedString.AllLanguageComparer.Equals(
            localizedWeapon.Name, localizedRoundTrip.Name),
        "localized round-trip did not preserve all nine source Name translations");
    Check(localizedRoundTrip.Description is not null &&
            !localizedRoundTrip.Description.Any() && localizedRoundTrip.Description.String is null,
        "localized round-trip changed null/ID-0 Description semantics");
    Check(localizedWeapon.Description!.NumLanguages == 0 &&
            localizedRoundTrip.Description!.NumLanguages > 0 &&
            !TranslatedString.AllLanguageComparer.Equals(
                localizedWeapon.Description, localizedRoundTrip.Description),
        "empty localized backing-count regression fixture was not reproduced");
    try
    {
        LocalizationPolicy.RequireExactTranslatedSemantics(
            localizedWeapon, localizedRoundTrip, "synthetic-empty-backing");
    }
    catch (InvalidOperationException exception)
    {
        failures.Add("exact translated semantic gate rejected equivalent ID-0 fields: " +
            exception.Message);
    }
    var normalizedEmptyExpected = localizedWeapon.DeepCopy();
    var normalizedEmptyActual = localizedRoundTrip.DeepCopy();
    LocalizationPolicy.NormalizeEmptyBackingForRecordComparison(normalizedEmptyExpected);
    LocalizationPolicy.NormalizeEmptyBackingForRecordComparison(normalizedEmptyActual);
    Check(TranslatedString.AllLanguageComparer.Equals(
            normalizedEmptyExpected.Description, normalizedEmptyActual.Description),
        "empty localized backing normalization did not converge equivalent ID-0 fields");

    var absentDescription = localizedWeapon.DeepCopy();
    absentDescription.Description = null;
    try
    {
        LocalizationPolicy.RequireExactTranslatedSemantics(
            localizedWeapon, absentDescription, "synthetic-absent-description");
        failures.Add("exact translated semantic gate accepted absent vs ID-0 Description");
    }
    catch (InvalidOperationException)
    {
        // Expected: subrecord presence remains semantically distinct.
    }
    var explicitEmptyDescription = localizedWeapon.DeepCopy();
    explicitEmptyDescription.Description = new TranslatedString(Language.English, string.Empty);
    try
    {
        LocalizationPolicy.RequireExactTranslatedSemantics(
            localizedWeapon, explicitEmptyDescription, "synthetic-explicit-empty-description");
        failures.Add("exact translated semantic gate accepted null/ID-0 vs explicit empty text");
    }
    catch (InvalidOperationException)
    {
        // Expected: null and explicit empty text remain semantically distinct.
    }
    var targetLanguageTamper = localizedWeapon.DeepCopy();
    targetLanguageTamper.Name = new TranslatedString(
        Language.French, targetLanguageTamper.Name!.ToArray());
    try
    {
        LocalizationPolicy.RequireExactTranslatedSemantics(
            localizedWeapon, targetLanguageTamper, "synthetic-target-language-tamper");
        failures.Add("exact translated semantic gate accepted a target-language change");
    }
    catch (InvalidOperationException)
    {
        // Expected: the target language is part of the exact semantic contract.
    }
    Check(TranslatedString.AllLanguageComparer.Equals(
            embeddedWeapon.Name, embeddedRoundTrip.Name),
        "localized round-trip changed the expanded embedded Name fallback");
    Check(TranslatedString.AllLanguageComparer.Equals(
            embeddedWeapon.Description, embeddedRoundTrip.Description),
        "localized round-trip changed the explicit embedded empty Description");
    Check(TranslatedString.AllLanguageComparer.Equals(
            partialLocalizedWeapon.Name, partialLocalizedRoundTrip.Name),
        "localized round-trip synthesized translations absent from an English-only localized source");
    Check(partialLocalizedRoundTrip.Description is null,
        "localized round-trip materialized an absent optional Description");

    var removedRelativePath = resourceInventory.Providers[0].CandidateRelativePaths[0];
    File.Delete(Path.Combine(
        roundTripRoot, removedRelativePath.Replace('/', Path.DirectorySeparatorChar)));
    var missingResourceInventory = LocalizationResourceInventory.Create(
        roundTripRoot,
        [new LocalizationProviderSpec(localizedOutputKey.FileName.String, outputLanguages)]);
    Check(missingResourceInventory.Sha256 != resourceInventory.Sha256 &&
            missingResourceInventory.Resolutions.Single(item =>
                item.RelativePath == removedRelativePath).Resolution == "absent",
        "localized input-resource inventory did not detect a newly absent loose candidate");
}
finally
{
    if (Directory.Exists(roundTripRoot))
    {
        Directory.Delete(roundTripRoot, recursive: true);
    }
}

// Exercise the actual Synthesis entry point in a disposable physical Data
// folder.  This catches the important NoPatch contract: pinned Synthesis
// supplies no PatchMod, yet our patcher must still create and write its owned
// output through the serial writer.
var pipelineRoot = Path.Combine(
    Path.GetTempPath(), "WeaponBalancePatcher.Pipeline",
    Guid.NewGuid().ToString("N"));
try
{
    var pipelineData = Path.Combine(pipelineRoot, "Data");
    var pipelineSettings = Path.Combine(pipelineRoot, "Settings");
    var pipelineOutput = Path.Combine(pipelineRoot, "Output", PatcherProgram.OutputPlugin);
    var pipelineReport = Path.Combine(pipelineRoot, "selection-report.json");
    Directory.CreateDirectory(pipelineData);
    Directory.CreateDirectory(pipelineSettings);

    foreach (var masterName in new[]
    {
        "Skyrim.esm", "Update.esm", "Dawnguard.esm",
        "HearthFires.esm", "Dragonborn.esm",
    })
    {
        var master = new SkyrimMod(
            ModKey.FromNameAndExtension(masterName), SkyrimRelease.SkyrimSE);
        master.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        master.WriteToBinary(Path.Combine(pipelineData, masterName));
    }

    var pipelineSourceKey = ModKey.FromNameAndExtension("FixtureWeapons.esp");
    var pipelineSource = new SkyrimMod(pipelineSourceKey, SkyrimRelease.SkyrimSE)
    {
        UsingLocalization = true,
    };
    var pipelineWeapon = FixtureAt(
        new FormKey(pipelineSourceKey, 0x800), "01E711:Skyrim.esm");
    pipelineWeapon.Name = new TranslatedString(
        Language.English,
        new Dictionary<Language, string>
        {
            [Language.English] = "Pipeline sword",
            [Language.French] = "Épée de pipeline",
        });
    pipelineSource.Weapons.Add(pipelineWeapon);
    pipelineSource.WriteToBinary(
        Path.Combine(pipelineData, pipelineSourceKey.FileName.String));

    var pipelineLoadOrder = Path.Combine(pipelineRoot, "plugins.txt");
    File.WriteAllText(pipelineLoadOrder, $"*{pipelineSourceKey.FileName.String}\n");
    File.WriteAllText(
        Path.Combine(pipelineSettings, "settings.json"),
        JsonSerializer.Serialize(new Settings(), new JsonSerializerOptions
        {
            WriteIndented = true,
        }));

    var oldPipelineReport = Environment.GetEnvironmentVariable(
        "WEAPON_BALANCE_REPORT_PATH");
    int pipelineExit;
    try
    {
        Environment.SetEnvironmentVariable(
            "WEAPON_BALANCE_REPORT_PATH", pipelineReport);
        pipelineExit = await PatcherProgram.Main([
            "run-patcher",
            "--DataFolderPath", pipelineData,
            "--ExtraDataFolder", pipelineSettings,
            "--GameRelease", "SkyrimSE",
            "--LoadOrderFilePath", pipelineLoadOrder,
            "--OutputPath", pipelineOutput,
            "--ModKey", PatcherProgram.OutputPlugin,
            "--Localize", "true",
            "--LoadOrderIncludesCreationClub", "true",
        ]);
    }
    finally
    {
        Environment.SetEnvironmentVariable(
            "WEAPON_BALANCE_REPORT_PATH", oldPipelineReport);
    }

    Check(pipelineExit == 0 && File.Exists(pipelineOutput) && File.Exists(pipelineReport),
        "NoPatch pipeline did not create its owned plugin and selection report");
    if (File.Exists(pipelineOutput))
    {
        using var pipelineResult = SkyrimMod.CreateFromBinaryOverlay(
            pipelineOutput, SkyrimRelease.SkyrimSE);
        var pipelineResultWeapon = pipelineResult.Weapons.Single();
        Check(Math.Abs(pipelineResultWeapon.Data!.Speed - BalanceRules.Defaults.Sword) <=
                PatcherProgram.SpeedTolerance,
            "NoPatch pipeline output did not apply the selected sword speed");
        Check(pipelineResult.UsingLocalization &&
                pipelineResultWeapon.Name!.TryLookup(
                    Language.French, out var pipelineFrench) &&
                pipelineFrench == "Épée de pipeline",
            "NoPatch pipeline output did not retain source localization");
    }
}
finally
{
    if (Directory.Exists(pipelineRoot))
    {
        Directory.Delete(pipelineRoot, recursive: true);
    }
}

var archiveFixtureData = Environment.GetEnvironmentVariable(
    "WEAPON_BALANCE_ARCHIVE_FIXTURE_DATA");
if (!string.IsNullOrWhiteSpace(archiveFixtureData))
{
    var creationClubInventory = LocalizationResourceInventory.Create(
        archiveFixtureData,
        [new LocalizationProviderSpec("ccKRTSSE001_Altar.esl", localizedValues.Keys.ToArray())]);
    Check(creationClubInventory.LooseFiles.Count == 0 &&
            creationClubInventory.Archives.Count == 1 &&
            creationClubInventory.Archives[0].MatchedEntries.Count == 27 &&
            creationClubInventory.Resolutions.Count == 27 &&
            creationClubInventory.Resolutions.All(item => item.Resolution == "archive"),
        "optional Creation Club integration fixture did not resolve 27 localized entries from one BSA");

    var realCandidatePath = Environment.GetEnvironmentVariable(
        "WEAPON_BALANCE_REAL_CANDIDATE");
    if (!string.IsNullOrWhiteSpace(realCandidatePath))
    {
        var sourcePath = Path.Combine(archiveFixtureData, "ccKRTSSE001_Altar.esl");
        using var realSource = SkyrimMod.CreateFromBinaryOverlay(
            sourcePath, SkyrimRelease.SkyrimSE);
        using var realCandidate = SkyrimMod.CreateFromBinaryOverlay(
            realCandidatePath, SkyrimRelease.SkyrimSE);
        var realFormKey = FormKey.Factory("000ECE:ccKRTSSE001_Altar.esl");
        var expectedRealRecord = realSource.Weapons.Single(item =>
            item.FormKey == realFormKey).DeepCopy();
        PatcherProgram.ApplySpeedOnly(expectedRealRecord, 1.25f);
        LocalizationPolicy.PrepareForLocalizedOutput(
            expectedRealRecord,
            sourceUsesLocalization: true,
            LocalizationPolicy.DetermineOutputLanguages([expectedRealRecord]));
        var actualRealRecord = realCandidate.Weapons.Single(item =>
            item.FormKey == realFormKey);
        try
        {
            LocalizationPolicy.RequireExactTranslatedSemantics(
                expectedRealRecord, actualRealRecord, realFormKey.ToString());
        }
        catch (InvalidOperationException exception)
        {
            failures.Add("real localized candidate semantic comparison failed: " +
                exception.Message);
        }
        var actualRealComparison = actualRealRecord.DeepCopy();
        LocalizationPolicy.NormalizeEmptyBackingForRecordComparison(expectedRealRecord);
        LocalizationPolicy.NormalizeEmptyBackingForRecordComparison(actualRealComparison);
        Check(expectedRealRecord.Equals(actualRealComparison),
            "real localized candidate differs after narrow empty-backing normalization");

        var realDeterminismRoot = Path.Combine(
            Path.GetTempPath(), "WeaponBalancePatcher.RealDeterminism",
            Guid.NewGuid().ToString("N"));
        try
        {
            var firstRoot = Path.Combine(realDeterminismRoot, "first");
            var secondRoot = Path.Combine(realDeterminismRoot, "second");
            var firstPath = Path.Combine(firstRoot, PatcherProgram.OutputPlugin);
            var secondPath = Path.Combine(secondRoot, PatcherProgram.OutputPlugin);

            LoadOrder<IModListingGetter<ISkyrimModGetter>> CandidateLoadOrder(
                ISkyrimModGetter candidate)
            {
                var listings = candidate.ModHeader.MasterReferences
                    .Select(reference =>
                    {
                        var stub = new SkyrimMod(reference.Master, SkyrimRelease.SkyrimSE);
                        if (reference.Master.FileName.String.EndsWith(
                                ".esm", StringComparison.OrdinalIgnoreCase))
                        {
                            stub.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
                        }
                        else if (reference.Master.FileName.String.EndsWith(
                                     ".esl", StringComparison.OrdinalIgnoreCase))
                        {
                            stub.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master |
                                SkyrimModHeader.HeaderFlag.Small;
                        }
                        return (IModListingGetter<ISkyrimModGetter>)
                            new ModListing<ISkyrimModGetter>(stub, enabled: true);
                    })
                    .Append(new ModListing<ISkyrimModGetter>(candidate, enabled: true))
                    .ToArray();
                return new LoadOrder<IModListingGetter<ISkyrimModGetter>>(
                    listings, disposeItems: false);
            }

            var candidateLoadOrder = CandidateLoadOrder(realCandidate);
            PatcherProgram.WriteDeterministically(
                realCandidate, firstPath, candidateLoadOrder);
            using var secondRealCandidate = SkyrimMod.CreateFromBinaryOverlay(
                realCandidatePath, SkyrimRelease.SkyrimSE);
            var secondCandidateLoadOrder = CandidateLoadOrder(secondRealCandidate);
            PatcherProgram.WriteDeterministically(
                secondRealCandidate, secondPath, secondCandidateLoadOrder);

            var firstRelativeFiles = Directory.EnumerateFiles(
                    firstRoot, "*", SearchOption.AllDirectories)
                .Select(path => Path.GetRelativePath(firstRoot, path))
                .OrderBy(value => value, StringComparer.OrdinalIgnoreCase)
                .ToArray();
            var secondRelativeFiles = Directory.EnumerateFiles(
                    secondRoot, "*", SearchOption.AllDirectories)
                .Select(path => Path.GetRelativePath(secondRoot, path))
                .OrderBy(value => value, StringComparer.OrdinalIgnoreCase)
                .ToArray();
            Check(firstRelativeFiles.SequenceEqual(
                    secondRelativeFiles, StringComparer.OrdinalIgnoreCase),
                "real candidate deterministic rewrites emitted different file sets");
            foreach (var relativePath in firstRelativeFiles)
            {
                Check(File.ReadAllBytes(Path.Combine(firstRoot, relativePath))
                        .SequenceEqual(File.ReadAllBytes(
                            Path.Combine(secondRoot, relativePath))),
                    $"real candidate deterministic rewrite differed: {relativePath}");
            }
        }
        finally
        {
            if (Directory.Exists(realDeterminismRoot))
            {
                Directory.Delete(realDeterminismRoot, recursive: true);
            }
        }
    }
}

using var guardedError = new StringWriter();
var guardedExit = await PatcherProgram.RunGuarded(
    () => Task.FromException<int>(new InvalidOperationException("guarded fixture failure")),
    guardedError);
Check(guardedExit == 1 && guardedError.ToString().Contains(
        "ERROR: InvalidOperationException: guarded fixture failure", StringComparison.Ordinal),
    "CLI exception boundary did not return exit 1 with an actionable diagnostic");

var originalError = Console.Error;
using var commandError = new StringWriter();
int invalidAuditExit;
try
{
    Console.SetError(commandError);
    invalidAuditExit = await PatcherProgram.Main([
        "audit-build",
        Path.Combine(roundTripRoot, "missing-data"),
        Path.Combine(roundTripRoot, "missing-load-order.txt"),
        Path.Combine(roundTripRoot, "missing-plugin.esp"),
        Path.Combine(roundTripRoot, "missing-settings.json"),
        Path.Combine(roundTripRoot, "missing-report.json"),
        Path.Combine(roundTripRoot, "missing-receipt.json"),
    ]);
}
finally
{
    Console.SetError(originalError);
}
Check(invalidAuditExit == 1 && commandError.ToString().StartsWith("ERROR: ",
        StringComparison.Ordinal),
    "malformed audit command escaped the top-level CLI exception boundary");

var settingsPath = Path.Combine(AppContext.BaseDirectory, "Data", "settings.json");
var settings = JsonSerializer.Deserialize<Settings>(File.ReadAllText(settingsPath),
    new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
    ?? throw new InvalidOperationException("Could not parse copied settings fixture.");
var rules = Policy.ParseRecordRules(settings.RecordRules);
Check(rules.Count == 15, $"expected 15 reviewed record rules, got {rules.Count}");
Check(rules.Values.Count(rule => rule.Action == RecordRuleAction.Preserve) == 3,
    "expected three named speed-preservation rules");
Check(rules.Values.Count(rule => rule.Action == RecordRuleAction.Class &&
        rule.WeaponClass == WeaponBalanceClass.Longsword) == 9,
    "expected nine Lost Longswords custom-class rules");
Check(rules.Values.Count(rule => rule.Action == RecordRuleAction.Exclude) == 3,
    "expected three excluded Lost Longswords rules");

foreach (var formKey in new[]
{
    "0063F6:LostLongSwords.esp", "00592D:LostLongSwords.esp",
    "008F16:LostLongSwords.esp", "000D63:LostLongSwords.esp",
    "000D6E:LostLongSwords.esp", "007423:LostLongSwords.esp",
    "003E2F:LostLongSwords.esp", "000D68:LostLongSwords.esp",
    "0099DF:LostLongSwords.esp",
})
{
    Check(rules.TryGetValue(FormKey.Factory(formKey), out var rule) &&
            rule.Action == RecordRuleAction.Class &&
            rule.WeaponClass == WeaponBalanceClass.Longsword,
        $"{formKey}: missing exact Lost Longswords custom-class rule");
}

var expectedLongswords = new Dictionary<string, ushort>
{
    ["0063F6:LostLongSwords.esp"] = 19,
    ["00592D:LostLongSwords.esp"] = 18,
    ["008F16:LostLongSwords.esp"] = 13,
    ["000D63:LostLongSwords.esp"] = 12,
    ["000D6E:LostLongSwords.esp"] = 14,
    ["007423:LostLongSwords.esp"] = 13,
    ["003E2F:LostLongSwords.esp"] = 16,
    ["000D68:LostLongSwords.esp"] = 13,
    ["0099DF:LostLongSwords.esp"] = 13,
};
var curationKey = ModKey.FromNameAndExtension("Ensrick Lost LongSwords Curation.esp");
foreach (var (formKeyText, damage) in expectedLongswords)
{
    var rule = rules[FormKey.Factory(formKeyText)];
    Check(rule.ExpectedWinningProvider == curationKey && rule.ExpectedDamage == damage,
        $"{formKeyText}: expected provider/damage pin differs");
}
var longswordKey = FormKey.Factory("0063F6:LostLongSwords.esp");
var longsword = FixtureAt(longswordKey, "06D931:Skyrim.esm");
longsword.BasicStats!.Damage = 19;
longsword.Data!.AnimationType = WeaponAnimationType.TwoHandSword;
longsword.Data.Skill = Skill.TwoHanded;
longsword.EquipmentType.SetTo(PatcherProgram.BothHandsEquipType);
var longswordPlan = Policy.Plan(
    longsword, curationKey, settings, settings.ToProfile(), rules);
Check(longswordPlan.ExplicitRule && longswordPlan.WeaponClass == WeaponBalanceClass.Longsword &&
        Math.Abs(longswordPlan.TargetSpeed!.Value - 1.0f) <= PatcherProgram.SpeedTolerance,
    "reviewed Lost Longsword rule did not take precedence over Greatsword keyword");
try
{
    Policy.Plan(longsword, longswordKey.ModKey, settings, settings.ToProfile(), rules);
    failures.Add("Lost Longsword accepted the wrong winning provider");
}
catch (InvalidOperationException)
{
    // Expected fail-closed provider pin.
}
var wrongDamage = longsword.DeepCopy();
wrongDamage.BasicStats!.Damage = 20;
try
{
    Policy.Plan(wrongDamage, curationKey, settings, settings.ToProfile(), rules);
    failures.Add("Lost Longsword accepted the wrong winning damage");
}
catch (InvalidOperationException)
{
    // Expected fail-closed damage pin.
}
var wrongLongswordShape = longsword.DeepCopy();
wrongLongswordShape.Data!.AnimationType = WeaponAnimationType.OneHandSword;
try
{
    Policy.Plan(wrongLongswordShape, curationKey, settings, settings.ToProfile(), rules);
    failures.Add("Lost Longsword accepted an inherited one-handed animation");
}
catch (InvalidOperationException)
{
    // Expected fail-closed class-shape pin.
}
var unkeywordedLongsword = longsword.DeepCopy();
unkeywordedLongsword.Keywords!.Clear();
try
{
    Policy.Plan(unkeywordedLongsword, curationKey, settings, settings.ToProfile(), rules);
    failures.Add("Lost Longsword accepted a record without the Greatsword perk keyword");
}
catch (InvalidOperationException)
{
    // Expected fail-closed perk-keyword pin.
}

var directRules = Policy.ParseRecordRules([
    new RecordRule
    {
        FormId = fixtureKey.ToString(),
        Action = "Speed",
        Speed = 1.11f,
        Reason = "future per-record speed fixture",
    },
]);
var directPlan = Policy.Plan(
    Fixture(), fixtureKey.ModKey, new Settings(), BalanceRules.Defaults, directRules);
Check(directPlan.ExplicitRule && directPlan.WeaponClass is null &&
        Math.Abs(directPlan.TargetSpeed!.Value - 1.11f) <= PatcherProgram.SpeedTolerance,
    "direct per-record Speed action did not produce a scoped target");

try
{
    Policy.ParseRecordRules([
        new RecordRule { FormId = "000800:Fixture.esp", Action = "Preserve", Reason = "a" },
        new RecordRule { FormId = "000800:Fixture.esp", Action = "Exclude", Reason = "b" },
    ]);
    failures.Add("duplicate record rules were accepted");
}
catch (InvalidOperationException)
{
    // Expected.
}

var genericMace = Fixture("01E714:Skyrim.esm");
genericMace.Data!.AnimationType = WeaponAnimationType.OneHandMace;
var genericPlan = Policy.Plan(
    genericMace, fixtureKey.ModKey, settings, settings.ToProfile(), rules);
Check(!genericPlan.ExplicitRule && genericPlan.WeaponClass == WeaponBalanceClass.Mace &&
        Math.Abs(genericPlan.TargetSpeed!.Value - BalanceRules.Defaults.Mace) <= PatcherProgram.SpeedTolerance,
    "generic standard-keyword selection does not cover a conventional mace");
var fallbackPlan = Policy.Plan(
    unkeyworded, fixtureKey.ModKey, settings, settings.ToProfile(), rules);
Check(fallbackPlan.TargetSpeed is null && fallbackPlan.Source == "no-standard-weapon-type-keyword",
    "unkeyworded record was selected without an explicit rule");

if (failures.Count > 0)
{
    foreach (var failure in failures) Console.Error.WriteLine($"FAIL: {failure}");
    return 2;
}

Console.WriteLine(
    "PASS: profile math, real FormKey classification, steel guard, no fallback leakage, " +
    "reviewed rule inventory, generic selection coverage, localized round-trip, CLI guard, " +
    "and only-Speed mutation.");
return 0;
