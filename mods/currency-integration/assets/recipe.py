"""Deterministic user-local regional denomination assets; never redistribute output.

Inputs are pinned vendor loose files/archive members. Only diffuse color and
the referring texture path change; geometry is checked with a deterministic
OBJ export. LE meshes are converted with the pinned nifly-based headless tool.
"""
import argparse
import ast
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


def resolve(relative, archives):
    for root in roots():
        file = root / relative
        if file.is_file():
            raw = file.read_bytes()
            return raw, {'path': str(file), 'member': None, 'sha256': sha(raw)}
    matches = []
    for archive in archives:
        for index, name in enumerate(archive.names()):
            if name.lower().replace('/', '\\') == relative.lower().replace('/', '\\'):
                raw = archive.read(index)
                matches.append((raw, {'path': str(archive.path), 'member': name, 'sha256': sha(raw),
                                      'archiveSha256': sha(Path(archive.path).read_bytes())}))
    if len(matches) != 1:
        raise ValueError(f'Expected one unambiguous archive provider for {relative}: {len(matches)}')
    return matches[0]


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
    reader = bsa_reader()
    mint = INSTANCE / 'mods/M.I.N.T. - More Interesting New Tender'
    archives = [reader(file) for file in sorted(mint.glob('*.bsa'))]
    sources = []
    for family in json.loads(POLICY.read_text())['denominations']['modernFamilies']:
        label = family['displayLabel']
        raw, provenance = resolve(family['sourceModel'], archives)
        folder = ROOT / 'inputs' / label
        folder.mkdir(parents=True, exist_ok=True)
        mesh = folder / 'source.nif'
        mesh.write_bytes(raw)
        state = inspect(mesh)
        diffuse_paths = {shape['textures'][0] for shape in state['shapeDetails']}
        if len(diffuse_paths) != 1:
            raise ValueError(f'{label}: diffuse per shape differs')
        diffuse_path = next(iter(diffuse_paths))
        diffuse, texture_provenance = resolve(diffuse_path, archives)
        (folder / 'source.dds').write_bytes(diffuse)
        sources.append({'family': label, 'mesh': provenance, 'diffuse': texture_provenance,
                        'diffusePath': diffuse_path, 'inspection': state, 'dds': dds_info(diffuse)})
    manifest = {'schemaVersion': 1, 'license': 'vendor-derived outputs: private/user-local generation only',
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
        mesh, diffuse = folder / 'source.nif', folder / 'source.dds'
        if sha(mesh.read_bytes()) != source['mesh']['sha256'] or sha(diffuse.read_bytes()) != source['diffuse']['sha256']:
            raise ValueError('pinned input drift: ' + label)
        work = output / 'work' / label
        work.mkdir(parents=True)
        before_obj = work / 'before.obj'
        run('nif', 'export-obj', mesh, before_obj)
        if source['inspection']['isLE']:
            converted = work / 'converted'
            run('nif', 'convert-sse', mesh, converted)
            mesh = converted / mesh.name
        dimensions = source['dds']
        scale = min(1.0, 1024 / max(dimensions['width'], dimensions['height']))
        width, height = int(dimensions['width'] * scale), int(dimensions['height'] * scale)
        for tier, color in COLORS.items():
            stem = f'{label}_{tier}'
            png = work / (stem + '.png')
            # Neutralize the source metal hue while retaining luminance detail,
            # then blend in the explicit tier color. Alpha is left unchanged.
            run('magick', str(diffuse) + '[0]', '-colorspace', 'Gray', '-colorspace', 'sRGB',
                '-channel', 'RGB', '-fill', color, '-colorize', '55', '+channel',
                '-resize', f'{width}x{height}!', '-strip',
                '-define', 'png:exclude-chunk=date,time', png)
            texture_dir = output / 'package/textures/Ensrick/Currency' / label
            texture_dir.mkdir(parents=True, exist_ok=True)
            run('texconv', '-f', 'BC7_UNORM', '-m', '0', '-nogpu', '-nologo',
                '-o', texture_dir, png)
            texture = texture_dir / (stem + '.dds')
            # Preserve every existing normal/environment/mask texture binding.
            target_relative = f'textures\\Ensrick\\Currency\\{label}\\{stem}.dds'
            target_mesh = output / 'package/Meshes/Ensrick/Currency' / label / (stem + '.nif')
            run('nif', 'remap-textures', mesh, target_mesh, source['diffusePath'], target_relative)
            state = inspect(target_mesh)
            if not state['isSSE'] or not state['sseGeometryCompatible']:
                raise ValueError('Output is not SSE compatible')
            after_obj = work / (stem + '.obj')
            run('nif', 'export-obj', target_mesh, after_obj)
            if before_obj.read_bytes() != after_obj.read_bytes():
                raise ValueError(f'Geometry changed: {stem}')
            expected_textures = {target_relative if t.lower() == source['diffusePath'].lower() else t
                                 for t in source['inspection']['textures']}
            if {t.lower() for t in state['textures']} != {t.lower() for t in expected_textures}:
                raise ValueError(f'Unexpected texture binding changed: {stem}')
            final = dds_info(texture.read_bytes())
            if final['width'] != width or final['height'] != height or final['mips'] != math.floor(math.log2(max(width, height))) + 1:
                raise ValueError('Incorrect dimensions or mip chain')
            results.append({'family': label, 'tier': tier, 'targetColor': color,
                            'mesh': str(target_mesh.relative_to(output / 'package')).replace('\\', '/'),
                            'meshSha256': sha(target_mesh.read_bytes()), 'geometryPreserved': True,
                            'diffuse': str(texture.relative_to(output / 'package')).replace('\\', '/'),
                            'diffuseSha256': sha(texture.read_bytes()), 'dds': final})
    report = {'schemaVersion': 1, 'inputsSha256': sha((ROOT / 'inputs.json').read_bytes()),
              'recipeSha256': sha(Path(__file__).read_bytes()), 'files': results, 'commands': COMMANDS}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'{output}: {len(results)} variants; all SSE geometry, paths, dimensions and mip chains verified')


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
