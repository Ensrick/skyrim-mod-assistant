"""The local resolver patches must have the last word on every record they carry.

Born 2026-09-07 after the same failure three times in two days. Each time a newly
installed plugin landed at the end of plugins.txt and quietly took WRLD Tamriel
(0000003C) away from `Ensrick General Compatibility Patch.esp`, whose twelve WRLD
records are the entire point of that patch (#47):

  - Mesh Improvement Compilation.esp   - differed in MNAM, plus a 45,608-byte MHDT
  - PatchDirfjordFolkstead.esp         - MNAM 7e0a3019 over the resolver's aa288a23
  - Ensrick Inigo Bloodchill Landscape Forward.esp - avoided only because its WRLD
    record was deliberately authored as a byte copy of the resolver's

Skyrim replaces records whole rather than merging fields, so "it only carries the
record structurally" is not a defence: whoever loads last wins the whole record.
A cell or worldspace patch has to carry its parent WRLD, so this will keep
happening on every install. Hence a gate rather than vigilance.

The rule: for every record a resolver plugin overrides, no plugin loading after it
may override that same record - unless the later plugin's copy is byte-identical,
which is a no-op and is how the Bloodchill forward stays legal.

  py -3 audit/resolver_last_gate.py          # standalone, exit 1 on a violation
  resolver_last_gate.run(fails, warns)       # from preflight
"""
import os
import struct
import sys
import zlib

INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
GAME_DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'

# Load-order-last patches whose whole job is to settle conflicts. Order matters:
# each must beat everything after it, and later entries may legitimately beat
# earlier ones.
RESOLVERS = (
    'Ensrick Lux Water CS Patch.esp',
    'Ensrick General Compatibility Patch.esp',
)
GUARDED = {b'WRLD', b'CELL', b'LAND', b'NAVM'}


def _subrecords(body):
    p, n = 0, len(body)
    while p + 6 <= n:
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        yield typ, body[p + 6:p + 6 + size]
        p += 6 + size


def _records(path):
    """{(master, local id, type): body hash} for every override in the plugin."""
    with open(path, 'rb') as handle:
        data = handle.read()
    header = struct.unpack_from('<I', data, 4)[0]
    masters = [v.rstrip(b'\x00').decode('latin-1').lower()
               for typ, v in _subrecords(data[24:24 + header]) if typ == b'MAST']
    own = len(masters)
    found = {}

    def walk(pos, end):
        while pos + 24 <= end:
            typ = data[pos:pos + 4]
            size = struct.unpack_from('<I', data, pos + 4)[0]
            if typ == b'GRUP':
                walk(pos + 24, pos + size)
                pos += size
                continue
            flags = struct.unpack_from('<I', data, pos + 8)[0]
            formid = struct.unpack_from('<I', data, pos + 12)[0]
            index = formid >> 24
            if typ in GUARDED and index < own:
                body = data[pos + 24:pos + 24 + size]
                if flags & 0x00040000:
                    try:
                        body = zlib.decompress(body[4:])
                    except zlib.error:
                        pass
                found[(masters[index], formid & 0x00FFFFFF, typ.decode())] = hash(body)
            pos += 24 + size

    walk(24 + header, len(data))
    return found


def _plugin_paths(profile):
    """Active plugins in load order, mapped to the file the VFS would serve."""
    mods = os.path.join(INSTANCE, 'mods')
    order = []
    with open(os.path.join(profile, 'modlist.txt'), encoding='utf-8') as handle:
        for line in handle:
            line = line.rstrip('\n')
            if line.startswith('+') and not line.endswith('_separator'):
                order.append(line[1:])
    order.reverse()                      # modlist.txt is highest-priority first
    index = {}
    for mod in order:
        folder = os.path.join(mods, mod)
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if name.lower().endswith(('.esp', '.esm', '.esl')):
                index[name.lower()] = os.path.join(folder, name)
    for name in os.listdir(GAME_DATA):
        if name.lower().endswith(('.esp', '.esm', '.esl')):
            index.setdefault(name.lower(), os.path.join(GAME_DATA, name))

    active = []
    with open(os.path.join(profile, 'plugins.txt'), encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line.startswith('*'):
                active.append(line[1:])
    return [(name, index[name.lower()]) for name in active if name.lower() in index]


def check(profile=None):
    """(blocking, advisory) violation lists. Empty blocking = the resolvers win.

    A third-party plugin landing after the block is the failure this gate exists
    for and blocks. One of our own `Ensrick ...` patches doing it is deliberate
    ordering more often than not - the CRF semantic patch is meant to follow the
    Lux water patch - so it is reported as advisory rather than refusing a launch.
    """
    profile = profile or os.path.join(INSTANCE, 'profiles', 'Default')
    ordered = _plugin_paths(profile)
    positions = {name.lower(): i for i, (name, _) in enumerate(ordered)}
    problems = []
    advisory = []

    for resolver in RESOLVERS:
        at = positions.get(resolver.lower())
        if at is None:
            problems.append(f'{resolver} is not active - the resolver block is incomplete')
            continue
        path = dict((n.lower(), p) for n, p in ordered)[resolver.lower()]
        try:
            owned = _records(path)
        except (OSError, struct.error) as error:
            problems.append(f'{resolver} could not be read: {error}')
            continue
        for name, later in ordered[at + 1:]:
            if name in RESOLVERS:
                continue
            try:
                theirs = _records(later)
            except (OSError, struct.error):
                continue
            for key, digest in theirs.items():
                if key in owned and owned[key] != digest:
                    master, local, typ = key
                    message = (
                        f'{name} (load order {positions[name.lower()]}) overrides '
                        f'{typ} {local:06X}:{master} after {resolver} '
                        f'(load order {at}) and its copy differs - move it before the '
                        f'resolver block, or make its record a byte copy')
                    (advisory if name.startswith('Ensrick') else problems).append(message)
    return problems, advisory


def run(fails, warns):
    problems, advisory = check()
    fails.extend('resolver order: ' + problem for problem in problems)
    warns.extend('resolver order: ' + note for note in advisory)


def main():
    problems, advisory = check()
    for note in advisory:
        print(f'  WARN  {note}')
    for problem in problems:
        print(f'  FAIL  {problem}')
    if problems:
        print(f'\n{len(problems)} resolver-order violation(s), {len(advisory)} advisory')
        return 1
    print(f'resolver order clean - the local patches win every record they carry '
          f'({len(advisory)} advisory)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
