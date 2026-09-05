using System.Security.Cryptography;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Archives;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace WeaponBalancePatcher;

public static class LocalizationResourceInventory
{
    private static readonly StringsSource[] Sources =
    [
        StringsSource.Normal,
        StringsSource.IL,
        StringsSource.DL,
    ];

    public static InputLocalizationResourcesReceipt Create(
        string dataFolder,
        IEnumerable<LocalizationProviderSpec> sourceProviders)
    {
        var dataRoot = Path.GetFullPath(dataFolder);
        Program.Require(Directory.Exists(dataRoot),
            $"Localization resource Data folder is absent: {dataRoot}.");

        var providers = sourceProviders
            .GroupBy(item => item.Provider, StringComparer.OrdinalIgnoreCase)
            .Select(group =>
            {
                Program.Require(group.Count() == 1,
                    $"Duplicate localization provider specification: {group.Key}.");
                var item = group.Single();
                var modKey = ModKey.FromNameAndExtension(item.Provider);
                var languages = item.Languages
                    .Distinct()
                    .OrderBy(value => value.ToString(), StringComparer.Ordinal)
                    .ToArray();
                var candidates = languages
                    .SelectMany(language => Sources.Select(source => new LocalizationCandidate(
                        modKey.FileName.String,
                        NormalizeRelativePath(Path.Combine(
                            "Strings",
                            StringsUtility.GetFileName(
                                StringsLanguageFormat.FullName, modKey, language, source))),
                        language.ToString(),
                        source.ToString())))
                    .OrderBy(value => value.RelativePath, StringComparer.Ordinal)
                    .ToArray();
                return new PreparedProvider(modKey, languages, candidates);
            })
            .OrderBy(item => item.ModKey.FileName.String, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        var providerReceipts = providers.Select(item => new InputLocalizationProviderReceipt(
            item.ModKey.FileName.String,
            item.Languages.Select(value => value.ToString()).ToArray(),
            item.Candidates.Select(value => value.RelativePath).ToArray()))
            .ToArray();
        var looseFiles = new List<InputLocalizationLooseFileReceipt>();
        var archives = new List<InputLocalizationArchiveReceipt>();

        foreach (var provider in providers)
        {
            var candidateByPath = provider.Candidates.ToDictionary(
                item => item.RelativePath, StringComparer.OrdinalIgnoreCase);
            foreach (var candidate in provider.Candidates)
            {
                var fullPath = Path.Combine(
                    dataRoot,
                    candidate.RelativePath.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(fullPath))
                {
                    continue;
                }
                looseFiles.Add(new InputLocalizationLooseFileReceipt(
                    candidate.Provider,
                    candidate.RelativePath,
                    candidate.Language,
                    candidate.Source,
                    new FileInfo(fullPath).Length,
                    Sha256File(fullPath)));
            }

            var applicableArchives = Archive.GetApplicableArchivePaths(
                    GameRelease.SkyrimSE,
                    new DirectoryPath(dataRoot),
                    provider.ModKey,
                    returnEmptyIfMissing: true)
                .Select(path => Path.GetFullPath(path.Path))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray();
            for (var order = 0; order < applicableArchives.Length; order++)
            {
                var archivePath = applicableArchives[order];
                var reader = Archive.CreateReader(
                    GameRelease.SkyrimSE, new FilePath(archivePath));
                var matchingEntries = reader.Files
                    .Select(file => new
                    {
                        File = file,
                        RelativePath = NormalizeRelativePath(file.Path),
                    })
                    .Where(item => candidateByPath.ContainsKey(item.RelativePath))
                    .Select(item =>
                    {
                        var candidate = candidateByPath[item.RelativePath];
                        var bytes = item.File.GetBytes();
                        return new InputLocalizationArchiveEntryReceipt(
                            item.RelativePath,
                            candidate.Language,
                            candidate.Source,
                            item.File.Size,
                            Sha256Bytes(bytes));
                    })
                    .OrderBy(item => item.RelativePath, StringComparer.Ordinal)
                    .ToArray();
                if (matchingEntries.Length == 0)
                {
                    continue;
                }

                archives.Add(new InputLocalizationArchiveReceipt(
                    provider.ModKey.FileName.String,
                    NormalizeRelativePath(Path.GetRelativePath(dataRoot, archivePath)),
                    order,
                    new FileInfo(archivePath).Length,
                    Sha256File(archivePath),
                    matchingEntries));
            }
        }

        var orderedLoose = looseFiles
            .OrderBy(item => item.Provider, StringComparer.OrdinalIgnoreCase)
            .ThenBy(item => item.RelativePath, StringComparer.Ordinal)
            .ToArray();
        var orderedArchives = archives
            .OrderBy(item => item.Provider, StringComparer.OrdinalIgnoreCase)
            .ThenBy(item => item.ApplicableOrder)
            .ThenBy(item => item.RelativePath, StringComparer.Ordinal)
            .ToArray();
        var resolutions = providers
            .SelectMany(provider => provider.Candidates.Select(candidate =>
            {
                var loose = orderedLoose
                    .Where(item => item.Provider.Equals(candidate.Provider,
                            StringComparison.OrdinalIgnoreCase) &&
                        item.RelativePath.Equals(candidate.RelativePath,
                            StringComparison.OrdinalIgnoreCase))
                    .ToArray();
                var archiveMatches = orderedArchives
                    .Where(item => item.Provider.Equals(candidate.Provider,
                            StringComparison.OrdinalIgnoreCase) &&
                        item.MatchedEntries.Any(entry => entry.RelativePath.Equals(
                            candidate.RelativePath, StringComparison.OrdinalIgnoreCase)))
                    .ToArray();
                var available = loose.Select(item => $"loose:{item.RelativePath}")
                    .Concat(archiveMatches.Select(item => $"archive:{item.RelativePath}"))
                    .OrderBy(item => item, StringComparer.Ordinal)
                    .ToArray();
                var resolution = loose.Length > 0
                    ? "loose"
                    : archiveMatches.Length switch
                    {
                        0 => "absent",
                        1 => "archive",
                        _ => "ambiguous-archives",
                    };
                var selected = resolution switch
                {
                    "loose" => $"loose:{loose.Single().RelativePath}",
                    "archive" => $"archive:{archiveMatches.Single().RelativePath}",
                    _ => null,
                };
                return new InputLocalizationResolutionReceipt(
                    candidate.Provider,
                    candidate.RelativePath,
                    candidate.Language,
                    candidate.Source,
                    resolution,
                    selected,
                    available);
            }))
            .OrderBy(item => item.Provider, StringComparer.OrdinalIgnoreCase)
            .ThenBy(item => item.RelativePath, StringComparer.Ordinal)
            .ToArray();

        var ambiguous = resolutions.Where(item => item.Resolution == "ambiguous-archives")
            .ToArray();
        Program.Require(ambiguous.Length == 0,
            "Localized input resource has multiple applicable BSA providers and no loose winner: " +
            string.Join("; ", ambiguous.Take(20).Select(item =>
                $"{item.Provider}:{item.RelativePath} [{string.Join(", ", item.AvailableContainers)}]")) +
            (ambiguous.Length > 20 ? $"; and {ambiguous.Length - 20} more" : string.Empty));
        foreach (var provider in providers)
        {
            foreach (var language in provider.Languages.Select(value => value.ToString()))
            {
                Program.Require(resolutions.Any(item =>
                        item.Provider.Equals(provider.ModKey.FileName.String,
                            StringComparison.OrdinalIgnoreCase) &&
                        item.Language == language && item.Resolution != "absent"),
                    $"No physical localization table was found for " +
                    $"{provider.ModKey.FileName.String} language {language}.");
            }
        }

        var payload = new InputLocalizationResourcesPayload(
            SchemaVersion: 1,
            Providers: providerReceipts,
            LooseFiles: orderedLoose,
            Archives: orderedArchives,
            Resolutions: resolutions);
        var canonicalBytes = JsonSerializer.SerializeToUtf8Bytes(payload, Program.JsonOptions);
        return new InputLocalizationResourcesReceipt(
            payload.SchemaVersion,
            payload.Providers,
            payload.LooseFiles,
            payload.Archives,
            payload.Resolutions,
            Sha256Bytes(canonicalBytes));
    }

    private static string NormalizeRelativePath(string path) =>
        path.Replace('\\', '/').TrimStart('/');

    private static string Sha256File(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream));
    }

    private static string Sha256Bytes(ReadOnlySpan<byte> bytes) =>
        Convert.ToHexString(SHA256.HashData(bytes));

    private sealed record PreparedProvider(
        ModKey ModKey,
        IReadOnlyList<Language> Languages,
        IReadOnlyList<LocalizationCandidate> Candidates);

    private sealed record LocalizationCandidate(
        string Provider,
        string RelativePath,
        string Language,
        string Source);

    private sealed record InputLocalizationResourcesPayload(
        int SchemaVersion,
        IReadOnlyList<InputLocalizationProviderReceipt> Providers,
        IReadOnlyList<InputLocalizationLooseFileReceipt> LooseFiles,
        IReadOnlyList<InputLocalizationArchiveReceipt> Archives,
        IReadOnlyList<InputLocalizationResolutionReceipt> Resolutions);
}

