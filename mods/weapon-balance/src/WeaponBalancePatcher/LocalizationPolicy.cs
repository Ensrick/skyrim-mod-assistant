using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace WeaponBalancePatcher;

public static class LocalizationPolicy
{
    public static Language[] DetermineOutputLanguages(IEnumerable<IWeaponGetter> weapons)
    {
        var languages = weapons
            .SelectMany(EnumerateTranslatedFields)
            .SelectMany(value => value)
            .Select(pair => pair.Key)
            .ToHashSet();

        // Embedded strings are language-independent at runtime.  English is the
        // configured target language used to represent their original bytes in
        // Mutagen, and is replicated below when those records enter one localized
        // output alongside records carrying real translation tables.
        languages.Add(Language.English);
        return languages.OrderBy(value => value.ToString(), StringComparer.Ordinal).ToArray();
    }

    public static void PrepareForLocalizedOutput(
        IWeapon weapon,
        bool sourceUsesLocalization,
        IReadOnlyCollection<Language> outputLanguages)
    {
        if (sourceUsesLocalization)
        {
            // Enumerating each value resolves every lazy source sidecar before the
            // input load order is disposed and before the copied record is written.
            foreach (var value in EnumerateTranslatedFields(weapon))
            {
                _ = value.ToArray();
            }
            return;
        }

        ExpandEmbeddedFallback(weapon.Name, outputLanguages);
        ExpandEmbeddedFallback(weapon.Description, outputLanguages);
    }

    public static IEnumerable<ITranslatedStringGetter> EnumerateTranslatedFields(
        IWeaponGetter weapon)
    {
        if (weapon.Name is not null)
        {
            yield return weapon.Name;
        }
        if (weapon.Description is not null)
        {
            yield return weapon.Description;
        }
    }

    public static void RequireExactTranslatedSemantics(
        IWeaponGetter expected,
        IWeaponGetter actual,
        string context)
    {
        RequireExactTranslatedField(expected.Name, actual.Name, context, "Name");
        RequireExactTranslatedField(
            expected.Description, actual.Description, context, "Description");
    }

    public static void NormalizeEmptyBackingForRecordComparison(IWeapon weapon)
    {
        weapon.Name = NormalizeEmptyBacking(weapon.Name);
        weapon.Description = NormalizeEmptyBacking(weapon.Description);
    }

    private static void ExpandEmbeddedFallback(
        ITranslatedString? value,
        IReadOnlyCollection<Language> outputLanguages)
    {
        if (value is null)
        {
            return;
        }

        var embeddedValue = value.String;
        if (embeddedValue is null)
        {
            // Preserve a genuinely absent optional field.  In particular, do not
            // turn a missing DESC into explicit empty entries.
            return;
        }

        foreach (var language in outputLanguages)
        {
            value.Set(language, embeddedValue);
        }
    }

    private static void RequireExactTranslatedField(
        ITranslatedStringGetter? expected,
        ITranslatedStringGetter? actual,
        string context,
        string field)
    {
        Program.Require((expected is null) == (actual is null),
            $"{context}: localized {field} presence differs.");
        if (expected is null || actual is null)
        {
            return;
        }

        Program.Require(expected.TargetLanguage == actual.TargetLanguage,
            $"{context}: localized {field} target language differs.");
        Program.Require(string.Equals(expected.String, actual.String,
                StringComparison.Ordinal),
            $"{context}: localized {field} target value/null/empty semantics differ.");
        var expectedValues = expected
            .OrderBy(item => item.Key.ToString(), StringComparer.Ordinal)
            .ToArray();
        var actualValues = actual
            .OrderBy(item => item.Key.ToString(), StringComparer.Ordinal)
            .ToArray();
        Program.Require(expectedValues.Length == actualValues.Length &&
                expectedValues.Zip(actualValues).All(pair =>
                    pair.First.Key == pair.Second.Key &&
                    string.Equals(pair.First.Value, pair.Second.Value,
                        StringComparison.Ordinal)),
            $"{context}: localized {field} language/value map differs.");
    }

    private static TranslatedString? NormalizeEmptyBacking(TranslatedString? value)
    {
        if (value is null || value.Any())
        {
            return value;
        }

        // Localized ID 0 has no text entries.  Mutagen can expose NumLanguages=0
        // when it came from a BSA lookup and NumLanguages=1 after reading the same
        // ID 0 beside a generated empty loose table.  The exact semantic gate
        // above already distinguishes field absence, target language, null vs
        // explicit empty, and every language/value pair.  Rebuild only this empty
        // backing object on both comparison copies so full-record Equals is not
        // defeated by that lookup-provider count.
        return new TranslatedString(
            value.TargetLanguage,
            Array.Empty<KeyValuePair<Language, string>>());
    }

}
