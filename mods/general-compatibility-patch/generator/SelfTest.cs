namespace Ensrick.GeneralCompatibilityPatcher;

internal static class SelfTest
{
    public static int Run()
    {
        try
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

            Console.WriteLine("PASS: Decision A target and field-ownership invariants.");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine($"SELF-TEST FAILED: {exception.Message}");
            return 1;
        }
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
