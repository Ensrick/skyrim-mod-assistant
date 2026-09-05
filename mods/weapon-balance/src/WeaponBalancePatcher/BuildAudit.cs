using System.Security.Cryptography;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace WeaponBalancePatcher;

internal static class BuildAudit
{
    private static readonly IReadOnlyDictionary<FormKey, string> KeywordFixtures =
        new Dictionary<FormKey, string>
        {
            [FormKey.Factory("01E713:Skyrim.esm")] = "WeapTypeDagger",
            [FormKey.Factory("01E711:Skyrim.esm")] = "WeapTypeSword",
            [FormKey.Factory("01E712:Skyrim.esm")] = "WeapTypeWarAxe",
            [FormKey.Factory("01E714:Skyrim.esm")] = "WeapTypeMace",
            [FormKey.Factory("06D931:Skyrim.esm")] = "WeapTypeGreatsword",
            [FormKey.Factory("06D932:Skyrim.esm")] = "WeapTypeBattleaxe",
            [FormKey.Factory("06D930:Skyrim.esm")] = "WeapTypeWarhammer",
            [Program.SteelMaterialKeyword] = "WeapMaterialSteel",
        };

    public static int Run(
        string dataFolder,
        string loadOrderFile,
        string pluginPath,
        string settingsPath,
        string reportPath,
        string outputPath)
    {
        var settings = ReadJson<Settings>(settingsPath);
        var profile = settings.ToProfile();
        profile.Validate();
        var rules = Policy.ParseRecordRules(settings.RecordRules);
        var report = ReadJson<SelectionReport>(reportPath);
        Program.Require(report.SchemaVersion == 2, "Selection report schema is not 2.");
        Program.Require(report.OutputPlugin == Program.OutputPlugin,
            $"Selection report output is {report.OutputPlugin}, expected {Program.OutputPlugin}.");

        var modKeys = LoadOrderFile.Read(loadOrderFile, excludeOutput: true);
        Program.Require(!modKeys.Any(key => key == ModKey.FromNameAndExtension(Program.OutputPlugin)),
            "Build-audit input load order must exclude WeaponBalancePatch.esp.");
        using var loadOrder = ImportLoadOrder(dataFolder, modKeys);
        using var linkCache = loadOrder.ToImmutableLinkCache();
        using var plugin = SkyrimMod.CreateFromBinaryOverlay(pluginPath, SkyrimRelease.SkyrimSE);

        AuditKeywordFixtures(loadOrder);
        Program.Require(plugin.ModKey == ModKey.FromNameAndExtension(Program.OutputPlugin),
            $"Plugin key is {plugin.ModKey}, expected {Program.OutputPlugin}.");
        Program.Require(plugin.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small),
            "Plugin is not ESL-flagged.");
        var lightPluginsBeforeOutput = loadOrder.ListedOrder.Count(listing =>
            listing.Mod?.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small) == true);
        Program.Require(lightPluginsBeforeOutput + 1 <= 4096,
            $"Adding the output would exceed the 4,096 light-plugin index space " +
            $"({lightPluginsBeforeOutput} already loaded).");
        var allRecords = plugin.EnumerateMajorRecords().ToArray();
        Program.Require(allRecords.All(record => record is IWeaponGetter),
            "Output contains a record type other than WEAP.");
        Program.Require(allRecords.All(record => record.FormKey.ModKey != plugin.ModKey),
            "Speed-only output may not allocate new/light FormIDs.");
        Program.Require(!allRecords.Any(record => record.IsDeleted),
            "Output contains a deleted WEAP record.");

        var contexts = loadOrder.PriorityOrder
            .WinningContextOverrides<ISkyrimMod, ISkyrimModGetter, IWeapon, IWeaponGetter>(linkCache)
            .ToArray();
        var contextByKey = contexts.ToDictionary(context => context.Record.FormKey);
        var recomputed = new Dictionary<FormKey, (IWeaponGetter Source, SelectionDecision Decision)>();
        var resolvedRules = new HashSet<FormKey>();
        var freshRows = new List<SelectionReportRow>();
        var freshReviewCandidates = new List<ReviewCandidate>();
        var freshClassCounts = Enum.GetValues<WeaponBalanceClass>()
            .ToDictionary(value => value, _ => new ClassCounts());
        var freshDirectChanged = 0;
        var freshDirectAlreadyTarget = 0;
        foreach (var context in contexts)
        {
            var decision = Policy.Plan(
                context.Record, context.ModKey, settings, profile, rules);
            if (decision.ExplicitRule)
            {
                resolvedRules.Add(context.Record.FormKey);
            }
            var row = SelectionReportRow.From(context.Record, context.ModKey, decision);
            freshRows.Add(row);
            if (decision.WeaponClass is { } classified)
            {
                freshClassCounts[classified].Classified++;
            }
            if (!decision.ExplicitRule && decision.WeaponClass is { } reviewClass &&
                decision.TargetSpeed is { } reviewTarget &&
                Policy.NeedsReview(context.Record, reviewClass))
            {
                freshReviewCandidates.Add(Program.CreateReviewCandidate(
                    context.Record, context.ModKey, reviewClass, reviewTarget));
            }
            if (decision.TargetSpeed is { } target && context.Record.Data is { } data &&
                Math.Abs(data.Speed - target) > Program.SpeedTolerance)
            {
                recomputed.Add(context.Record.FormKey, (context.Record, decision));
                if (decision.WeaponClass is { } changedClass)
                {
                    freshClassCounts[changedClass].Changed++;
                }
                else
                {
                    freshDirectChanged++;
                }
            }
            else if (decision.TargetSpeed is not null)
            {
                if (decision.WeaponClass is { } targetClass)
                {
                    freshClassCounts[targetClass].AlreadyTarget++;
                }
                else
                {
                    freshDirectAlreadyTarget++;
                }
            }
        }
        Program.Require(resolvedRules.SetEquals(rules.Keys),
            "One or more explicit record rules do not resolve against the audited inputs.");

        var pluginWeapons = plugin.Weapons.ToDictionary(weapon => weapon.FormKey);
        var reportKeys = report.Patched.Select(row => FormKey.Factory(row.FormKey)).ToHashSet();
        Program.Require(report.Rows.Count == contexts.Length &&
                report.Rows.Select(row => FormKey.Factory(row.FormKey)).ToHashSet()
                    .SetEquals(contextByKey.Keys),
            "Selection-report coverage differs from the complete winning WEAP set.");
        Program.Require(report.ExplicitRulesConfigured == rules.Count &&
                report.ExplicitRulesResolved == resolvedRules.Count,
            "Selection-report explicit-rule counts differ from settings/current inputs.");
        Program.Require(reportKeys.SetEquals(recomputed.Keys),
            "Selection-report patched FormKey set differs from a fresh policy evaluation.");
        Program.Require(pluginWeapons.Keys.ToHashSet().SetEquals(recomputed.Keys),
            "Output WEAP FormKey set differs from a fresh policy evaluation.");

        foreach (var context in contexts)
        {
            var row = report.Rows.Single(item =>
                FormKey.Factory(item.FormKey) == context.Record.FormKey);
            var decision = Policy.Plan(
                context.Record, context.ModKey, settings, profile, rules);
            Program.Require(
                row.WinningProvider.Equals(context.ModKey.FileName.String,
                    StringComparison.OrdinalIgnoreCase) &&
                row.Action == decision.Action.ToString() &&
                row.Source == decision.Source &&
                row.WeaponClass == decision.WeaponClass?.ToString() &&
                NullableSpeedEqual(row.SourceSpeed, context.Record.Data?.Speed) &&
                row.SourceDamage == context.Record.BasicStats?.Damage &&
                NullableSpeedEqual(row.TargetSpeed, decision.TargetSpeed) &&
                row.ExplicitRule == decision.ExplicitRule &&
                row.Reason == decision.Reason &&
                row.Changed == (decision.TargetSpeed is { } target &&
                    context.Record.Data is { } data &&
                    Math.Abs(data.Speed - target) > Program.SpeedTolerance),
                $"{context.Record.FormKey}: selection-report row differs from the fresh winning record/policy.");
        }

        var freshRowsOrdered = freshRows.OrderBy(row => row.FormKey,
            StringComparer.OrdinalIgnoreCase).ToArray();
        Program.Require(JsonSerializer.Serialize(report.Rows, Program.JsonOptions) ==
                JsonSerializer.Serialize(freshRowsOrdered, Program.JsonOptions),
            "Selection-report full row array differs from fresh evaluation/order.");
        var freshPatched = freshRowsOrdered.Where(row => row.Changed).ToArray();
        Program.Require(JsonSerializer.Serialize(report.Patched, Program.JsonOptions) ==
                JsonSerializer.Serialize(freshPatched, Program.JsonOptions),
            "Selection-report Patched rows differ from fresh evaluation/order.");
        var freshReviewOrdered = freshReviewCandidates.OrderBy(row => row.FormKey,
            StringComparer.OrdinalIgnoreCase).ToArray();
        Program.Require(JsonSerializer.Serialize(report.ReviewCandidates, Program.JsonOptions) ==
                JsonSerializer.Serialize(freshReviewOrdered, Program.JsonOptions),
            "Selection-report review-candidate rows differ from fresh evaluation/order.");
        foreach (var weaponClass in Enum.GetValues<WeaponBalanceClass>())
        {
            if (!report.ClassCounts.TryGetValue(weaponClass.ToString(), out var actualCount) ||
                actualCount is null)
            {
                throw new InvalidOperationException(
                    $"Selection report has no {weaponClass} class count.");
            }
            var expectedCount = freshClassCounts[weaponClass];
            Program.Require(actualCount.Classified == expectedCount.Classified &&
                    actualCount.Changed == expectedCount.Changed &&
                    actualCount.AlreadyTarget == expectedCount.AlreadyTarget,
                $"Selection report {weaponClass} counts differ from fresh evaluation.");
        }
        Program.Require(report.ClassCounts.Count == freshClassCounts.Count &&
                report.DirectSpeedChanged == freshDirectChanged &&
                report.DirectSpeedAlreadyTarget == freshDirectAlreadyTarget,
            "Selection-report class/direct-speed summary differs from fresh evaluation.");

        foreach (var (formKey, expected) in recomputed)
        {
            var actual = pluginWeapons[formKey];
            var target = expected.Decision.TargetSpeed!.Value;
            Program.Require(actual.Data is not null &&
                    Math.Abs(actual.Data.Speed - target) <= Program.SpeedTolerance,
                $"{formKey}: output speed {actual.Data?.Speed} differs from {target}.");

            // Exhaustive semantic only-Speed gate: create the exact record expected by
            // copying the current winner, change WEAP.DNAM.Speed (Mutagen Data.Speed),
            // then compare every Mutagen field.
            var expectedRecord = expected.Source.DeepCopy();
            Program.ApplySpeedOnly(expectedRecord, target);
            Program.Require(expectedRecord.Equals(actual),
                $"{formKey}: output differs from the winning input in a field other than WEAP.DNAM.Speed.");

            var row = report.Patched.Single(item =>
                FormKey.Factory(item.FormKey) == formKey);
            Program.Require(row.Changed && row.TargetSpeed is { } reportedTarget &&
                    Math.Abs(reportedTarget - target) <= Program.SpeedTolerance &&
                    row.SourceSpeed is { } sourceSpeed &&
                    Math.Abs(sourceSpeed - expected.Source.Data!.Speed) <= Program.SpeedTolerance,
                $"{formKey}: selection-report speeds or changed flag differ from the fresh evaluation.");
        }

        var actualMasters = plugin.ModHeader.MasterReferences.Select(reference => reference.Master).ToArray();
        var derivedMasters = allRecords
            .Select(record => record.FormKey.ModKey)
            .Concat(allRecords.SelectMany(record => record.EnumerateFormLinks())
                .Where(link => !link.FormKey.IsNull)
                .Select(link => link.FormKey.ModKey))
            .Where(key => key != plugin.ModKey)
            .ToHashSet();
        Program.Require(actualMasters.ToHashSet().SetEquals(derivedMasters),
            "Output master set is not minimal/exact for its WEAP records and links.");
        Program.Require(actualMasters.Length <= 253,
            $"Output has {actualMasters.Length} masters; Skyrim's regular master index space is exhausted.");

        var linksChecked = 0;
        var unresolvedLinks = new List<string>();
        foreach (var record in allRecords)
        {
            foreach (var link in record.EnumerateFormLinks())
            {
                if (link.FormKey.IsNull) continue;
                linksChecked++;
                if (!linkCache.TryResolve(link.FormKey, link.Type, out _))
                {
                    unresolvedLinks.Add(
                        $"{record.FormKey} -> {link.FormKey} ({link.Type.FullName})");
                }
            }
        }
        Program.Require(unresolvedLinks.Count == 0,
            "Output contains unresolved FormLinks: " + string.Join("; ", unresolvedLinks.Take(20)) +
            (unresolvedLinks.Count > 20 ? $"; and {unresolvedLinks.Count - 20} more" : string.Empty));

        var inputBinaries = modKeys.Select(key =>
        {
            var path = Path.Combine(dataFolder, key.FileName.String);
            Program.Require(File.Exists(path), $"Input plugin binary is absent: {key}.");
            return new
            {
                plugin = key.FileName.String,
                sha256 = Sha256(path),
            };
        }).ToArray();

        var receipt = new
        {
            schemaVersion = 2,
            status = "pass",
            mode = "candidate-build",
            plugin = Program.OutputPlugin,
            eslFlagged = true,
            ownLightFormCount = 0,
            lightPluginsBeforeOutput,
            lightPluginsWithOutput = lightPluginsBeforeOutput + 1,
            records = allRecords.Length,
            recordTypes = new { WEAP = allRecords.Length },
            masters = actualMasters.Select(key => key.FileName.String).ToArray(),
            mastersCount = actualMasters.Length,
            explicitRules = rules.Count,
            selectionRows = report.Rows.Count,
            reviewCandidates = report.ReviewCandidates.Count,
            pluginSha256 = Sha256(pluginPath),
            settingsSha256 = Sha256(settingsPath),
            selectionReportSha256 = Sha256(reportPath),
            onlySpeedSemanticComparison = true,
            linksChecked,
            unresolvedLinks = 0,
            keywordFixtures = KeywordFixtures.ToDictionary(
                pair => pair.Key.ToString(), pair => pair.Value),
            inputBinaries,
        };
        WriteResult(outputPath, receipt);
        Console.WriteLine(
            $"PASS: {allRecords.Length} WEAP overrides, ESL flag, zero owned light forms, " +
            $"{actualMasters.Length} exact masters, complete selection coverage, and semantic only-Speed equality.");
        return 0;
    }

    public static int RunFinalWinners(
        string dataFolder,
        string loadOrderFile,
        string settingsPath,
        string reportPath,
        string outputPath)
    {
        var settings = ReadJson<Settings>(settingsPath);
        settings.ToProfile().Validate();
        Policy.ParseRecordRules(settings.RecordRules);
        var report = ReadJson<SelectionReport>(reportPath);
        var modKeys = LoadOrderFile.Read(loadOrderFile, excludeOutput: false);
        var outputKey = ModKey.FromNameAndExtension(Program.OutputPlugin);
        Program.Require(modKeys.Count(key => key == outputKey) == 1,
            "Final-winner load order must contain WeaponBalancePatch.esp exactly once.");
        using var loadOrder = ImportLoadOrder(dataFolder, modKeys);
        using var linkCache = loadOrder.ToImmutableLinkCache();
        var winners = loadOrder.PriorityOrder
            .WinningContextOverrides<ISkyrimMod, ISkyrimModGetter, IWeapon, IWeaponGetter>(linkCache)
            .ToDictionary(context => context.Record.FormKey);
        var failures = new List<string>();
        foreach (var row in report.Rows.Where(item =>
            item.TargetSpeed is not null || item.Action == RecordRuleAction.Preserve.ToString()))
        {
            var formKey = FormKey.Factory(row.FormKey);
            if (!winners.TryGetValue(formKey, out var winner))
            {
                failures.Add($"{formKey}: no final winner");
                continue;
            }
            var shouldBeOutput = row.Changed;
            var expectedProvider = shouldBeOutput ? outputKey.FileName.String : row.WinningProvider;
            if (!winner.ModKey.FileName.String.Equals(expectedProvider,
                    StringComparison.OrdinalIgnoreCase))
            {
                failures.Add(
                    $"{formKey}: final provider is {winner.ModKey}, expected {expectedProvider}");
                continue;
            }
            var expectedSpeed = row.Action == RecordRuleAction.Preserve.ToString()
                ? row.SourceSpeed
                : row.TargetSpeed;
            if (expectedSpeed is not { } expected || winner.Record.Data is not { } data ||
                Math.Abs(data.Speed - expected) > Program.SpeedTolerance)
            {
                failures.Add($"{formKey}: final speed is {winner.Record.Data?.Speed}, expected {expectedSpeed}");
            }
        }
        Program.Require(failures.Count == 0,
            "Final winning-speed gate failed: " + string.Join("; ", failures.Take(20)) +
            (failures.Count > 20 ? $"; and {failures.Count - 20} more" : string.Empty));

        var result = new
        {
            schemaVersion = 2,
            status = "pass",
            mode = "installed-final-winners",
            plugin = Program.OutputPlugin,
            checkedRecords = report.Rows.Count(item =>
                item.TargetSpeed is not null || item.Action == RecordRuleAction.Preserve.ToString()),
            changedRecordsFinalProvider = Program.OutputPlugin,
            selectionReportSha256 = Sha256(reportPath),
        };
        WriteResult(outputPath, result);
        Console.WriteLine(
            $"PASS: all target-speed and named-preserve rows have their expected final providers and exact final speeds.");
        return 0;
    }

    private static ILoadOrder<IModListing<ISkyrimModGetter>> ImportLoadOrder(
        string dataFolder,
        IReadOnlyList<ModKey> modKeys) =>
        LoadOrder.Import<ISkyrimModGetter>(
            new DirectoryPath(dataFolder),
            modKeys,
            GameRelease.SkyrimSE,
            factory: modPath => SkyrimMod.CreateFromBinaryOverlay(
                modPath.Path, SkyrimRelease.SkyrimSE));

    private static void AuditKeywordFixtures(
        ILoadOrderGetter<IModListingGetter<ISkyrimModGetter>> loadOrder)
    {
        var skyrimKey = ModKey.FromNameAndExtension("Skyrim.esm");
        var skyrim = loadOrder.ListedOrder.Single(listing => listing.ModKey == skyrimKey).Mod
            ?? throw new InvalidOperationException("Skyrim.esm is unavailable in the audited input.");
        foreach (var (formKey, expectedEditorId) in KeywordFixtures)
        {
            var keyword = skyrim.Keywords.SingleOrDefault(record => record.FormKey == formKey)
                ?? throw new InvalidOperationException($"Keyword fixture {formKey} is absent from Skyrim.esm.");
            Program.Require(keyword.EditorID == expectedEditorId,
                $"Keyword fixture {formKey} is {keyword.EditorID}, expected {expectedEditorId}.");
        }
        Program.Require(!Program.StandardKeywords.ContainsKey(Program.SteelMaterialKeyword),
            "WeapMaterialSteel entered the standard weapon-type keyword map.");
    }

    private static T ReadJson<T>(string path)
    {
        var value = JsonSerializer.Deserialize<T>(File.ReadAllText(path), new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true,
        });
        return value ?? throw new InvalidOperationException($"Could not deserialize {path}.");
    }

    private static string Sha256(string path) =>
        Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));

    private static bool NullableSpeedEqual(float? left, float? right) =>
        left is null && right is null ||
        left is { } leftValue && right is { } rightValue &&
        Math.Abs(leftValue - rightValue) <= Program.SpeedTolerance;

    private static void WriteResult(string outputPath, object result)
    {
        var json = JsonSerializer.Serialize(result, Program.JsonOptions);
        if (string.IsNullOrWhiteSpace(outputPath) || outputPath == "-")
        {
            Console.WriteLine(json);
            return;
        }
        var fullPath = Path.GetFullPath(outputPath);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);
        File.WriteAllText(fullPath, json);
    }
}

internal static class LoadOrderFile
{
    public static ModKey[] Read(string loadOrderFile, bool excludeOutput)
    {
        var normalized = File.ReadAllLines(loadOrderFile)
            .Select(line => line.Trim())
            .Where(line => line.Length > 0 && !line.StartsWith('#'))
            .ToArray();
        var unstarred = normalized.Where(line => !line.StartsWith('*')).ToArray();
        if (unstarred.Length > 0)
        {
            throw new InvalidOperationException(
                "Audit load-order files must be normalized enabled-only files; unstarred entries: " +
                string.Join(", ", unstarred.Take(20)));
        }
        var listed = normalized
            .Select(line => ModKey.FromNameAndExtension(line.TrimStart('*')))
            .Where(key => !excludeOutput ||
                !string.Equals(key.FileName.String, Program.OutputPlugin,
                    StringComparison.OrdinalIgnoreCase));
        return new[] { "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm" }
            .Select(name => ModKey.FromNameAndExtension(name))
            .Concat(listed)
            .Distinct()
            .ToArray();
    }
}
