"""Compare two isolated asset builds and emit the package integration receipt."""
import json
from pathlib import Path
import recipe

root = Path(__file__).resolve().parent
left, right = root / 'build-b', root / 'build-c'
inputs = json.loads((root / 'inputs.json').read_text())
reports = [json.loads((path / 'report.json').read_text()) for path in (left, right)]

def inventory(path):
    return {file.relative_to(path).as_posix(): (file.stat().st_size, recipe.sha(file.read_bytes()))
            for file in path.rglob('*') if file.is_file()}

files = inventory(left / 'package')
if files != inventory(right / 'package') or len(files) != 36:
    raise SystemExit('FAIL: expected 36 byte-identical NIF/DDS outputs')
recipe_hash = recipe.sha((root / 'recipe.py').read_bytes())
if any(report['recipeSha256'] != recipe_hash for report in reports):
    raise SystemExit('FAIL: recipe changed during builds')
if reports[0]['files'] != reports[1]['files']:
    raise SystemExit('FAIL: semantic asset receipts differ')

rows = []
for family in inputs['sources']:
    label = family['family']
    for tier in recipe.COLORS:
        stem = f'{label}_{tier}'
        for kind, prefix, extension in [('mesh', 'Meshes', 'nif'), ('diffuse', 'textures', 'dds')]:
            path = f'{prefix}/Ensrick/Currency/{label}/{stem}.{extension}'
            provenance = family[kind]
            source_file = root / 'inputs' / label / ('source.nif' if kind == 'mesh' else 'source.dds')
            row = {'path': path, 'bytes': files[path][0], 'sha256': files[path][1],
                   'sourcePath': provenance['path'], 'sourceMember': provenance['member'],
                   'sourceBytes': source_file.stat().st_size, 'sourceSha256': provenance['sha256'],
                   'sourceArchiveSha256': provenance.get('archiveSha256'),
                   'transform': ('nifly LE-to-SSE conversion; ' if family['inspection']['isLE'] else '') +
                                'remap diffuse only; exact OBJ geometry equality' if kind == 'mesh' else
                                'neutral luminance; 55% tier tint; <=1024 without upscaling; BC7 CPU; complete mip chain'}
            if kind == 'mesh':
                inspection = recipe.inspect(left / 'package' / path)
                row['textureBindings'] = inspection['textures']
                row['shapeDetails'] = inspection['shapeDetails']
                row['sseCompatible'] = inspection['isSSE'] and inspection['sseGeometryCompatible']
            else:
                row['dds'] = recipe.dds_info((left / 'package' / path).read_bytes())
                row['targetColor'] = recipe.COLORS[tier]
            rows.append(row)

receipt = {'schemaVersion': 1, 'status': 'static-pass/runtime-unverified',
           'privateOutputs': True, 'redistribution': 'source recipe only; derive licensed NIF/DDS locally',
           'packageRoot': str(left / 'package'), 'secondBuildRoot': str(right / 'package'),
           'recipePath': str(root / 'recipe.py'), 'recipeSha256': recipe_hash,
           'inputReceiptSha256': recipe.sha((root / 'inputs.json').read_bytes()),
           'tools': inputs['tools'], 'outputCount': len(rows), 'repeatability': '36/36 SHA256 and size identical',
           'geometryBoundary': 'OBJ equality checks shape name, transformed positions and triangle topology; '
                               'texture binding checks preserve normals/environment/masks; no new UV authoring',
           'files': rows}
(root / 'integration-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(f'PASS: {len(rows)} byte-identical assets; integration-receipt.json ready')
