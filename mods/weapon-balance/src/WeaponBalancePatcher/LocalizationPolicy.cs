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
}
