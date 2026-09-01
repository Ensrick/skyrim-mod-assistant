using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Ensrick.GeneralCompatibilityPatcher;

internal static class SelfTest
{
    private static readonly IReadOnlySet<string> IntentionalItms = new HashSet<string>(
        [
            "01A276:Skyrim.esm",
            "02EE41:Skyrim.esm",
            "037EE9:Skyrim.esm",
        ],
        StringComparer.OrdinalIgnoreCase);

    public static int Run(
        string? decisionsPath = null,
        string? expectedValuesPath = null,
        string? manifestPath = null,
        string? sourceBuildPath = null,
        string? spriggitPath = null)
    {
        try
        {
            ValidateCompiledPolicy();
            if (decisionsPath is not null || expectedValuesPath is not null || manifestPath is not null ||
                sourceBuildPath is not null || spriggitPath is not null)
            {
                Require(
                    new[] { decisionsPath, expectedValuesPath, manifestPath, sourceBuildPath, spriggitPath }
                        .All(path => path is not null),
                    "fixture validation requires decisions, expected values, manifest, source-build, and Spriggit paths");
                ValidateFixtures(
                    decisionsPath!,
                    expectedValuesPath!,
                    manifestPath!,
                    sourceBuildPath!,
                    spriggitPath!);
            }

            Console.WriteLine(
                decisionsPath is null
                    ? "PASS: Decision A target and field-ownership invariants."
                    : "PASS: Decision A policy, evidence, provenance, and Spriggit fixture invariants.");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine($"SELF-TEST FAILED: {exception.Message}");
            return 1;
        }
    }

    private static void ValidateCompiledPolicy()
    {
        Require(Program.WorldspaceTargets.Count == 12, "expected 12 WRLD targets");
        Require(Program.CellTargets.Count == 2, "expected 2 CELL targets");

        var allKeys = Program.WorldspaceTargets.Select(target => target.FormKey)
            .Concat(Program.CellTargets.Select(target => target.FormKey))
            .ToArray();
        Require(allKeys.Distinct().Count() == 14, "target FormKeys must be unique");

        Require(
            Program.WorldspaceTargets.Count(target => target.SourcePlugin == Program.LuxOrbisCs) == 8,
            "expected eight Lux Orbis CS WRLD targets");
        Require(
            Program.WorldspaceTargets.Count(target => target.SourcePlugin == Program.Bruma) == 4,
            "expected four Bruma WRLD targets");
        Require(
            Program.CellTargets.All(target => target.SourcePlugin == Program.LuxOrbisCs),
            "both CELL locations must come from Lux Orbis CS");
        Require(Program.RequiredMasters.Count == 7, "expected seven hard masters");
        Require(
            Program.RequiredMasters[4].FileName.String == Program.LuxOrbisCs,
            "Lux Orbis CS must be an explicit hard master");

        var allowed = Program.WorldspaceFields.Flags |
                      Program.WorldspaceFields.MaxHeight |
                      Program.WorldspaceFields.Parent |
                      Program.WorldspaceFields.Climate |
                      Program.WorldspaceFields.Location |
                      Program.WorldspaceFields.ObjectBoundsMax;
        Require(
            Program.WorldspaceTargets.All(target => target.Fields != Program.WorldspaceFields.None),
            "every WRLD target must own at least one field");
        Require(
            Program.WorldspaceTargets.All(target => (target.Fields & ~allowed) == 0),
            "WRLD field ownership must stay inside the approved allowlist");
    }