public sealed record LocalizationProviderSpec(
    string Provider,
    IReadOnlyList<Language> Languages);

public sealed record InputLocalizationResourcesReceipt(
    int SchemaVersion,
    IReadOnlyList<InputLocalizationProviderReceipt> Providers,
    IReadOnlyList<InputLocalizationLooseFileReceipt> LooseFiles,
    IReadOnlyList<InputLocalizationArchiveReceipt> Archives,
    IReadOnlyList<InputLocalizationResolutionReceipt> Resolutions,
    string Sha256);

public sealed record InputLocalizationProviderReceipt(
    string Provider,
    IReadOnlyList<string> Languages,
    IReadOnlyList<string> CandidateRelativePaths);

public sealed record InputLocalizationLooseFileReceipt(
    string Provider,
    string RelativePath,
    string Language,
    string Source,
    long Bytes,
    string Sha256);

public sealed record InputLocalizationArchiveReceipt(
    string Provider,
    string RelativePath,
    int ApplicableOrder,
    long Bytes,
    string Sha256,
    IReadOnlyList<InputLocalizationArchiveEntryReceipt> MatchedEntries);

public sealed record InputLocalizationArchiveEntryReceipt(
    string RelativePath,
    string Language,
    string Source,
    uint Bytes,
    string Sha256);

public sealed record InputLocalizationResolutionReceipt(
    string Provider,
    string RelativePath,
    string Language,
    string Source,
    string Resolution,
    string? SelectedContainer,
    IReadOnlyList<string> AvailableContainers);
