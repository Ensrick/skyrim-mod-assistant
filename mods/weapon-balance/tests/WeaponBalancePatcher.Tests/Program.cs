using WeaponBalancePatcher;

var failures = new List<string>();
var expected = new Dictionary<WeaponBalanceClass, (float Damage, float Dps)>
{
    [WeaponBalanceClass.Dagger] = (12.0f, 15.0f),
    [WeaponBalanceClass.Sword] = (15.0f, 15.0f),
    [WeaponBalanceClass.WarAxe] = (16.0f, 15.0f),
    [WeaponBalanceClass.Mace] = (17.0f, 15.0f),
    [WeaponBalanceClass.Greatsword] = (25.0f, 20.0f),
    [WeaponBalanceClass.Battleaxe] = (26.0f, 20.0f),
    [WeaponBalanceClass.Warhammer] = (28.0f, 20.0f),
};

BalanceRules.Defaults.Validate();

foreach (var (weaponClass, target) in expected)
{
    var actualDps = target.Damage * BalanceRules.Defaults.For(weaponClass);
    if (Math.Abs(actualDps - target.Dps) > 0.0001f)
    {
        failures.Add($"{weaponClass}: expected {target.Dps}, got {actualDps}");
    }
}

foreach (var name in Enum.GetNames<WeaponBalanceClass>())
{
    if (!BalanceRules.TryParseClass(name.ToLowerInvariant(), out var parsed)
        || !string.Equals(parsed.ToString(), name, StringComparison.Ordinal))
    {
        failures.Add($"case-insensitive class parse failed: {name}");
    }
}

if (failures.Count > 0)
{
    foreach (var failure in failures)
    {
        Console.Error.WriteLine($"FAIL: {failure}");
    }

    return 2;
}

Console.WriteLine("PASS: all Dragonbone reference DPS targets and class parsers.");
return 0;
