"""Build "Ensrick Inigo Bloodchill Landscape Forward.esp".

Inigo.esp lists only Skyrim.esm and Update.esm as masters, so the Creation Kit
wrote its LAND 00009FC4 and NAVM 001062F7 records from the Skyrim.esm versions.
That silently reverts Dawnguard.esm's edits to that cell: Dawnguard digs the
ravine the Bloodchill Cavern entrance (Creation Club, ccEEJSSE005-Cave.esm)
sits in, and Inigo's copies fill it back in. The entrance ends up under 500-800
units of hillside, and the navmesh over it is the vanilla hillside too, so
followers cannot path to the door.

The fix is a straight conflict forward of Bethesda's own records, loaded after
Inigo.esp:

  WRLD 0000003C  copied from the current WRLD Tamriel winner (structural parent)
  CELL 00008FC4  copied from Inigo.esp   (structural parent; XLCN remapped)
  LAND 00009FC4  copied from Dawnguard.esm
  NAVM 001062F7  copied from Dawnguard.esm

Skyrim replaces records whole, not field by field, so the structural WRLD
parent this file has to carry would beat the real WRLD Tamriel winner if the
plugin ever sorted last. It is therefore copied from that winner - today
"Ensrick General Compatibility Patch.esp" (#47), whose 12 WRLD records are the
point of that patch - so the record is a no-op wherever this plugin lands. Its
WRLD Tamriel holds only Skyrim.esm formids, so no extra master is pulled in.
Re-run this script if that patch is ever regenerated with different WRLD data.

Nothing is authored here: every record is a byte copy of a record already on
disk. The only edit is the CELL's XLCN (location) formid, whose master index
moves from 02 (Inigo's own index inside Inigo.esp) to 03 (Inigo's index in this
plugin's master list). Masters are listed in load order, so Skyrim.esm,
Update.esm and Dawnguard.esm keep the indices they use inside Dawnguard.esm and
Inigo.esp, and no other formid needs remapping.

Trade-off, deliberate: Inigo's NAVM added 4 vertices / 8 triangles around three
stone-wall statics he places at (65200, 68400), ~3000 units from the entrance.
Forwarding Dawnguard's navmesh drops those, so NPCs may clip that wall corner.
Dawnguard's navmesh is what the Creation Club home was built against.

    py -3 build.py [--out <mod folder>]
"""
import argparse
import os
import struct
import sys
import zlib

DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
MODS = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\mods'
DAWNGUARD = os.path.join(DATA, 'Dawnguard.esm')
INIGO = os.path.join(MODS, 'INIGO', 'Inigo.esp')
WRLD_WINNER = os.path.join(MODS, 'Ensrick - General Compatibility Patch',
                           'Ensrick General Compatibility Patch.esp')

