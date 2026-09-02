namespace WeaponBalancePatcher;

public sealed class Settings
{
    public float DaggerSpeed { get; set; } = BalanceRules.Defaults.Dagger;
    public float SwordSpeed { get; set; } = BalanceRules.Defaults.Sword;
    public float WarAxeSpeed { get; set; } = BalanceRules.Defaults.WarAxe;
    public float MaceSpeed { get; set; } = BalanceRules.Defaults.Mace;
    public float GreatswordSpeed { get; set; } = BalanceRules.Defaults.Greatsword;
    public float BattleaxeSpeed { get; set; } = BalanceRules.Defaults.Battleaxe;
    public float WarhammerSpeed { get; set; } = BalanceRules.Defaults.Warhammer;

    public bool IncludeNonPlayableWeapons { get; set; } = true;
    public string[] ExcludeEditorIdContains { get; set; } = ["Dummy", "GiantClub"];
    public bool UseAnimationFallback { get; set; } = true;
    public string[] Exclude { get; set; } = [];
    public ForceClassRule[] ForceClass { get; set; } = [];

    public SpeedProfile ToProfile() => new(
        DaggerSpeed,
        SwordSpeed,
        WarAxeSpeed,
        MaceSpeed,
        GreatswordSpeed,
        BattleaxeSpeed,
        WarhammerSpeed);
}

public sealed class ForceClassRule
{
    public string FormId { get; set; } = string.Empty;
    public string Class { get; set; } = string.Empty;
}
