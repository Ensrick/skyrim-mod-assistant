using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace WeaponBalancePatcher;

public enum RecordRuleAction
{
    Preserve,
    Exclude,
    Class,
    Speed,
}

public sealed record ParsedRecordRule(
    FormKey FormKey,
    RecordRuleAction Action,
    WeaponBalanceClass? WeaponClass,
    float? Speed,
    ModKey? ExpectedWinningProvider,
    ushort? ExpectedDamage,
    string Reason);

public sealed record SelectionDecision(
    RecordRuleAction Action,
    WeaponBalanceClass? WeaponClass,
    float? TargetSpeed,
    bool ExplicitRule,
    string Source,
    string? Reason);

public static class Policy
{
    public static IReadOnlyDictionary<FormKey, ParsedRecordRule> ParseRecordRules(
        IEnumerable<RecordRule> source)
    {
        var result = new Dictionary<FormKey, ParsedRecordRule>();
        foreach (var input in source ?? [])
        {
            FormKey formKey;
            try
            {
                formKey = FormKey.Factory(input.FormId.Trim());
            }
            catch (Exception exception)
            {
                throw new InvalidOperationException(
                    $"Invalid RecordRules FormId '{input.FormId}': {exception.Message}", exception);
            }

            if (!Enum.TryParse<RecordRuleAction>(input.Action, true, out var action) ||
                !Enum.IsDefined(action))
            {
                throw new InvalidOperationException(
                    $"Invalid RecordRules action '{input.Action}' for {formKey}.");
            }

            if (string.IsNullOrWhiteSpace(input.Reason))
            {
                throw new InvalidOperationException($"RecordRules {formKey} requires a review reason.");
            }

            WeaponBalanceClass? weaponClass = null;
            if (action == RecordRuleAction.Class)
            {
                if (string.IsNullOrWhiteSpace(input.Class) ||
                    !BalanceRules.TryParseClass(input.Class, out var parsedClass))
                {
                    throw new InvalidOperationException(
                        $"RecordRules {formKey} Class action has invalid class '{input.Class}'.");
                }
                weaponClass = parsedClass;
            }
            else if (!string.IsNullOrWhiteSpace(input.Class))
            {
                throw new InvalidOperationException(
                    $"RecordRules {formKey} action {action} may not specify Class.");
            }

            float? speed = null;
            if (action == RecordRuleAction.Speed)
            {
                if (input.Speed is not { } configuredSpeed || !float.IsFinite(configuredSpeed) ||
                    configuredSpeed is < 0.1f or > 3.0f)
                {
                    throw new InvalidOperationException(
                        $"RecordRules {formKey} Speed action requires a finite speed in [0.1, 3.0].");
                }
                speed = configuredSpeed;
            }
            else if (input.Speed is not null)
            {
                throw new InvalidOperationException(
                    $"RecordRules {formKey} action {action} may not specify Speed.");
            }

            ModKey? expectedProvider = null;
            if (!string.IsNullOrWhiteSpace(input.ExpectedWinningProvider))
            {
                try
                {
                    expectedProvider = ModKey.FromNameAndExtension(input.ExpectedWinningProvider.Trim());
                }
                catch (Exception exception)
                {
                    throw new InvalidOperationException(
                        $"RecordRules {formKey} has invalid ExpectedWinningProvider " +
                        $"'{input.ExpectedWinningProvider}': {exception.Message}", exception);
                }
            }
            if (input.ExpectedDamage is not null && expectedProvider is null)
            {
                throw new InvalidOperationException(
                    $"RecordRules {formKey} ExpectedDamage requires ExpectedWinningProvider.");
            }

            var rule = new ParsedRecordRule(
                formKey,
                action,
                weaponClass,
                speed,
                expectedProvider,
                input.ExpectedDamage,
                input.Reason.Trim());
            if (!result.TryAdd(formKey, rule))
            {
                throw new InvalidOperationException($"Duplicate RecordRules FormId: {formKey}.");
            }
        }

        return result;
    }