    private static void ValidateFixtures(
        string decisionsPath,
        string expectedValuesPath,
        string manifestPath,
        string sourceBuildPath,
        string spriggitPath)
    {
        foreach (var path in new[] { decisionsPath, expectedValuesPath, manifestPath, sourceBuildPath })
        {
            Require(File.Exists(path), $"required fixture does not exist: {path}");
        }
        Require(Directory.Exists(spriggitPath), $"Spriggit fixture does not exist: {spriggitPath}");

        using var decisions = JsonDocument.Parse(File.ReadAllText(decisionsPath));
        using var expected = JsonDocument.Parse(File.ReadAllText(expectedValuesPath));
        using var manifest = JsonDocument.Parse(File.ReadAllText(manifestPath));
        using var sourceBuild = JsonDocument.Parse(File.ReadAllText(sourceBuildPath));

        var compiled = Program.WorldspaceTargets.ToDictionary(
            target => target.FormKey.ToString(),
            target => new TargetPolicy(
                target.EditorId,
                "Worldspace",
                target.SourcePlugin,
                Enum.GetValues<Program.WorldspaceFields>()
                    .Where(field => field != Program.WorldspaceFields.None && target.Fields.HasFlag(field))
                    .Select(field => field.ToString())
                    .ToHashSet(StringComparer.Ordinal)),
            StringComparer.OrdinalIgnoreCase);
        foreach (var target in Program.CellTargets)
        {
            compiled.Add(
                target.FormKey.ToString(),
                new TargetPolicy(
                    target.EditorId,
                    "Cell",
                    target.SourcePlugin,
                    new HashSet<string>(["Location"], StringComparer.Ordinal)));
        }

        var recommended = decisions.RootElement.GetProperty("recommendedPlugin");
        var decisionTargets = new Dictionary<string, TargetPolicy>(StringComparer.OrdinalIgnoreCase);
        AddDecisionTargets(
            decisionTargets,
            recommended.GetProperty("worldspaceFieldsFromLuxOrbisCs"),
            "Worldspace",
            Program.LuxOrbisCs);
        AddDecisionTargets(
            decisionTargets,
            recommended.GetProperty("worldspaceFieldsFromBruma"),
            "Worldspace",
            Program.Bruma);
        AddDecisionTargets(
            decisionTargets,
            recommended.GetProperty("cellFieldsFromLuxOrbisCs"),
            "Cell",
            Program.LuxOrbisCs);
        RequirePoliciesEqual(compiled, decisionTargets, "compiled policy and decisions.json");

        var expectedRoot = expected.RootElement;
        var expectedMasters = expectedRoot.GetProperty("requiredHardMasters")
            .EnumerateArray()
            .Select(item => item.GetString()!)
            .ToArray();
        var compiledMasters = Program.RequiredMasters.Select(master => master.FileName.String).ToArray();
        Require(expectedMasters.SequenceEqual(compiledMasters, StringComparer.Ordinal),
            "expected-values hard masters differ from compiled hard masters");

        var expectedTargets = new Dictionary<string, TargetPolicy>(StringComparer.OrdinalIgnoreCase);
        foreach (var target in expectedRoot.GetProperty("targets").EnumerateArray())
        {
            var owned = target.GetProperty("ownedValues").EnumerateObject()
                .Select(property => property.Name)
                .ToHashSet(StringComparer.Ordinal);
            expectedTargets.Add(
                target.GetProperty("formKey").GetString()!,
                new TargetPolicy(
                    target.GetProperty("editorId").GetString()!,
                    target.GetProperty("recordType").GetString()!,
                    target.GetProperty("sourcePlugin").GetString()!,
                    owned));
        }
        RequirePoliciesEqual(compiled, expectedTargets, "compiled policy and expected-values.json");

        var expectedItms = expectedRoot.GetProperty("intentionalIdenticalToMasterOverrides")
            .EnumerateArray()
            .Select(item => item.GetProperty("formKey").GetString()!)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        Require(expectedItms.SetEquals(IntentionalItms), "intentional ITM fixture differs from approved set");
        ValidateRelationship(expectedRoot.GetProperty("relationship"), "expected-values relationship");

        // Git may materialize JSON with CRLF on Windows even though the evidence
        // hash was recorded from the repository's canonical LF form. Normalize
        // line endings so this provenance check is stable across checkout policy.
        var expectedHash = CanonicalTextSha256(expectedValuesPath);
        var manifestRoot = manifest.RootElement;
        Require(
            manifestRoot.GetProperty("expectedValues").GetProperty("sha256").GetString() == expectedHash,
            "manifest expected-values hash is stale");
        Require(
            manifestRoot.GetProperty("spriggit").GetProperty("treeSha256").GetString() == TreeSha256(spriggitPath),
            "manifest Spriggit tree hash is stale");
        ValidateOutput(manifestRoot.GetProperty("output"), compiledMasters);
        ValidateRelationship(manifestRoot.GetProperty("relationship"), "manifest relationship");

        var sourceRoot = sourceBuild.RootElement;
        Require(sourceRoot.GetProperty("outputPlugin").GetString() == Program.OutputPlugin,
            "source-build output plugin differs from compiled output name");
        Require(sourceRoot.GetProperty("expectedValuesSha256").GetString() == expectedHash,
            "source-build expected-values hash is stale");
        Require(
            sourceRoot.GetProperty("outputSha256").GetString() ==
            manifestRoot.GetProperty("output").GetProperty("sha256").GetString(),
            "source-build and manifest output hashes differ");
    }