PLUGIN = 'Ensrick Inigo Bloodchill Landscape Forward.esp'
AUTHOR = 'Ensrick'
SUMMARY = 'Forwards Dawnguard LAND 00009FC4 and NAVM 001062F7 over Inigo.esp'
MASTERS = ['Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'Inigo.esp']

WRLD_TAMRIEL = 0x0000003C
CELL_LANGLEYPATH3 = 0x00008FC4
LAND_LANGLEYPATH3 = 0x00009FC4
NAVM_LANGLEYPATH3 = 0x001062F7
INIGO_OWN_INDEX = 0x02          # Inigo.esp has two masters, so its own forms are 02
PATCH_INIGO_INDEX = 0x03        # Inigo.esp is the fourth master here

COMPRESSED = 0x00040000
ESL_FLAG = 0x00000200


def subrecords(body):
    """Yield (type, payload, whole-subrecord-bytes) honouring XXXX oversize."""
    p, n, pending = 0, len(body), None
    while p + 6 <= n:
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        head = p
        p += 6
        if typ == b'XXXX':
            pending = struct.unpack_from('<I', body, p)[0]
            p += size
            continue
        if pending is not None:
            size, pending = pending, None
        yield typ, body[p:p + size], body[head:p + size]
        p += size


def read_plugin(path, wanted):
    """Return {(type, formid): (raw record bytes, group stack)} for the wanted records."""
    data = open(path, 'rb').read()
    found = {}

    def walk(pos, end, stack):
        while pos + 24 <= end:
            typ = data[pos:pos + 4]
            size = struct.unpack_from('<I', data, pos + 4)[0]
            if typ == b'GRUP':
                walk(pos + 24, pos + size, stack + [data[pos:pos + 24]])
                pos += size
                continue
            formid = struct.unpack_from('<I', data, pos + 12)[0]
            if (typ, formid) in wanted:
                found[(typ, formid)] = (data[pos:pos + 24 + size], stack)
            pos += 24 + size

    walk(24 + struct.unpack_from('<I', data, 4)[0], len(data), [])
    missing = wanted - set(found)
    if missing:
        raise SystemExit(f'{path}: missing {[(t.decode(), f"{f:08X}") for t, f in missing]}')
    return found


def record_body(raw):
    size = struct.unpack_from('<I', raw, 4)[0]
    flags = struct.unpack_from('<I', raw, 8)[0]
    body = raw[24:24 + size]
    if flags & COMPRESSED:
        body = zlib.decompress(body[4:])
    return flags, body


def rebuild(raw, body):
    """Re-emit a record with a new, uncompressed body."""
    head = bytearray(raw[:24])
    struct.pack_into('<I', head, 4, len(body))
    flags = struct.unpack_from('<I', head, 8)[0] & ~COMPRESSED
    struct.pack_into('<I', head, 8, flags)
    return bytes(head) + body


def remap_cell_location(raw):
    """Point the CELL's XLCN at Inigo's location through this plugin's master list."""
    _, body = record_body(raw)
    out, patched = bytearray(), 0
    for typ, payload, whole in subrecords(body):
        if typ == b'XLCN' and len(payload) == 4:
            formid = struct.unpack('<I', payload)[0]
            if formid >> 24 == INIGO_OWN_INDEX:
                formid = (PATCH_INIGO_INDEX << 24) | (formid & 0x00FFFFFF)
                out += whole[:6] + struct.pack('<I', formid)
                patched += 1
                continue
        out += whole
    if patched != 1:
        raise SystemExit(f'expected exactly one Inigo XLCN in the CELL, patched {patched}')
    return rebuild(raw, bytes(out))


def zstring(text):
    return text.encode('cp1252') + b'\x00'


def subrecord(typ, payload):
    return typ + struct.pack('<H', len(payload)) + payload


def tes4(record_count):
    body = subrecord(b'HEDR', struct.pack('<fiI', 1.71, record_count, 0x800))
    body += subrecord(b'CNAM', zstring(AUTHOR))
    body += subrecord(b'SNAM', zstring(SUMMARY))
    for master in MASTERS:
        body += subrecord(b'MAST', zstring(master))
        body += subrecord(b'DATA', struct.pack('<Q', 0))
    header = b'TES4' + struct.pack('<IIIIHH', len(body), ESL_FLAG, 0, 0, 44, 0)
    return header + body


def group(label, group_type, payload, template=None):
    stamp = template[16:24] if template else struct.pack('<HHHH', 0, 0, 44, 0)
    return b'GRUP' + struct.pack('<I', 24 + len(payload)) + label + struct.pack('<i', group_type) + stamp


def wrap(label, group_type, payload, template=None):
    return group(label, group_type, payload, template) + payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(MODS, 'Ensrick - Inigo Bloodchill Landscape Forward'))
    args = ap.parse_args()

    dawn = read_plugin(DAWNGUARD, {(b'LAND', LAND_LANGLEYPATH3), (b'NAVM', NAVM_LANGLEYPATH3),
                                   (b'CELL', CELL_LANGLEYPATH3)})
    inigo = read_plugin(INIGO, {(b'WRLD', WRLD_TAMRIEL), (b'CELL', CELL_LANGLEYPATH3)})
    wrld_source = WRLD_WINNER if os.path.exists(WRLD_WINNER) else INIGO
    wrld = read_plugin(wrld_source, {(b'WRLD', WRLD_TAMRIEL)})

    land_raw, _ = dawn[(b'LAND', LAND_LANGLEYPATH3)]
    navm_raw, _ = dawn[(b'NAVM', NAVM_LANGLEYPATH3)]
    wrld_raw, _ = wrld[(b'WRLD', WRLD_TAMRIEL)]
    cell_raw, _ = inigo[(b'CELL', CELL_LANGLEYPATH3)]

    for typ, payload, _ in subrecords(record_body(wrld_raw)[1]):
        if len(payload) == 4 and typ in (b'CNAM', b'NAM2', b'NAM3', b'ZNAM'):
            if struct.unpack('<I', payload)[0] >> 24 != 0:
                raise SystemExit(f'{wrld_source}: WRLD {typ.decode()} is not a Skyrim.esm form')
    _, cell_stack = dawn[(b'CELL', CELL_LANGLEYPATH3)]

    # Dawnguard's own group chain for this cell: top WRLD, world children,
    # exterior block, exterior sub-block. Reuse its labels rather than deriving
    # the block coordinates.
    labels = [(g[8:12], struct.unpack_from('<i', g, 12)[0], g) for g in cell_stack]
    kinds = [t for _, t, _ in labels]
    if kinds != [0, 1, 4, 5]:
        raise SystemExit(f'unexpected group chain for the cell: {kinds}')

    cell = remap_cell_location(cell_raw)
    children = wrap(struct.pack('<I', CELL_LANGLEYPATH3), 9, land_raw + navm_raw, labels[3][2])
    cell_children = wrap(struct.pack('<I', CELL_LANGLEYPATH3), 6, children, labels[3][2])
    sub_block = wrap(labels[3][0], 5, cell + cell_children, labels[3][2])
    block = wrap(labels[2][0], 4, sub_block, labels[2][2])
    world_children = wrap(labels[1][0], 1, block, labels[1][2])
    top = wrap(b'WRLD', 0, wrld_raw + world_children, labels[0][2])

    plugin = tes4(4) + top
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, PLUGIN)
    with open(path, 'wb') as fh:
        fh.write(plugin)
    print(f'wrote {path} ({len(plugin)} bytes)')
    print(f'  masters: {", ".join(MASTERS)}')
    print(f'  records: WRLD {WRLD_TAMRIEL:08X} ({os.path.basename(wrld_source)}), '
          f'CELL {CELL_LANGLEYPATH3:08X} (Inigo, XLCN remapped), '
          f'LAND {LAND_LANGLEYPATH3:08X} (Dawnguard), NAVM {NAVM_LANGLEYPATH3:08X} (Dawnguard)')


if __name__ == '__main__':
    main()
