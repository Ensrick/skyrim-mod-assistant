"""Deterministic user-local denomination assets; never redistribute output.

Inputs are pinned vendor loose files/archive members. Every selected cultural
coin design receives Copper/Silver/Gold output paths. Only authored diffuse
bindings and the referring texture paths change; geometry is checked with a
deterministic OBJ export. LE meshes are converted with the pinned nifly-based
headless tool.
"""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parent
INSTANCE = Path(r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se')
REPO = Path(r'C:\Users\danjo\source\repos\skyrim-mod-assistant')
POLICY = Path(r'C:\Users\danjo\source\repos\_codex_worktrees\ece-null-location-guard\mods\currency-integration\policy.json')
TOOLS = {
    'nif': Path(r'C:\Users\danjo\source\repos\skyrim-tools-builds\nif-port-cli\Release\nif-port-cli.exe'),
    'magick': Path(r'C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe'),
    'texconv': Path(r'C:\Users\danjo\AppData\Local\Microsoft\WinGet\Packages\Microsoft.DirectXTex.Texconv_Microsoft.Winget.Source_8wekyb3d8bbwe\texconv.exe'),
}
COLORS = {'Copper': '#B87333', 'Silver': '#C0C0C0', 'Gold': '#D4AF37'}
COMMANDS = []
_ARCHIVE_CACHE = {}
_ARCHIVE_HASHES = {}

# One entry per non-Septim visual design. Form aliases belong in bindings and
# deliberately do not manufacture a nonexistent source mesh. In particular,
# M.I.N.T.'s unified Gibber (DE5027) uses the authored GibberFront mesh.
DESIGNS = [
    {
        'designId': 'mede', 'currencyId': 'mede', 'label': 'Mede',
        'bindings': [{'formKey': 'DE5021:Update.esm', 'editorId': 'EC_Mede'}],
        'meshPath': r'Meshes\Trotsky2302\mede.nif', 'meshArchive': None,
        'diffuses': [{'path': r'textures\Trotsky2302\mede.dds', 'archive': None, 'outputSuffix': None}],
    },
    {
        'designId': 'ulfric', 'currencyId': 'ulfric', 'label': 'Ulfric',
        'bindings': [{'formKey': 'DE5024:Update.esm', 'editorId': 'DES_Ulfric'}],
        'meshPath': r'Meshes\MINT\Ulfric\Ulfric.nif', 'meshArchive': 'M.I.N.T.bsa',
        'diffuses': [{'path': r'textures\mint\Ulfric\Ulfric.dds',
                      'archive': 'M.I.N.T - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'dram', 'currencyId': 'dram', 'label': 'Dram',
        'bindings': [{'formKey': 'DE5029:Update.esm', 'editorId': 'DES_Dram'}],
        'meshPath': r'Meshes\MINT\Dram\Dram.nif', 'meshArchive': None,
        'diffuses': [{'path': r'textures\MINT\Dram\dram.dds', 'archive': None, 'outputSuffix': None}],
    },
    {
        'designId': 'oshka', 'currencyId': 'oshka', 'label': 'Oshka',
        'bindings': [{'formKey': '000871:exchangeCurrency_patch_COIN.esp', 'editorId': 'EC_Oshka'}],
        'meshPath': r'Meshes\Nerapharu\Oshka\oshka.nif', 'meshArchive': None,
        'diffuses': [{'path': r'textures\Nerapharu\Oshka\oshka.dds',
                      'archive': None, 'outputSuffix': None}],
    },
    {
        'designId': 'ohzer', 'currencyId': 'ohzer', 'label': 'Ohzer',
        'bindings': [{'formKey': '00086F:exchangeCurrency_patch_COIN.esp', 'editorId': 'EC_Ohzer'}],
        'meshPath': r"Meshes\Mihail's Shards of Immersion\Coin Apocrypha\ohzer.nif",
        'meshArchive': None,
        'diffuses': [{'path': r"textures\mihail's shards of immersion\coin apocrypha\coin.dds",
                      'archive': None, 'outputSuffix': None}],
    },
    {
        'designId': 'varken', 'currencyId': 'varken', 'label': 'Varken',
        'bindings': [{'formKey': '000870:exchangeCurrency_patch_COIN.esp', 'editorId': 'EC_Varken'}],
        'meshPath': r"Meshes\Mihail's Shards of Immersion\Coin Dremora\varken.nif",
        'meshArchive': None,
        'diffuses': [{'path': r"textures\mihail's shards of immersion\coin dremora\coin.dds",
                      'archive': None, 'outputSuffix': None}],
    },
    {
        'designId': 'drakr-dragon', 'currencyId': 'drakr', 'label': 'DrakrDragon',
        'bindings': [{'formKey': 'DE5012:Update.esm', 'editorId': 'DES_DrakrDragon'}],
        'meshPath': r'Meshes\COIN\Drakr\Drakr01.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'textures\COIN\Drakr\Drakr.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'drakr-moth', 'currencyId': 'drakr', 'label': 'DrakrMoth',
        'bindings': [{'formKey': 'DE5013:Update.esm', 'editorId': 'DES_DrakrMoth'}],
        'meshPath': r'Meshes\COIN\Drakr\Drakr02.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'textures\COIN\Drakr\Drakr.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'drakr-owl', 'currencyId': 'drakr', 'label': 'DrakrOwl',
        'bindings': [{'formKey': 'DE5014:Update.esm', 'editorId': 'DES_DrakrOwl'}],
        'meshPath': r'Meshes\COIN\Drakr\Drakr03.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'textures\COIN\Drakr\Drakr.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'drakr-whale', 'currencyId': 'drakr', 'label': 'DrakrWhale',
        'bindings': [{'formKey': 'DE5015:Update.esm', 'editorId': 'DES_DrakrWhale'}],
        'meshPath': r'Meshes\COIN\Drakr\Drakr04.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'textures\COIN\Drakr\Drakr.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'gibber-front', 'currencyId': 'gibber', 'label': 'GibberFront',
        'bindings': [
            {'formKey': 'DE5018:Update.esm', 'editorId': 'DES_GibberFront'},
            {'formKey': 'DE5027:Update.esm', 'editorId': 'DES_Gibber', 'assetAlias': True},
        ],
        'meshPath': r'Meshes\MINT\Gibber\GibberFront.nif', 'meshArchive': 'M.I.N.T.bsa',
        'diffuses': [
            {'path': r'textures\MINT\Gibber\GibberGold.dds',
             'archive': 'M.I.N.T - Textures.bsa', 'outputSuffix': 'Face0'},
            {'path': r'textures\MINT\Gibber\GibberDark.dds',
             'archive': 'M.I.N.T - Textures.bsa', 'outputSuffix': 'Face10'},
        ],
    },
    {
        'designId': 'gibber-back', 'currencyId': 'gibber', 'label': 'GibberBack',
        'bindings': [{'formKey': 'DE5017:Update.esm', 'editorId': 'DES_GibberBack'}],
        'meshPath': r'Meshes\MINT\Gibber\GibberBack.nif', 'meshArchive': 'M.I.N.T.bsa',
        'diffuses': [
            {'path': r'textures\MINT\Gibber\GibberGold.dds',
             'archive': 'M.I.N.T - Textures.bsa', 'outputSuffix': 'Face0'},
            {'path': r'textures\MINT\Gibber\GibberDark.dds',
             'archive': 'M.I.N.T - Textures.bsa', 'outputSuffix': 'Face10'},
        ],
    },
    {
        'designId': 'mala', 'currencyId': 'mala', 'label': 'Mala',
        'bindings': [{'formKey': 'DE5019:Update.esm', 'editorId': 'DES_Mala'}],
        'meshPath': r'Meshes\COIN\Mala\Mala.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'textures\COIN\Mala\Mala.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'mallari', 'currencyId': 'mallari', 'label': 'Mallari',
        'bindings': [{'formKey': 'DE5020:Update.esm', 'editorId': 'DES_Mallari'}],
        'meshPath': r'Meshes\COIN\Mallari\Mallari.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'textures\COIN\Mallari\Mallari.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'nchuark', 'currencyId': 'nchuark', 'label': 'Nchuark',
        'bindings': [{'formKey': 'DE5022:Update.esm', 'editorId': 'DES_Nchuark'}],
        'meshPath': r'Meshes\COIN\Nchuark\Nchuark.nif', 'meshArchive': 'C.O.I.N.bsa',
        'diffuses': [{'path': r'Textures\COIN\Nchuark\Nchuark.dds',
                      'archive': 'C.O.I.N - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'sancar', 'currencyId': 'sancar', 'label': 'Sancar',
        'bindings': [{'formKey': 'DE5023:Update.esm', 'editorId': 'DES_Sancar'}],
        'meshPath': r'Meshes\MINT\Sancar\Sancar.nif', 'meshArchive': 'M.I.N.T.bsa',
        'diffuses': [{'path': r'textures\mint\sancar\sancar.dds',
                      'archive': 'M.I.N.T - Textures.bsa', 'outputSuffix': None}],
    },
    {
        'designId': 'bruma-ayleid', 'currencyId': 'mala', 'label': 'BrumaAyleid',
        'bindings': [{'formKey': '6028DC:BSAssets.esm', 'editorId': 'BSKAyleidGold001'}],
        'meshPath': r'Meshes\BSCyrodiil\dungeons\AyleidRuins\AyleidCoin01.nif',
        'meshArchive': 'BSAssets - Textures.bsa',
        'diffuses': [
            {'path': r'textures\bscyrodiil\dungeons\ayleidruins\ayleiscoin01.dds',
             'archive': 'BSAssets - Textures.bsa', 'outputSuffix': None},
        ],
    },
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def run(tool, *args):
    command = [str(TOOLS.get(tool, tool))] + [str(arg) for arg in args]
    COMMANDS.append(command)
    env = dict(os.environ, MAGICK_THREAD_LIMIT='1', OMP_NUM_THREADS='8', SOURCE_DATE_EPOCH='946684800')
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace',
                            check=True, creationflags=0x08000000, env=env)
    return result.stdout


def bsa_reader():
    # Reuse only the credential-free reader definitions, NOT modasset's network
    # configuration or module initialization. The reader source is input-pinned.
    path = REPO / 'audit/modasset.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                and node.name in ('BSA', 'lz4_frame', 'lz4_block')]
    if len(selected) != 3:
        raise ValueError('audited BSA reader definitions changed')
    namespace = {'struct': struct, 'zlib': zlib}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['BSA']


def roots():
    rows = (INSTANCE / 'profiles/Default/modlist.txt').read_text(encoding='utf-8-sig').splitlines()
    return [INSTANCE / 'overwrite'] + [INSTANCE / 'mods' / row[1:] for row in rows if row.startswith('+')]


def resolve(relative, archive_name=None):
    for root in roots():
        file = root / relative
        if file.is_file():
            raw = file.read_bytes()
            return raw, {'path': str(file), 'member': None, 'sha256': sha(raw)}
    if not archive_name:
        raise ValueError(f'Pinned loose provider is absent for {relative}')
    candidates = [root / archive_name for root in roots() if (root / archive_name).is_file()]
    if not candidates:
        raise ValueError(f'Pinned archive is not visible: {archive_name}')
    archive_path = candidates[0]
    if archive_path not in _ARCHIVE_CACHE:
        _ARCHIVE_CACHE[archive_path] = bsa_reader()(archive_path)
    archive = _ARCHIVE_CACHE[archive_path]
    matches = [index for index, name in enumerate(archive.names())
               if name.lower().replace('/', '\\') == relative.lower().replace('/', '\\')]
    if len(matches) != 1:
        raise ValueError(f'Expected one exact member in {archive_name} for {relative}: {len(matches)}')
    index = matches[0]
    raw = archive.read(index)
    if archive_path not in _ARCHIVE_HASHES:
        _ARCHIVE_HASHES[archive_path] = sha(archive_path.read_bytes())
    return raw, {'path': str(archive.path), 'member': archive.names()[index], 'sha256': sha(raw),
                 'archiveSha256': _ARCHIVE_HASHES[archive_path]}


def dds_info(raw):
    if len(raw) < 128 or raw[:4] != b'DDS ':
        raise ValueError('invalid DDS')
    height, width = struct.unpack_from('<II', raw, 12)
    mips = struct.unpack_from('<I', raw, 28)[0]
    return {'width': width, 'height': height, 'mips': mips, 'fourCC': raw[84:88].decode('ascii')}


def inspect(file):
    obj = json.loads(run('nif', 'inspect', file))
    if not obj['valid'] or obj['unknownBlocks']:
        raise ValueError(f'Unsupported NIF {file}')
    return obj


def snapshot_inputs():
    if (ROOT / 'inputs.json').exists():
        raise ValueError('inputs already exist; never silently repin')
    sources = []
    for design in DESIGNS:
        label = design['label']
        raw, provenance = resolve(design['meshPath'], design['meshArchive'])
        folder = ROOT / 'inputs' / label
        folder.mkdir(parents=True, exist_ok=True)
        mesh = folder / 'source.nif'
        mesh.write_bytes(raw)
        state = inspect(mesh)
        actual_diffuses = {shape['textures'][0].casefold() for shape in state['shapeDetails']}
        configured_diffuses = {item['path'].casefold() for item in design['diffuses']}
        if actual_diffuses != configured_diffuses:
            raise ValueError(f'{label}: authored diffuse bindings differ from the exact catalog')
        diffuse_pins = []
        for index, item in enumerate(design['diffuses']):
            diffuse, texture_provenance = resolve(item['path'], item['archive'])
            suffix = item['outputSuffix']
            cache_file = 'source.dds' if len(design['diffuses']) == 1 else f'source-{suffix}.dds'
            (folder / cache_file).write_bytes(diffuse)
            diffuse_pins.append({'sourcePath': item['path'], 'outputSuffix': suffix,
                                 'cacheFile': cache_file, 'file': texture_provenance,
                                 'dds': dds_info(diffuse)})
        sources.append({'designId': design['designId'], 'currencyId': design['currencyId'],
                        'family': label, 'bindings': design['bindings'],
                        'meshLogicalPath': design['meshPath'], 'mesh': provenance,
                        'diffuses': diffuse_pins, 'inspection': state})
    manifest = {'schemaVersion': 2, 'license': 'vendor-derived outputs: private/user-local generation only',
                'maximumDiffuseDimension': 1024, 'colors': COLORS,
                'tools': {name: {'path': str(path), 'sha256': sha(path.read_bytes())} for name, path in TOOLS.items()},
                'bsaReaderSha256': sha((REPO / 'audit/modasset.py').read_bytes()), 'sources': sources}
    (ROOT / 'inputs.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))


def build(name):
    if not name or Path(name).name != name:
        raise ValueError('output must be one directory name')
    output = ROOT / name
    if output.exists():
        raise ValueError('output directory already exists; no overwrite')
    pins = json.loads((ROOT / 'inputs.json').read_text())
    for tool, pin in pins['tools'].items():
        if sha(TOOLS[tool].read_bytes()) != pin['sha256']:
            raise ValueError(f'Tool drift: {tool}')
    if sha((REPO / 'audit/modasset.py').read_bytes()) != pins['bsaReaderSha256']:
        raise ValueError('BSA reader drift')
    output.mkdir()
    results = []
    for source in pins['sources']:
        label = source['family']
        folder = ROOT / 'inputs' / label
        mesh = folder / 'source.nif'
        if sha(mesh.read_bytes()) != source['mesh']['sha256']:
            raise ValueError('pinned input drift: ' + label)
        diffuse_inputs = []
        for diffuse_pin in source['diffuses']:
            diffuse = folder / diffuse_pin['cacheFile']
            if sha(diffuse.read_bytes()) != diffuse_pin['file']['sha256']:
                raise ValueError('pinned diffuse input drift: ' + label)
            diffuse_inputs.append((diffuse_pin, diffuse))
        work = output / 'work' / label
        work.mkdir(parents=True)
        before_obj = work / 'before.obj'
        run('nif', 'export-obj', mesh, before_obj)
        if source['inspection']['isLE']:
            converted = work / 'converted'
            run('nif', 'convert-sse', mesh, converted)
            mesh = converted / mesh.name
        texture_dir = output / 'package/textures/Ensrick/Currency' / label
        texture_dir.mkdir(parents=True, exist_ok=True)
        mesh_dir = output / 'package/Meshes/Ensrick/Currency' / label
        mesh_dir.mkdir(parents=True, exist_ok=True)

        def build_tier(item):
            tier, color = item
            stem = f'{label}_{tier}'
            remaps = []
            diffuse_results = []
            for diffuse_pin, diffuse in diffuse_inputs:
                suffix = diffuse_pin['outputSuffix']
                output_stem = stem if suffix is None else f'{stem}_{suffix}'
                png = work / (output_stem + '.png')
                dimensions = diffuse_pin['dds']
                scale = min(1.0, 1024 / max(dimensions['width'], dimensions['height']))
                width, height = int(dimensions['width'] * scale), int(dimensions['height'] * scale)
                # Neutralize the source metal hue while retaining luminance detail,
                # then blend in the explicit tier color. Alpha is left unchanged.
                run('magick', str(diffuse) + '[0]', '-colorspace', 'Gray', '-colorspace', 'sRGB',
                    '-channel', 'RGB', '-fill', color, '-colorize', '55', '+channel',
                    '-resize', f'{width}x{height}!', '-strip',
                    '-define', 'png:exclude-chunk=date,time', png)
                run('texconv', '-f', 'BC7_UNORM', '-m', '0', '-nogpu', '-nologo',
                    '-o', texture_dir, png)
                texture = texture_dir / (output_stem + '.dds')
                target_relative = f'textures\\Ensrick\\Currency\\{label}\\{output_stem}.dds'
                remaps.extend((diffuse_pin['sourcePath'], target_relative))
                final = dds_info(texture.read_bytes())
                if (final['width'] != width or final['height'] != height or
                        final['mips'] != math.floor(math.log2(max(width, height))) + 1):
                    raise ValueError('Incorrect dimensions or mip chain')
                diffuse_results.append({'sourcePath': diffuse_pin['sourcePath'],
                                        'outputSuffix': suffix,
                                        'diffuse': str(texture.relative_to(output / 'package')).replace('\\', '/'),
                                        'diffuseSha256': sha(texture.read_bytes()), 'dds': final})
            target_mesh = mesh_dir / (stem + '.nif')
            run('nif', 'remap-textures', mesh, target_mesh, *remaps)
            state = inspect(target_mesh)
            if not state['isSSE'] or not state['sseGeometryCompatible']:
                raise ValueError('Output is not SSE compatible')
            after_obj = work / (stem + '.obj')
            run('nif', 'export-obj', target_mesh, after_obj)
            if before_obj.read_bytes() != after_obj.read_bytes():
                raise ValueError(f'Geometry changed: {stem}')
            replacements = {remaps[index].casefold(): remaps[index + 1]
                            for index in range(0, len(remaps), 2)}
            before_shapes = source['inspection']['shapeDetails']
            after_shapes = state['shapeDetails']
            if len(before_shapes) != len(after_shapes):
                raise ValueError(f'Unexpected shape count changed: {stem}')
            for before, after in zip(before_shapes, after_shapes):
                expected = [replacements.get(texture.casefold(), texture)
                            for texture in before['textures']]
                if (before['name'] != after['name'] or
                        [texture.casefold() for texture in after['textures']] !=
                        [texture.casefold() for texture in expected]):
                    raise ValueError(f'Unexpected per-shape texture binding changed: {stem}')
            return {'designId': source['designId'], 'currencyId': source['currencyId'],
                    'family': label, 'tier': tier, 'targetColor': color,
                    'mesh': str(target_mesh.relative_to(output / 'package')).replace('\\', '/'),
                    'meshSha256': sha(target_mesh.read_bytes()), 'geometryPreserved': True,
                    'diffuses': diffuse_results}

        # The pinned compressors are CPU-bound and operate on independent paths.
        # map() preserves Copper/Silver/Gold report order despite parallel work.
        with ThreadPoolExecutor(max_workers=len(COLORS)) as executor:
            results.extend(executor.map(build_tier, COLORS.items()))
    report = {'schemaVersion': 2, 'inputsSha256': sha((ROOT / 'inputs.json').read_bytes()),
              'recipeSha256': sha(Path(__file__).read_bytes()), 'files': results,
              'commands': sorted(COMMANDS)}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    output_files = sum(1 + len(source['diffuses']) for source in pins['sources']) * len(COLORS)
    print(f'{output}: {len(results)} design tiers / {output_files} files; '
          'all SSE geometry, paths, dimensions and mip chains verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true')
    parser.add_argument('--build')
    options = parser.parse_args()
    if options.snapshot:
        snapshot_inputs()
    elif options.build:
        build(options.build)
    else:
        parser.error('select --snapshot or --build NAME')
