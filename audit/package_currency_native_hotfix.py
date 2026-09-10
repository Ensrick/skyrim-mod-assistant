"""Repackage a tested, receipt-bound native candidate as a separate hotfix.

No installation, game/save mutation, or vendor payload redistribution. Original
corresponding source and DLL bytes are preserved; overlay-specific notices fix
the base-package notices which otherwise incorrectly describe ESP/PEX assets.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def native_version(payload, contract):
    cmake = payload['Source/EnsrickCurrencyDenominations/CMakeLists.txt'].decode('utf-8')
    matches = re.findall(r'project\(\s*EnsrickCurrencyDenominations\s+VERSION\s+(\d+\.\d+\.\d+)\s+LANGUAGES\s+CXX\s*\)', cmake)
    if len(matches) != 1:
        raise ValueError('Expected exactly one versioned native project declaration')
    version = matches[0]
    if 'nativeVersion' in contract and contract['nativeVersion'] != version:
        raise ValueError('Candidate receipt disagrees with corresponding source version')
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.receipt.read_text())
    assert sha(args.candidate.read_bytes()) == contract['overlaySha256']
    with zipfile.ZipFile(args.candidate) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        payload = {name: archive.read(name) for name in archive.namelist()}
    assert {name: sha(data) for name, data in payload.items()} == contract['overlayFiles']
    native = json.loads(payload['Source/EnsrickCurrencyDenominations/native-build-receipt.json'])
    assert native['dll']['sha256'] == sha(payload['SKSE/Plugins/EnsrickCurrencyDenominations.dll'])
    for item in native['sourceInputs']:
        relative = item['relativePath'].replace('\\', '/')
        data = payload['Source/EnsrickCurrencyDenominations/' + relative]
        assert sha(data) == item['sha256'] and len(data) == item['bytes']
    version = native_version(payload, contract)
    payload['SOURCE.txt'] = f'''Ensrick Currency Native Initialization Fix {version}

The exact {len(native['sourceInputs'])} plugin-side source/build/test inputs are
bundled in Source/EnsrickCurrencyDenominations and bound by the included
native-build-receipt.json. DLL bytes are unchanged from the tested candidate.
Original source: https://github.com/Ensrick/skyrim-mod-assistant
External CommonLib corresponding source: https://github.com/Ensrick/CommonLibSSE-NG
Exact commit: {native['commonLibCommit']}
Build with the bundled build-native.ps1, the pinned CommonLib checkout, and
the UNCHANGED runtime JSON from Regional Currency Integration 0.4.0.
The build receipt records exact toolchain, source, runtime and config inputs.
Packaging-only source is in Source/Packaging/package_currency_native_hotfix.py.
This archive contains no coin models, textures, ESPs or Papyrus binaries.
'''.encode()
    payload['NOTICE.txt'] = f'''Ensrick Currency Native Initialization Fix {version}

Original native repair, separate from Regional Currency Integration 0.4.0.
This overlay replaces only SKSE/Plugins/EnsrickCurrencyDenominations.dll at
runtime. No configuration, currency values, distribution, plugins, assets,
Papyrus or save data are replaced. Full corresponding native source accompanies
the binary. Source is MIT except identified interoperability material; the
combined DLL retains CommonLib GPL-3.0-or-later plus its explicit exceptions.
Keep LICENSE.txt, COMMONLIBSSE-COPYING.txt, COMMONLIBSSE-EXCEPTIONS.md,
QuickLootIE-LICENSE.txt and corresponding source with redistributed binaries.
The candidate's source snapshot includes its original test-only packager;
this final overlay was assembled by the separate packaging recipe.
Fresh-character and matching-checkpoint requirements remain in force.
'''.encode()
    payload['DEPENDENCIES.txt'] = b'''Requires the complete Ensrick Regional Currency Integration 0.4.0 package
and ALL of its existing dependencies, Skyrim 1.7.104.0 and SKSE 2.3.1.
Load this loose-file overlay after that package. Keep both currency ESPs and
the original JSON enabled and unchanged. No new third-party dependency.
This is NOT a standalone currency mod and cannot migrate older saves.
Rollback disables only this overlay; retain original saves and co-saves.
Rollback compatibility depends on the paired SKSE admission build. The old base
DLL has known initialization defects. Overlay 0.2.2 fixes initialization but lacks
the readiness export required by always-on save admission; do not roll it back
independently of an admission-enabled SKSE build.
'''
    payload['Source/Packaging/package_currency_native_hotfix.py'] = Path(__file__).read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / f'Ensrick-Currency-Native-Initialization-Fix-{version}.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    result = dict(contract)
    result.update(status='packaged-hotfix-not-installed', nativeVersion=version,
                  overlaySha256=sha(output.read_bytes()), overlayFileName=output.name,
                  overlayBytes=output.stat().st_size,
                  overlayFiles={name: sha(data) for name, data in sorted(payload.items())},
                  testedCandidateSha256=contract['overlaySha256'],
                  runtimeVerification='Packaging alone proves no runtime behavior; see the separate session report.')
    (args.output / 'hotfix-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(archive=str(output), files=len(payload), sha256=result['overlaySha256']), indent=2))


if __name__ == '__main__':
    main()
