using System.Text.Json;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using WeaponBalancePatcher;
using PatcherProgram = WeaponBalancePatcher.Program;

var failures = new List<string>();
void Check(bool condition, string failure)
{
    if (!condition) failures.Add(failure);
}

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
    "reviewed rule inventory, generic selection coverage, and only-Speed mutation.");
return 0;