    public static SelectionDecision Plan(
        IWeaponGetter weapon,
        ModKey winningProvider,
        Settings settings,
        SpeedProfile profile,
        IReadOnlyDictionary<FormKey, ParsedRecordRule> rules)
    {
        if (rules.TryGetValue(weapon.FormKey, out var rule))
        {
            if (rule.ExpectedWinningProvider is { } expectedProvider &&
                winningProvider != expectedProvider)
            {
                throw new InvalidOperationException(
                    $"{weapon.FormKey}: winning provider is {winningProvider}, " +
                    $"expected reviewed provider {expectedProvider}.");
            }
            if (rule.ExpectedDamage is { } expectedDamage &&
                weapon.BasicStats?.Damage != expectedDamage)
            {
                throw new InvalidOperationException(
                    $"{weapon.FormKey}: winning damage is {weapon.BasicStats?.Damage}, " +
                    $"expected reviewed damage {expectedDamage}.");
            }
            if (rule.Action == RecordRuleAction.Class)
            {
                if (rule.WeaponClass is not { } explicitClass)
                {
                    throw new InvalidOperationException(
                        $"{weapon.FormKey}: explicit Class rule has no weapon class.");
                }
                if (!HasCoherentClassShape(weapon, explicitClass, out var shapeFailure))
                {
                    throw new InvalidOperationException(
                        $"{weapon.FormKey}: explicit {explicitClass} class shape is invalid: {shapeFailure}.");
                }
            }
            return rule.Action switch
            {
                RecordRuleAction.Preserve => new(
                    rule.Action, null, null, true, "explicit-preserve", rule.Reason),
                RecordRuleAction.Exclude => new(
                    rule.Action, null, null, true, "explicit-exclude", rule.Reason),
                RecordRuleAction.Class => new(
                    rule.Action,
                    rule.WeaponClass,
                    profile.For(rule.WeaponClass!.Value),
                    true,
                    "explicit-class",
                    rule.Reason),
                RecordRuleAction.Speed => new(
                    rule.Action, null, rule.Speed, true, "explicit-speed", rule.Reason),
                _ => throw new InvalidOperationException($"Unsupported rule action {rule.Action}."),
            };
        }

        if (!settings.IncludeNonPlayableWeapons && IsNonPlayableWeapon(weapon))
        {
            return Skip("non-playable");
        }

        if (weapon.Data is { } data &&
            (data.Flags & WeaponData.Flag.NotUsedInNormalCombat) != 0)
        {
            return Skip("not-used-in-normal-combat");
        }

        if (weapon.EditorID is { } editorId && (settings.ExcludeEditorIdContains ?? [])
            .Where(fragment => !string.IsNullOrWhiteSpace(fragment))
            .Any(fragment => editorId.Contains(fragment.Trim(), StringComparison.OrdinalIgnoreCase)))
        {
            return Skip("editor-id-utility-filter");
        }

        var classes = (weapon.Keywords ?? [])
            .Select(link => link.FormKey)
            .Where(Program.StandardKeywords.ContainsKey)
            .Select(key => Program.StandardKeywords[key])
            .Distinct()
            .ToArray();
        if (classes.Length != 1)
        {
            return Skip(classes.Length == 0
                ? "no-standard-weapon-type-keyword"
                : "multiple-standard-weapon-type-keywords");
        }

        var weaponClass = classes[0];
        if (!HasCoherentClassShape(weapon, weaponClass, out _))
        {
            return Skip("weapon-type-keyword-animation-mismatch");
        }
        return new SelectionDecision(
            RecordRuleAction.Class,
            weaponClass,
            profile.For(weaponClass),
            false,
            "standard-weapon-type-keyword",
            null);
    }

