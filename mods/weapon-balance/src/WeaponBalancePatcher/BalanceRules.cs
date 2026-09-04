namespace WeaponBalancePatcher;

public enum WeaponBalanceClass
{
    Dagger,
    Sword,
    WarAxe,
    Mace,
    Greatsword,
    Battleaxe,
    Warhammer,
}

public sealed record SpeedProfile(
    float Dagger,
    float Sword,
    float WarAxe,
    float Mace,
    float Greatsword,
    float Battleaxe,
    float Warhammer)
{
    public float For(WeaponBalanceClass weaponClass) => weaponClass switch
    {
        WeaponBalanceClass.Dagger => Dagger,
        WeaponBalanceClass.Sword => Sword,
        WeaponBalanceClass.WarAxe => WarAxe,
        WeaponBalanceClass.Mace => Mace,
        WeaponBalanceClass.Greatsword => Greatsword,
        WeaponBalanceClass.Battleaxe => Battleaxe,
        WeaponBalanceClass.Warhammer => Warhammer,
        _ => throw new ArgumentOutOfRangeException(nameof(weaponClass), weaponClass, null),
    };

    public void Validate()
    {
        foreach (var weaponClass in Enum.GetValues<WeaponBalanceClass>())
        {
            var speed = For(weaponClass);
            if (!float.IsFinite(speed) || speed is < 0.1f or > 3.0f)
            {
                throw new InvalidOperationException(
                    $"{weaponClass} speed must be finite and between 0.1 and 3.0; got {speed}.");
            }
        }
    }
}

public static class BalanceRules
{
    public static readonly SpeedProfile Defaults = new(
        Dagger: 1.25f,
        Sword: 1.00f,
        WarAxe: 0.9375f,
        Mace: 15.0f / 17.0f,
        Greatsword: 0.80f,
        Battleaxe: 20.0f / 26.0f,
        Warhammer: 20.0f / 28.0f);

    public static bool TryParseClass(string value, out WeaponBalanceClass weaponClass) =>
        Enum.TryParse(value, ignoreCase: true, out weaponClass)
        && Enum.IsDefined(weaponClass);
}
