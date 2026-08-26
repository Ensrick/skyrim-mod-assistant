"""Verify every active plugin's masters are present and load earlier.

Run: py -3 audit/verify_order.py        (exit 0 clean, 2 on any violation)

A missing or late-loading master is a launch-blocker or a guaranteed CTD, and
neither MO2 2.5.2 nor the game warns usefully at 1.7.99. This reads the TES4
header of every starred plugin straight off disk, resolving each name through
the same search order the VFS presents: enabled mod folders by descending MO2
priority, then the real game Data directory.

Born 2026-08-26 after two worldspace installs; the check previously lived in a
throwaway script, which is exactly why it kept getting skipped.
"""
import io, os, struct, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
GAME_DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
PROFILE = os.path.join(INSTANCE, 'profiles', 'Default')


def masters_of(path):
    """MAST entries from a plugin's TES4 header, in declaration order."""
    with open(path, 'rb') as fh:
        head = fh.read(24)
        if head[:4] != b'TES4':
            raise ValueError('not a plugin')
        body = fh.read(struct.unpack_from('<I', head, 4)[0])
    out, sp = [], 0
    while sp + 6 <= len(body):
        st = body[sp:sp + 4]
        ssz = struct.unpack_from('<H', body, sp + 4)[0]
        if st == b'MAST':
            out.append(body[sp + 6:sp + 6 + ssz - 1].decode('cp1252', 'replace'))
        sp += 6 + ssz
    return out


def implicit_masters():
    """Plugins the engine loads without a plugins.txt entry.

    Vanilla masters, the DLC, and every Creation Club item shipped with the AE
    install sit in the real Data directory and always load before the managed
    list. Treating them as absent is the classic false alarm.
    """
    if not os.path.isdir(GAME_DATA):
        return set()
    return {fn.lower() for fn in os.listdir(GAME_DATA)
            if fn.lower().endswith(('.esp', '.esm', '.esl'))}


def build_index():
    """Data-relative plugin name -> file path, honouring MO2 load priority.

    modlist.txt is highest-priority-first, so the FIRST enabled mod that ships a
    plugin wins; the game Data dir is the last resort (vanilla + CC).
    """
    index = {}
    ml = io.open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8').read().splitlines()
    for line in ml:
        if not line.startswith('+'):
            continue
        d = os.path.join(INSTANCE, 'mods', line[1:])
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.lower().endswith(('.esp', '.esm', '.esl')):
                index.setdefault(fn.lower(), os.path.join(d, fn))
    if os.path.isdir(GAME_DATA):
        for fn in os.listdir(GAME_DATA):
            if fn.lower().endswith(('.esp', '.esm', '.esl')):
                index.setdefault(fn.lower(), os.path.join(GAME_DATA, fn))
    return index


def main():
    index = build_index()
    implicit = implicit_masters()
    starred = [l[1:] for l in io.open(os.path.join(PROFILE, 'plugins.txt'), encoding='utf-8')
               .read().splitlines() if l.startswith('*')]
    pos = {n.lower(): i for i, n in enumerate(starred)}
    missing_file, missing_master, order_viol, unreadable = [], [], [], []
    for name in starred:
        path = index.get(name.lower())
        if not path:
            missing_file.append(name)
            continue
        try:
            ms = masters_of(path)
        except Exception as ex:
            unreadable.append((name, str(ex)))
            continue
        for m in ms:
            mp = pos.get(m.lower())
            if mp is None:
                # implicit base/CC masters always load first; anything else
                # absent from the active list genuinely will not be there
                if m.lower() not in implicit:
                    missing_master.append((name, m))
            elif mp >= pos[name.lower()]:
                order_viol.append((name, m))
    print(f'{len(starred)} active plugins, {len(index)} discoverable')
    for n in missing_file:
        print(f'   NO PROVIDER   {n} is active but no enabled mod or Data dir ships it')
    for n, m in missing_master:
        print(f'   MISSING MASTER {n} needs {m}')
    for n, m in order_viol:
        print(f'   ORDER          {n} loads before its master {m}')
    for n, ex in unreadable:
        print(f'   UNREADABLE     {n}: {ex}')
    bad = len(missing_file) + len(missing_master) + len(order_viol) + len(unreadable)
    print('CLEAN' if not bad else f'{bad} problem(s)')
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