    public static Classification ClassifyByStandardKeyword(IWeaponGetter weapon)
    {
        var classes = (weapon.Keywords ?? [])
            .Select(link => link.FormKey)
            .Where(Program.StandardKeywords.ContainsKey)
            .Select(key => Program.StandardKeywords[key])
            .Distinct()
            .ToArray();
        return classes.Length switch
        {
            0 => new Classification(null, false, "no-standard-weapon-type-keyword"),
            1 => new Classification(classes[0], false, "standard-weapon-type-keyword"),
            _ => new Classification(null, true, "multiple-standard-weapon-type-keywords"),
        };
    }

    private static SelectionDecision Skip(string source) => new(
        RecordRuleAction.Exclude, null, null, false, source, null);

    public static bool AnimationMatchesClass(
        WeaponAnimationType animationType,
        WeaponBalanceClass weaponClass) => weaponClass switch
    {
        WeaponBalanceClass.Dagger => animationType == WeaponAnimationType.OneHandDagger,
        WeaponBalanceClass.Sword => animationType == WeaponAnimationType.OneHandSword,
        WeaponBalanceClass.Longsword => animationType == WeaponAnimationType.TwoHandSword,
        WeaponBalanceClass.WarAxe => animationType == WeaponAnimationType.OneHandAxe,
        WeaponBalanceClass.Mace => animationType == WeaponAnimationType.OneHandMace,
        WeaponBalanceClass.Greatsword => animationType == WeaponAnimationType.TwoHandSword,
        WeaponBalanceClass.Battleaxe or WeaponBalanceClass.Warhammer =>
            animationType == WeaponAnimationType.TwoHandAxe,
        _ => false,
    };

    public static bool HasCoherentClassShape(
        IWeaponGetter weapon,
        WeaponBalanceClass weaponClass,
        out string failure)
    {
        if (weapon.Data is null)
        {
            failure = "DNAM is absent";
            return false;
        }
        if (!AnimationMatchesClass(weapon.Data.AnimationType, weaponClass))
        {
            failure = $"animation is {weapon.Data.AnimationType}";
            return false;
        }
        var expectedSkill = weaponClass is WeaponBalanceClass.Dagger or
            WeaponBalanceClass.Sword or WeaponBalanceClass.WarAxe or WeaponBalanceClass.Mace
            ? Skill.OneHanded
            : Skill.TwoHanded;
        if (weapon.Data.Skill != expectedSkill)
        {
            failure = $"skill is {weapon.Data.Skill}, expected {expectedSkill}";
            return false;
        }
        if (weaponClass == WeaponBalanceClass.Longsword &&
            weapon.EquipmentType.FormKey != Program.BothHandsEquipType)
        {
            failure = $"equip type is {weapon.EquipmentType.FormKey}, expected BothHands {Program.BothHandsEquipType}";
            return false;
        }
        if (weaponClass == WeaponBalanceClass.Longsword &&
            !(weapon.Keywords ?? []).Any(link => link.FormKey == Program.GreatswordTypeKeyword))
        {
            failure = $"missing Greatsword type keyword {Program.GreatswordTypeKeyword}";
            return false;
        }
        failure = string.Empty;
        return true;
    }

    public static bool NeedsReview(IWeaponGetter weapon, WeaponBalanceClass weaponClass)
    {
        if (weapon.Data is null) return false;
        var specialKeyword = (weapon.Keywords ?? [])
            .Any(link => link.FormKey == Program.MagicDisallowEnchanting);
        return specialKeyword ||
            (BalanceRules.TryGetCanonicalSourceSpeed(weaponClass, out var canonical) &&
             Math.Abs(weapon.Data.Speed - canonical) > Program.SpeedTolerance);
    }

    private static bool IsNonPlayableWeapon(IWeaponGetter weapon)
    {
        if ((weapon.MajorFlags & Weapon.MajorFlag.NonPlayable) != 0)
        {
            return true;
        }
        return weapon.Data is { } data &&
            (data.Flags & WeaponData.Flag.NonPlayable) != 0;
    }
}

public sealed record Classification(
    WeaponBalanceClass? WeaponClass,
    bool Ambiguous,
    string Source);
