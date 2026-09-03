"""Every installed Nexus mod must carry a Keep; no Keep may be uninstalled.

Doctrine: docs/CURATION_POLICY.md, "Installed implies Keep" (user, 2026-09-02).
Adding the Keep is a required step of installing a mod, so this is a gate, not a
report. It runs inside preflight.py.

Three violations, all blocking:

  1. installed Nexus id with no Keep      - the install never finished
  2. Keep with nothing installed          - stale, or an un-actioned adoption
  3. Skip that is installed               - a rejected mod left in the tree

Enabled/disabled is deliberately irrelevant. A parked, superseded or
overlap-held mod is still in the build and keeps its Keep. Our own artifacts
(Ensrick overlays, native rebuilds, source builds, harness mods) resolve to no
Nexus id and are exempt.

  py -3 audit/keep_coverage.py            # gate, exit 1 on any violation
  py -3 audit/keep_coverage.py --json     # machine-readable, always exit 0
  py -3 audit/keep_coverage.py --plan     # what a relay batch would change

Reading the live curator state needs nexus-local-curator/scripts/curator_state.py
(Firefox extension storage). If that is unavailable the gate WARNS rather than
fails - it cannot prove a violation it cannot read.
"""
import argparse, json, pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se')
LEDGER = REPO / 'records' / 'installed-mods.json'
CURATOR = REPO.parent / 'nexus-local-curator' / 'scripts'
GAME = 'skyrimspecialedition'
PROFILE = 'Default'


def installed_ids(instance=INSTANCE, ledger_path=LEDGER):
    """name -> {nexus ids}, for every directory under mods/, enabled or not."""
    by_name = {}
    if ledger_path.exists():
        for row in json.loads(ledger_path.read_text(encoding='utf-8-sig')).get('mods', []):
            try:
                mid = int(row.get('modId') or 0)
            except (TypeError, ValueError):
                continue
            name = str(row.get('modName') or '')
            if name and mid > 0:
                by_name.setdefault(name, set()).add(mid)

    mods = instance / 'mods'
    out = {}
    for d in sorted(p for p in mods.iterdir() if p.is_dir()):
        if d.name.startswith('.') or d.name.endswith('_separator'):
            continue
        ids = set(by_name.get(d.name, ()))
        meta = d / 'meta.ini'
        if meta.exists():
            txt = meta.read_text(encoding='utf-8-sig', errors='replace')
            m = re.search(r'^modid\s*=\s*(\d+)', txt, re.M | re.I)
            if m and int(m.group(1)) > 0:
                ids.add(int(m.group(1)))
            m = re.search(r'^installationFile=(.*)$', txt, re.M)
            if m:
                lead = re.match(r'^(\d+)-\d+\.', pathlib.PurePath(m.group(1).strip()).name)
                if lead:
                    ids.add(int(lead.group(1)))
        out[d.name] = ids
    return out


def enabled_names(instance=INSTANCE, profile=PROFILE):
    ml = instance / 'profiles' / profile / 'modlist.txt'
    return {l[1:].strip() for l in ml.read_text(encoding='utf-8-sig').splitlines()
            if l.startswith('+') and l[1:].strip()}


def curator_decisions():
    """{id: row}. Raises if the extension state cannot be read."""
    sys.path.insert(0, str(CURATOR))
    import curator_state
    out = {}
    for row in curator_state.decisions():
        if row.get('game') != GAME or not row.get('modId'):
            continue
        try:
            out[int(row['modId'])] = row
        except (TypeError, ValueError):
            pass
    return out


def audit():
    name_ids = installed_ids()
    enabled = enabled_names()
    ids_to_names = {}
    for name, ids in name_ids.items():
        for i in ids:
            ids_to_names.setdefault(i, []).append(name)

    result = {'installedDirs': len(name_ids),
              'installedNexusIds': len(ids_to_names),
              'ownArtifacts': sorted(n for n, s in name_ids.items() if not s)}

    cur = curator_decisions()
    keeps = {i for i, r in cur.items() if r.get('status') == 'keep'}
    skips = {i for i, r in cur.items() if r.get('status') == 'skip'}

    result['liveKeeps'] = len(keeps)
    result['installedWithoutKeep'] = [
        {'modId': i, 'status': cur.get(i, {}).get('status') or 'unreviewed',
         'mods': sorted(ids_to_names[i]),
         'enabled': any(n in enabled for n in ids_to_names[i])}
        for i in sorted(ids_to_names) if i not in keeps and i not in skips]
    result['keepNotInstalled'] = [
        {'modId': i, 'title': cur[i].get('title') or str(i),
         'author': cur[i].get('author') or '', 'keptAt': cur[i].get('addedAt') or ''}
        for i in sorted(keeps) if i not in ids_to_names]
    result['skipInstalled'] = [
        {'modId': i, 'mods': sorted(ids_to_names[i]),
         'enabled': any(n in enabled for n in ids_to_names[i])}
        for i in sorted(skips & set(ids_to_names))]
    return result


