"""Package a receipt-bound native candidate, never deploy it or alter a release.

The test overlay must only be enabled in a disposable MO2 profile. Its source
and dependency notices accompany the DLL; no vendor/game assets are copied.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    repo = root.parents[2]
    base = root.parent
    receipt_bytes = (args.build / 'native-build-receipt.json').read_bytes()
    receipt = json.loads(receipt_bytes)
    release = json.loads((repo / 'records/source-builds/currency-integration-0.4.0.json').read_text())
    dll_path = receipt['dll']['relativePath']
    dll = (args.build / 'build/Release/EnsrickCurrencyDenominations.dll').read_bytes()
    assert digest(dll) == receipt['dll']['sha256']
    assert len(dll) == receipt['dll']['bytes']
    assert receipt['commonLibCommit'] == '90a64a4d65ce659a139137c968f42151bb6ecec9'
    assert receipt['commonLibTrackedStatus'] == 'clean'
    assert receipt['runtimeConfig']['sha256'] == release['winningFiles']['SKSE/Plugins/EnsrickCurrencyDenominations.json']
    payload = {dll_path: dll}
    source_prefix = 'Source/EnsrickCurrencyDenominations/'
    for item in receipt['sourceInputs']:
        relative = item['relativePath'].replace('\\', '/')
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        data = (root / relative).read_bytes()
        assert digest(data) == item['sha256'] and len(data) == item['bytes'], relative
        payload[source_prefix + relative] = data
    payload[source_prefix + 'native-build-receipt.json'] = receipt_bytes
    for name in ('LICENSE.txt', 'NOTICE.txt', 'SOURCE.txt', 'DEPENDENCIES.txt',
                 'COMMONLIBSSE-COPYING.txt', 'COMMONLIBSSE-EXCEPTIONS.md', 'QuickLootIE-LICENSE.txt'):
        payload[name] = (base / 'package' / name).read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / 'Ensrick-Currency-Native-0.2.2-TEST-ONLY.zip'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    # This test receipt inherits only the unchanged release's winning-file
    # contract, NOT its historical installation/static/runtime assertions.
    candidate = dict(schemaVersion=1, version='0.4.0',
                     status='native-0.2.2-isolated-test-only-runtime-unverified',
                     winningFiles=dict(release['winningFiles']),
                     parentRelease='currency-integration-0.4.0.json',
                     nativeBuildReceiptSha256=digest(receipt_bytes),
                     overlaySha256=digest(target.read_bytes()),
                     overlayFiles={name: digest(data) for name, data in sorted(payload.items())})
    candidate['winningFiles'][dll_path] = digest(dll)
    (args.output / 'candidate-receipt.json').write_text(json.dumps(candidate, indent=2) + '\n')
    print(json.dumps(dict(archive=str(target), files=len(payload), sha256=candidate['overlaySha256'],
                         nativeDllSha256=digest(dll)), indent=2))


if __name__ == '__main__':
    main()