    private static void AddDecisionTargets(
        IDictionary<string, TargetPolicy> output,
        JsonElement items,
        string recordType,
        string sourcePlugin)
    {
        foreach (var item in items.EnumerateArray())
        {
            output.Add(
                item.GetProperty("formKey").GetString()!,
                new TargetPolicy(
                    item.GetProperty("editorId").GetString()!,
                    recordType,
                    sourcePlugin,
                    item.GetProperty("fields").EnumerateArray()
                        .Select(field => field.GetString()!)
                        .ToHashSet(StringComparer.Ordinal)));
        }
    }

    private static void RequirePoliciesEqual(
        IReadOnlyDictionary<string, TargetPolicy> expected,
        IReadOnlyDictionary<string, TargetPolicy> actual,
        string label)
    {
        Require(expected.Keys.ToHashSet(StringComparer.OrdinalIgnoreCase)
            .SetEquals(actual.Keys), $"{label} target keys differ");
        foreach (var (key, policy) in expected)
        {
            var other = actual[key];
            Require(policy.EditorId == other.EditorId, $"{label}: {key} EditorID differs");
            Require(policy.RecordType == other.RecordType, $"{label}: {key} record type differs");
            Require(policy.SourcePlugin == other.SourcePlugin, $"{label}: {key} source differs");
            Require(policy.Fields.SetEquals(other.Fields), $"{label}: {key} field ownership differs");
        }
    }

    private static void ValidateOutput(JsonElement output, IReadOnlyList<string> masters)
    {
        Require(output.GetProperty("plugin").GetString() == Program.OutputPlugin,
            "manifest output plugin differs from compiled output name");
        Require(output.GetProperty("eslFlaggedEsp").GetBoolean(), "manifest does not declare an ESL ESP");
        Require(output.GetProperty("overrideOnly").GetBoolean(), "manifest does not declare override-only output");
        Require(output.GetProperty("records").GetInt32() == 14, "manifest output record count differs");
        Require(output.GetProperty("newForms").GetInt32() == 0, "manifest declares new forms");
        Require(
            output.GetProperty("masters").EnumerateArray().Select(item => item.GetString()!)
                .SequenceEqual(masters, StringComparer.Ordinal),
            "manifest masters differ from compiled hard masters");
    }

    private static void ValidateRelationship(JsonElement relationship, string label)
    {
        Require(relationship.GetProperty("existingPatch").GetString() == "Ensrick Lux Water CS Patch.esp",
            $"{label}: existing patch name differs");
        Require(relationship.GetProperty("existingPatchRecords").GetInt32() == 559,
            $"{label}: existing patch record count differs");
        Require(relationship.GetProperty("existingPatchRemainsSeparate").GetBoolean(),
            $"{label}: existing patch is not preserved separately");
        if (relationship.TryGetProperty("newPatchRecords", out var newPatchRecords))
        {
            Require(newPatchRecords.GetInt32() == 14, $"{label}: new patch record count differs");
        }
        if (relationship.TryGetProperty("loadAfterExistingPatch", out var loadAfter))
        {
            Require(loadAfter.GetBoolean(), $"{label}: load-after relationship is absent");
        }
    }

    private static string Sha256(string path) =>
        Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));

    private static string CanonicalTextSha256(string path)
    {
        var text = File.ReadAllText(path).Replace("\r\n", "\n", StringComparison.Ordinal);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text)));
    }

    private static string TreeSha256(string path)
    {
        var lines = Directory.EnumerateFiles(path, "*", SearchOption.AllDirectories)
            .OrderBy(file => file, StringComparer.OrdinalIgnoreCase)
            .Select(file =>
                $"{Path.GetRelativePath(path, file).Replace('\\', '/')}\t{Sha256(file)}");
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(string.Join("\n", lines) + "\n")));
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private sealed record TargetPolicy(
        string EditorId,
        string RecordType,
        string SourcePlugin,
        HashSet<string> Fields);
}
