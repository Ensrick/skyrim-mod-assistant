"""Compare two isolated asset builds and emit the package integration receipt."""

import argparse
import json
from pathlib import Path

import recipe


HERE = Path(__file__).resolve().parent
V030_BASELINE_SHA256 = 'D5FCDE1BD5E19B4FDF67BEF4F9411C25062E05FDDC98208647FDCB1D4C7A4B89'


def inventory(path):
    return {file.relative_to(path).as_posix(): (file.stat().st_size, recipe.sha(file.read_bytes()))
            for file in path.rglob('*') if file.is_file()}


def output_stem(label, tier, diffuse):
    stem = f'{label}_{tier}'
    suffix = diffuse['outputSuffix']
    return stem if suffix is None else f'{stem}_{suffix}'


def bind_report(report, inputs, package, actual):
    """Bind one semantic build report to the exact bytes in its package."""
    report_rows = report.get('files')
    if not isinstance(report_rows, list) or len(report_rows) != len(inputs['sources']) * len(recipe.COLORS):
        raise SystemExit('FAIL: build report does not contain exactly 51 design-tier rows')
    indexed = {}
    for row in report_rows:
        key = (row.get('family'), row.get('tier'))
        if key in indexed:
            raise SystemExit('FAIL: duplicate design-tier row in build report')
        indexed[key] = row

    flattened = {}

    def add(path, digest):
        if path in flattened:
            raise SystemExit(f'FAIL: duplicate output path in build report: {path}')
        flattened[path] = digest

    for source in inputs['sources']:
        label = source['family']
        for tier, color in recipe.COLORS.items():
            row = indexed.get((label, tier))
            if row is None:
                raise SystemExit(f'FAIL: build report omits {label} {tier}')
            mesh_path = f'Meshes/Ensrick/Currency/{label}/{label}_{tier}.nif'
            if (row.get('designId') != source['designId'] or
                    row.get('currencyId') != source['currencyId'] or
                    row.get('targetColor') != color or row.get('mesh') != mesh_path or
                    row.get('geometryPreserved') is not True):
                raise SystemExit(f'FAIL: invalid semantic report row for {label} {tier}')
            add(mesh_path, row.get('meshSha256'))
            reported_diffuses = row.get('diffuses')
            if not isinstance(reported_diffuses, list) or len(reported_diffuses) != len(source['diffuses']):
                raise SystemExit(f'FAIL: invalid diffuse report count for {label} {tier}')
            for diffuse, reported in zip(source['diffuses'], reported_diffuses):
                stem = output_stem(label, tier, diffuse)
                path = f'textures/Ensrick/Currency/{label}/{stem}.dds'
                if (reported.get('sourcePath', '').casefold() != diffuse['sourcePath'].casefold() or
                        reported.get('outputSuffix') != diffuse['outputSuffix'] or
                        reported.get('diffuse') != path):
                    raise SystemExit(f'FAIL: invalid diffuse mapping in report for {label} {tier}')
                info = recipe.dds_info((package / path).read_bytes())
                full_mips = max(info['width'], info['height']).bit_length()
                if (reported.get('dds') != info or info['fourCC'] != 'DX10' or
                        max(info['width'], info['height']) > 1024 or info['mips'] != full_mips):
                    raise SystemExit(f'FAIL: invalid output DDS metadata for {label} {tier}')
                add(path, reported.get('diffuseSha256'))
    actual_hashes = {path: values[1] for path, values in actual.items()}
    if flattened != actual_hashes:
        raise SystemExit('FAIL: build report hashes do not bind the exact package bytes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=HERE)
    parser.add_argument('--left', default='build-a')
    parser.add_argument('--right', default='build-b')
    parser.add_argument('--output', type=Path, default=HERE / 'integration-receipt.json')
    parser.add_argument('--baseline-receipt', type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    left, right = root / args.left, root / args.right
    inputs_raw = (root / 'inputs.json').read_bytes()
    inputs = json.loads(inputs_raw)
    reports = [json.loads((path / 'report.json').read_text()) for path in (left, right)]
    if inputs.get('schemaVersion') != 2 or any(report.get('schemaVersion') != 2 for report in reports):
        raise SystemExit('FAIL: expected schemaVersion 2 inputs and build reports')

    expected_count = sum(1 + len(source['diffuses']) for source in inputs['sources']) * len(recipe.COLORS)
    inventories = [inventory(path / 'package') for path in (left, right)]
    files = inventories[0]
    if files != inventories[1] or len(files) != expected_count or expected_count != 108:
        raise SystemExit(f'FAIL: expected {expected_count} byte-identical NIF/DDS outputs')
    recipe_hash = recipe.sha((HERE / 'recipe.py').read_bytes())
    inputs_hash = recipe.sha(inputs_raw)
    if any(report['recipeSha256'] != recipe_hash for report in reports):
        raise SystemExit('FAIL: recipe changed during builds')
    if any(report['inputsSha256'] != inputs_hash for report in reports):
        raise SystemExit('FAIL: input manifest changed during builds')
    if reports[0]['files'] != reports[1]['files']:
        raise SystemExit('FAIL: semantic asset receipts differ')
    for report, build_root, actual in zip(reports, (left, right), inventories):
        bind_report(report, inputs, build_root / 'package', actual)

    baseline_raw = args.baseline_receipt.read_bytes()
    baseline_json = json.loads(baseline_raw)
    baseline_rows = baseline_json.get('files')
    if (recipe.sha(baseline_raw) != V030_BASELINE_SHA256 or baseline_json.get('schemaVersion') != 1 or
            baseline_json.get('outputCount') != 36 or not isinstance(baseline_rows, list) or
            len(baseline_rows) != 36 or len({row.get('path') for row in baseline_rows}) != 36):
        raise SystemExit('FAIL: baseline is not the canonical v0.3.0 integration receipt')
    expected_baseline = {row['path']: (row['bytes'], row['sha256']) for row in baseline_rows}
    actual_baseline = {path: files.get(path) for path in expected_baseline}
    if actual_baseline != expected_baseline or any(value is None for value in actual_baseline.values()):
        raise SystemExit('FAIL: one or more of the original 36 tier assets changed')
    baseline = {'receiptSha256': V030_BASELINE_SHA256, 'preservedOutputCount': 36,
                'status': '36/36 path, size, and SHA256 tuples unchanged'}

    rows = []
    for source in inputs['sources']:
        label = source['family']
        for tier in recipe.COLORS:
            mesh_path = f'Meshes/Ensrick/Currency/{label}/{label}_{tier}.nif'
            inspection = recipe.inspect(left / 'package' / mesh_path)
            if not inspection['isSSE'] or not inspection['sseGeometryCompatible']:
                raise SystemExit(f'FAIL: output mesh is not SSE-compatible: {mesh_path}')
            rows.append({
                'path': mesh_path,
                'bytes': files[mesh_path][0],
                'sha256': files[mesh_path][1],
                'designId': source['designId'],
                'currencyId': source['currencyId'],
                'formBindings': source['bindings'],
                'sourceLogicalPath': source['meshLogicalPath'],
                'sourcePath': source['mesh']['path'],
                'sourceMember': source['mesh']['member'],
                'sourceBytes': (root / 'inputs' / label / 'source.nif').stat().st_size,
                'sourceSha256': source['mesh']['sha256'],
                'sourceArchiveSha256': source['mesh'].get('archiveSha256'),
                'transform': ('nifly LE-to-SSE conversion; ' if source['inspection']['isLE'] else '') +
                             'remap every authored diffuse slot only; exact OBJ geometry equality',
                'textureBindings': inspection['textures'],
                'shapeDetails': inspection['shapeDetails'],
                'sseCompatible': inspection['isSSE'] and inspection['sseGeometryCompatible'],
            })
            for diffuse in source['diffuses']:
                stem = output_stem(label, tier, diffuse)
                texture_path = f'textures/Ensrick/Currency/{label}/{stem}.dds'
                provenance = diffuse['file']
                source_file = root / 'inputs' / label / diffuse['cacheFile']
                rows.append({
                    'path': texture_path,
                    'bytes': files[texture_path][0],
                    'sha256': files[texture_path][1],
                    'designId': source['designId'],
                    'currencyId': source['currencyId'],
                    'formBindings': source['bindings'],
                    'sourceLogicalPath': diffuse['sourcePath'],
                    'sourcePath': provenance['path'],
                    'sourceMember': provenance['member'],
                    'sourceBytes': source_file.stat().st_size,
                    'sourceSha256': provenance['sha256'],
                    'sourceArchiveSha256': provenance.get('archiveSha256'),
                    'transform': 'neutral luminance; 55% tier tint; <=1024 without upscaling; '
                                 'BC7 CPU; complete mip chain',
                    'dds': recipe.dds_info((left / 'package' / texture_path).read_bytes()),
                    'targetColor': recipe.COLORS[tier],
                    'outputSuffix': diffuse['outputSuffix'],
                })

    if len(rows) != expected_count or {row['path'] for row in rows} != set(files):
        raise SystemExit('FAIL: receipt path set differs from deterministic design/tier paths')
    receipt = {
        'schemaVersion': 2,
        'status': 'static-pass/runtime-unverified',
        'privateOutputs': True,
        'redistribution': 'source recipe only; derive licensed NIF/DDS locally',
        'packageRoot': str(left / 'package'),
        'secondBuildRoot': str(right / 'package'),
        'recipePath': str(HERE / 'recipe.py'),
        'recipeSha256': recipe_hash,
        'inputReceiptSha256': inputs_hash,
        'tools': inputs['tools'],
        'designCount': len(inputs['sources']),
        'designTierCount': len(inputs['sources']) * len(recipe.COLORS),
        'outputCount': len(rows),
        'repeatability': f'{len(rows)}/{len(rows)} SHA256 and size identical',
        'preservedV030Baseline': baseline,
        'geometryBoundary': 'OBJ equality checks shape name, transformed positions and triangle topology; '
                            'texture binding checks preserve normals/environment/masks; no new UV authoring',
        'files': rows,
    }
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f'FAIL: refusing to overwrite receipt: {output}')
    output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {len(rows)} byte-identical assets; {output} ready')


if __name__ == '__main__':
    main()
