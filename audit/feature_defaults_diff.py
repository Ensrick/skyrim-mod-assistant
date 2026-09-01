"""Diff a source-built mod's shipped feature defaults against upstream's.

Policy (docs/CURATION_POLICY.md "Source builds", 2026-09-01, #144): a mod we
build from source is not recorded as installed until its build record carries
a `featureDefaultsDiff` naming every default that differs from the upstream
release the user would otherwise have installed. Community Shaders 1.8's AIO
build shipped Advanced Skin and Hair Specular DEFAULT-ON straight from source
headers; nobody had decided that, and the user saw plastic skin for a day.

Inputs are JSON (nested objects) or INI (section/key). Output is a JSON
object ready to paste into records/source-builds/<name>.json, and a human
summary on stdout.

  py -3 audit/feature_defaults_diff.py UPSTREAM BUILT [--out diff.json]
  py -3 audit/feature_defaults_diff.py SettingsDefault.upstream.json SettingsDefault.json
  py -3 audit/feature_defaults_diff.py --record records/source-builds/x.json UPSTREAM BUILT
                                       # writes the diff into the record's featureDefaultsDiff

Exit 0 when identical, 3 when defaults differ (so a build script can stop and
make the operator decide), 1 on a read error.
"""
import configparser, io, json, os, sys


def load(path):
    t = io.open(path, encoding='utf-8-sig', errors='replace').read()
    try:
        return json.loads(t)
    except ValueError:
        cp = configparser.ConfigParser(interpolation=None, strict=False,
                                       allow_no_value=True, delimiters=('=',))
        cp.optionxform = str
        cp.read_string(t)
        return {s: dict(cp.items(s)) for s in cp.sections()}


def flatten(obj, prefix=''):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f'{prefix}{k}.' if prefix or True else k))
    else:
        out[prefix.rstrip('.')] = obj
    return out


def diff(upstream, built):
    u, b = flatten(upstream), flatten(built)
    changed = {k: {'upstream': u[k], 'built': b[k]}
               for k in sorted(set(u) & set(b)) if u[k] != b[k]}
    added = {k: b[k] for k in sorted(set(b) - set(u))}
    removed = {k: u[k] for k in sorted(set(u) - set(b))}
    return {'changed': changed, 'onlyInBuilt': added, 'onlyInUpstream': removed}


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    record = None
    if '--record' in a:
        i = a.index('--record'); record = a[i + 1]; a = a[:i] + a[i + 2:]
    out = None
    if '--out' in a:
        i = a.index('--out'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    up, built = a[0], a[1]
    try:
        d = diff(load(up), load(built))
    except Exception as e:
        print(f'cannot read inputs: {e!r}'); return 1
    d['upstreamFile'] = os.path.abspath(up)
    d['builtFile'] = os.path.abspath(built)
    n = len(d['changed']) + len(d['onlyInBuilt']) + len(d['onlyInUpstream'])
    for k, v in d['changed'].items():
        print(f'  CHANGED  {k}: upstream={v["upstream"]!r} built={v["built"]!r}')
    for k, v in d['onlyInBuilt'].items():
        print(f'  BUILT+   {k} = {v!r}')
    for k, v in d['onlyInUpstream'].items():
        print(f'  UPSTREAM {k} = {v!r} (absent in build)')
    print(f'\n{n} default(s) differ' if n else '\ndefaults identical to upstream')
    if out:
        json.dump(d, io.open(out, 'w', encoding='utf-8'), indent=2)
    if record:
        rec = json.load(io.open(record, encoding='utf-8'))
        rec['featureDefaultsDiff'] = d
        json.dump(rec, io.open(record, 'w', encoding='utf-8'), indent=2)
        print(f'written into {record} as featureDefaultsDiff')
    return 3 if n else 0


if __name__ == '__main__':
    sys.exit(main())
