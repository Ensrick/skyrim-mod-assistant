namespace WeaponBalancePatcher;

public sealed class Settings
{
    public float DaggerSpeed { get; set; } = BalanceRules.Defaults.Dagger;
    public float SwordSpeed { get; set; } = BalanceRules.Defaults.Sword;
    public float LongswordSpeed { get; set; } = BalanceRules.Defaults.Longsword;
    public float WarAxeSpeed { get; set; } = BalanceRules.Defaults.WarAxe;
    public float MaceSpeed { get; set; } = BalanceRules.Defaults.Mace;
    public float GreatswordSpeed { get; set; } = BalanceRules.Defaults.Greatsword;
    public float BattleaxeSpeed { get; set; } = BalanceRules.Defaults.Battleaxe;
    public float WarhammerSpeed { get; set; } = BalanceRules.Defaults.Warhammer;

    public bool IncludeNonPlayableWeapons { get; set; } = true;
    public string[] ExcludeEditorIdContains { get; set; } = ["Dummy", "GiantClub"];
    public RecordRule[] RecordRules { get; set; } = [];

    public SpeedProfile ToProfile() => new(
        DaggerSpeed,
        SwordSpeed,
        LongswordSpeed,
        WarAxeSpeed,
        MaceSpeed,
        GreatswordSpeed,
        BattleaxeSpeed,
        WarhammerSpeed);
}

public sealed class RecordRule
{
    public string FormId { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string? Class { get; set; }
    public float? Speed { get; set; }
    public string? ExpectedWinningProvider { get; set; }
    public ushort? ExpectedDamage { get; set; }
    public string Reason { get; set; } = string.Empty;
}