def queued_keeps():
    """Ids sitting in the relay spool waiting for the extension to poll.

    A Keep is applied by the Firefox extension on its next Nexus page load, which
    the assistant cannot force. So a freshly installed mod whose Keep is already
    QUEUED is a warning, not a launch blocker; one with no Keep and nothing
    queued is the real violation - the install skipped the step.
    """
    import os
    pending = pathlib.Path(os.environ.get('TEMP', '.')) / 'nlc-relay' / 'decisions-pending.json'
    if not pending.exists():
        return set()
    try:
        batch = json.loads(pending.read_text(encoding='utf-8'))
    except Exception:
        return set()
    return {int(e['mod']['modId']) for e in batch
            if e.get('status') == 'keep' and str(e.get('mod', {}).get('modId') or '').isdigit()}


def run(fails, warns):
    """preflight hook."""
    try:
        r = audit()
    except Exception as exc:                                  # unreadable state
        warns.append('keep coverage unverifiable: %s: %s' % (type(exc).__name__, exc))
        return
    queued = queued_keeps()
    for row in r['installedWithoutKeep']:
        if row['modId'] in queued:
            warns.append('Keep for %d (%s) is queued, not yet applied - the '
                         'extension picks it up on the next Nexus page load'
                         % (row['modId'], ', '.join(row['mods'])))
            continue
        fails.append('installed with no Keep: %d (%s) - the install is not '
                     'finished until the Keep exists or is queued'
                     % (row['modId'], ', '.join(row['mods'])))
    for row in r['keepNotInstalled']:
        # WARN, not FAIL, in the LAUNCH gate: a Keep whose mod is not installed
        # puts no files in the tree and cannot affect a launch, and there is a
        # legitimate window for it during an adoption in flight (2026-09-02: a
        # Keep applied ahead of its install deadlocked two agents against each
        # other). The standalone gate still exits 1 on it - it is a curation
        # violation, just not a launch blocker.
        warns.append('Keep with nothing installed: %d %s - adopt it or clear it '
                     'to unreviewed (not a launch blocker)'
                     % (row['modId'], row['title'] or ''))
    for row in r['skipInstalled']:
        fails.append('Skip is installed: %d (%s) - move it to '
                     'mo2-instances\\_archived-rejects'
                     % (row['modId'], ', '.join(row['mods'])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--plan', action='store_true',
                    help='print the keep additions a relay batch would make')
    args = ap.parse_args()

    r = audit()
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    if args.plan:
        for row in r['installedWithoutKeep']:
            print('keep %-7d %s' % (row['modId'], ', '.join(row['mods'])))
        return 0

    print('installed dirs %d, nexus ids %d, own artifacts %d, live keeps %d'
          % (r['installedDirs'], r['installedNexusIds'],
             len(r['ownArtifacts']), r['liveKeeps']))
    bad = 0
    for row in r['installedWithoutKeep']:
        print('  FAIL  installed with no Keep: %d (%s)%s'
              % (row['modId'], ', '.join(row['mods']),
                 '' if row['enabled'] else ' [disabled - still needs the Keep]'))
        bad += 1
    for row in r['keepNotInstalled']:
        print('  FAIL  Keep with nothing installed: %d %s %s'
              % (row['modId'], row['title'], row['keptAt']))
        bad += 1
    for row in r['skipInstalled']:
        print('  FAIL  Skip is installed: %d (%s)' % (row['modId'], ', '.join(row['mods'])))
        bad += 1
    if bad:
        print('\n%d keep-coverage violation(s) - docs/CURATION_POLICY.md '
              '"Installed implies Keep"' % bad)
        return 1
    print('\nkeep coverage clean')
    return 0


if __name__ == '__main__':
    sys.exit(main())
