using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace Ensrick.GuardScalingPatcher;

internal static class LinkAudit
{
    public static int Run(string dataFolder, string loadOrderFile, string pluginPath)
    {
        var modKeys = LoadOrderFile.Read(loadOrderFile);
        using var loadOrder = LoadOrder.Import<ISkyrimModGetter>(
            new DirectoryPath(dataFolder),
            modKeys,
            GameRelease.SkyrimSE,
            factory: modPath => SkyrimMod.CreateFromBinaryOverlay(modPath.Path, SkyrimRelease.SkyrimSE));
        using var plugin = SkyrimMod.CreateFromBinaryOverlay(pluginPath, SkyrimRelease.SkyrimSE);
        using var cache = loadOrder.ListedOrder
            .Where(listing => listing.Mod is not null)
            .Select(listing => listing.Mod!)
            .Append(plugin)
            .ToImmutableLinkCache();
        var unresolved = new List<object>();
        var linksChecked = 0;
        foreach (var record in plugin.EnumerateMajorRecords())
        {
            foreach (var link in record.EnumerateFormLinks())
            {
                if (link.FormKey.IsNull) continue;
                linksChecked++;
                if (!cache.TryResolve(link.FormKey, link.Type, out _))
                {
                    unresolved.Add(new
                    {
                        record = record.FormKey.ToString(),
                        editorId = record.EditorID,
                        target = link.FormKey.ToString(),
                        targetType = link.Type.FullName,
                    });
                }
            }
        }
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            records = plugin.EnumerateMajorRecords().Count(),
            linksChecked,
            unresolved,
        }));
        return unresolved.Count == 0 ? 0 : 2;
    }
}

internal static class LoadOrderFile
{
    /// <summary>plugins.txt-style file: one plugin per line, '*' marks active, '#' comments.
    /// The five base masters are always present first; our own output is never an input.</summary>
    public static ModKey[] Read(string loadOrderFile)
    {
        var listed = File.ReadAllLines(loadOrderFile)
            .Select(line => line.Trim())
            .Where(line => line.Length > 0 && !line.StartsWith('#'))
            .Select(line => ModKey.FromNameAndExtension(line.TrimStart('*')))
            .Where(modKey => !string.Equals(modKey.FileName.String, Program.OutputPlugin, StringComparison.OrdinalIgnoreCase))
            .ToArray();
        return new[] { "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm" }
            .Select(name => ModKey.FromNameAndExtension(name))
            .Concat(listed)
            .Distinct()
            .ToArray();
    }
}
