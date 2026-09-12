"""Derive the patch's Spriggit YAML tree from the winning source records.

Reads policy.json, the Spriggit serialisation of Tomebound.esp and the Spriggit
serialisation of Apocalypse - Magic of Skyrim.esp, and writes a Spriggit tree for
"Ensrick - Tomebound Redundancy Patch.esp" holding one override per container
record that carries a removed entry, with that entry dropped and every other byte
of the record copied forward unchanged.

The YAML tree it writes is the reviewable source of truth and is committed; the
plugin is rebuilt from it with Spriggit deserialize (see regenerate.ps1). This
script only has to be re-run when Tomebound or Apocalypse themselves change.

  py -3 build_spriggit.py --tomebound <spriggit dir> --apocalypse <spriggit dir> --out spriggit

Determinism: records are emitted in FormKey order, entries keep their source
order, and the YAML writer is pinned to block style with sort_keys off, so two
runs over the same inputs produce byte-identical files.
"""
import argparse, json, os, re, sys, glob, hashlib

try:
    import yaml
except ImportError:
    sys.exit('PyYAML is required: py -3 -m pip install pyyaml')

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = 'Ensrick - Tomebound Redundancy Patch.esp'
DESCRIPTION = ('Removes redundant Tomebound and Apocalypse entries from spell tome, scroll and '
               'staff distribution. Spells, tomes, scrolls and staves themselves are untouched. '
               'Override-only, ESL-flagged, generated from policy.json.')

# Spriggit folder name per record type, and the field holding the entries.
CONTAINERS = {
    'LeveledItems': 'Entries',
    'FormLists': 'Items',
}


def load_tree(root):
    """FormKey -> (record dict, spriggit subfolder) for one serialised plugin."""
    out = {}
    for sub in CONTAINERS:
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, '**', '*.yaml'), recursive=True)):
            y = yaml.safe_load(open(f, encoding='utf-8'))
            if isinstance(y, dict) and 'FormKey' in y:
                out[y['FormKey']] = (y, sub)
    return out


def strip(record, sub, removals):
    """Return (new record, [names removed]) or (None, []) if nothing matched."""
    field = CONTAINERS[sub]
    entries = record.get(field) or []
    kept, dropped = [], []
    for e in entries:
        ref = e['Data']['Reference'] if sub == 'LeveledItems' else e
        if ref in removals:
            dropped.append(removals[ref]['name'])
        else:
            kept.append(e)
    if not dropped:
        return None, []
    new = dict(record)
    new[field] = kept
    return new, dropped


def safe_name(record):
    """Spriggit's file naming: '<EditorID> - <FormID>_<master>.yaml'."""
    fid, master = record['FormKey'].split(':', 1)
    eid = record.get('EditorID') or 'NoEditorID'
    return '%s - %s_%s.yaml' % (eid, fid, master)


FORMKEY = re.compile(r'^[0-9A-F]{6}:(.+\.es[pml])$', re.I)


def referenced_masters(node, out):
    """Every plugin named by a FormKey anywhere inside a copied record.

    A leveled list carries more than its entries: LVLG globals, COED owners and
    the record's own FormKey all point at other plugins, and every one of them has
    to appear in the header or Mutagen cannot map the FormKey to a master index.
    """
    if isinstance(node, dict):
        for v in node.values():
            referenced_masters(v, out)
    elif isinstance(node, list):
        for v in node:
            referenced_masters(v, out)
    elif isinstance(node, str):
        m = FORMKEY.match(node.strip())
        if m:
            out.add(m.group(1))


def write_yaml(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False, allow_unicode=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tomebound', required=True)
    ap.add_argument('--apocalypse', required=True)
    ap.add_argument('--out', default=os.path.join(HERE, 'spriggit'))
    ap.add_argument('--policy', default=os.path.join(HERE, 'policy.json'))
    ap.add_argument('--load-order', required=True,
                    help="the profile's loadorder.txt; masters are emitted in this order")
    a = ap.parse_args()

    policy = json.load(open(a.policy, encoding='utf-8'))
    sources = [('Tomebound.esp', a.tomebound), ('Apocalypse - Magic of Skyrim.esp', a.apocalypse)]

    order = [l.strip() for l in open(a.load_order, encoding='utf-8-sig') if l.strip()
             and not l.startswith('#')]
    rank = {n.lower(): i for i, n in enumerate(order)}

    report, emitted = [], 0
    masters = set()
    for master, root in sources:
        removals = policy['removals'][master]
        tree = load_tree(root)
        touched = False
        for fk in sorted(tree):
            record, sub = tree[fk]
            new, dropped = strip(record, sub, removals)
            if not new:
                continue
            before = len(record[CONTAINERS[sub]] or [])
            after = len(new[CONTAINERS[sub]])
            if after == 0:
                sys.exit('REFUSING: %s (%s) would be emptied. An empty container is not a '
                         'redundancy fix.' % (record.get('EditorID'), fk))
            referenced_masters(new, masters)
            write_yaml(os.path.join(a.out, sub, safe_name(new)), new)
            report.append({'formKey': fk, 'editorId': record.get('EditorID'), 'type': sub,
                           'entriesBefore': before, 'entriesAfter': after, 'removed': dropped})
            emitted += 1
            touched = True
        if touched:
            masters.add(master)

    if not emitted:
        sys.exit('REFUSING: the patch would be empty.')

    unknown = [m for m in masters if m.lower() not in rank]
    if unknown:
        sys.exit('REFUSING: referenced master(s) absent from the load order: %s' % unknown)
    masters = sorted(masters, key=lambda m: rank[m.lower()])

    write_yaml(os.path.join(a.out, 'RecordData.yaml'), {
        'SpriggitSource': {'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.41'},
        'ModKey': PLUGIN,
        'GameRelease': 'SkyrimSE',
        'ModHeader': {
            'Flags': ['Small'],
            'Author': 'Ensrick',
            'Description': DESCRIPTION,
            'MasterReferences': [{'Master': m, 'FileSize': 0} for m in masters],
        },
    })
    with open(os.path.join(a.out, 'spriggit-meta.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.41.0',
                   'Release': 'SkyrimSE', 'ModKey': PLUGIN}, fh, indent=2)

    total = sum(len(r['removed']) for r in report)
    print(json.dumps({'records': emitted, 'entriesRemoved': total,
                      'masters': masters, 'detail': report}, indent=2))


if __name__ == '__main__':
    main()
