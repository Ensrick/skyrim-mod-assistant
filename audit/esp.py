"""Read Bethesda plugins far enough to answer "what is this item and where does
it go on the body".

Only what the audit needs: ARMO/ARMA equip slots and their model paths, plus
masters and record counts. Handles compressed records and the XXXX oversize
subrecord.
"""
import struct, zlib, os, re

# Biped slots. 30-49 are Bethesda's; 50+ are conventions mods settled on, so
# they are labelled loosely on purpose.
SLOTS = {
    30: 'head', 31: 'hair', 32: 'body', 33: 'hands', 34: 'forearms',
    35: 'amulet', 36: 'ring', 37: 'feet', 38: 'calves', 39: 'shield',
    40: 'tail', 41: 'long hair', 42: 'circlet', 43: 'ears', 44: 'face/mouth',
    45: 'neck', 46: 'chest (cloak slot)', 47: 'back (pack slot)', 48: 'misc',
    49: 'pelvis', 50: 'decapitated head', 51: 'decapitate', 52: 'pelvis 2',
    53: 'leg 1', 54: 'leg 2', 55: 'face alt', 56: 'behind', 57: 'misc 57',
    58: 'misc 58', 59: 'misc 59', 60: 'misc 60', 61: 'fx01',
}
ARMOR_TYPE = {0: 'light', 1: 'heavy', 2: 'clothing'}

# Slots where loose cloth is the point of the item, so rigidity actually shows.
CLOTH_SLOTS = {40, 45, 46, 47, 31, 41}


def _subrecords(data):
    p, n = 0, len(data)
    pending = None
    while p + 6 <= n:
        typ = data[p:p + 4]
        size = struct.unpack_from('<H', data, p + 4)[0]
        p += 6
        if typ == b'XXXX':                       # real size lives in the payload
            pending = struct.unpack_from('<I', data, p)[0]
            p += size
            continue
        if pending is not None:
            size, pending = pending, None
        yield typ, data[p:p + size]
        p += size


def _zstring(b):
    return b.split(b'\x00')[0].decode('cp1252', 'replace')


class Plugin:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.raw = open(path, 'rb').read()
        self.masters = []
        self.records = {}
        self.armo = []
        self.arma = []
        self._parse()

    def _parse(self):
        d = self.raw
        # TES4 header first
        if d[:4] != b'TES4':
            raise ValueError('not a plugin')
        size = struct.unpack_from('<I', d, 4)[0]
        self.header_flags = struct.unpack_from('<I', d, 8)[0]
        self.esl = bool(self.header_flags & 0x200)
        for typ, payload in _subrecords(d[24:24 + size]):
            if typ == b'MAST':
                self.masters.append(_zstring(payload))
        self._walk(24 + size, len(d))

    def _walk(self, start, end):
        d = self.raw
        p = start
        while p + 24 <= end:
            typ = d[p:p + 4]
            size = struct.unpack_from('<I', d, p + 4)[0]
            if typ == b'GRUP':
                self._walk(p + 24, min(p + size, end))
                p += size
                continue
            flags = struct.unpack_from('<I', d, p + 8)[0]
            body = d[p + 24:p + 24 + size]
            if flags & 0x00040000 and len(body) > 4:      # compressed record
                try:
                    body = zlib.decompress(body[4:])
                except zlib.error:
                    body = b''
            self.records[typ] = self.records.get(typ, 0) + 1
            if typ in (b'ARMO', b'ARMA'):
                self._item(typ, body)
            p += 24 + size

    def _item(self, typ, body):
        rec = {'edid': None, 'name': None, 'slots': [], 'armor_type': None,
               'models': [], 'type': typ.decode()}
        for st, payload in _subrecords(body):
            if st == b'EDID':
                rec['edid'] = _zstring(payload)
            elif st == b'FULL':
                rec['name'] = _zstring(payload)
            elif st in (b'BOD2', b'BODT') and len(payload) >= 8:
                mask = struct.unpack_from('<I', payload, 0)[0]
                rec['slots'] = [30 + i for i in range(32) if mask & (1 << i)]
                if st == b'BOD2' and len(payload) >= 8:
                    rec['armor_type'] = ARMOR_TYPE.get(struct.unpack_from('<I', payload, 4)[0])
                elif len(payload) >= 12:
                    rec['armor_type'] = ARMOR_TYPE.get(struct.unpack_from('<I', payload, 8)[0])
            elif st in (b'MOD2', b'MOD3', b'MOD4', b'MOD5', b'MODL'):
                s = _zstring(payload)
                if s.lower().endswith('.nif'):
                    rec['models'].append(s.replace('\\', '/').lower())
        if rec['slots'] or rec['models']:
            (self.armo if typ == b'ARMO' else self.arma).append(rec)


def describe(rec):
    slots = [SLOTS.get(s, str(s)) for s in rec['slots']]
    return f"{rec.get('name') or rec.get('edid') or '?'} [{', '.join(slots) or 'no slot'}]"


def classify(rec):
    """What kind of wearable this is, from slot plus naming."""
    txt = ((rec.get('name') or '') + ' ' + (rec.get('edid') or '') + ' ' +
           ' '.join(rec.get('models') or [])).lower()
    for pat, label in [
        (r'cloak|cape|mantle', 'cloak/cape'),
        (r'skirt|dress|gown|robe|tunic', 'robe/skirt'),
        (r'tail', 'tail'),
        (r'hair|wig|braid|ponytail', 'hair'),
        (r'ring\b', 'ring'),
        (r'amulet|necklace|pendant|torc', 'amulet'),
        (r'circlet|crown|diadem', 'circlet'),
        (r'helm|hood|mask|cowl', 'headgear'),
        (r'boot|shoe|sandal|greave', 'footwear'),
        (r'gauntlet|glove|bracer', 'handwear'),
        (r'shield', 'shield'),
        (r'backpack|satchel|pack\b|bedroll', 'backpack'),
        (r'cuirass|armor|armour|chest|jerkin|coat', 'body armour'),
    ]:
        if re.search(pat, txt):
            return label
    s = set(rec.get('slots') or [])
    if 36 in s: return 'ring'
    if 35 in s: return 'amulet'
    if 37 in s: return 'footwear'
    if 33 in s: return 'handwear'
    if 30 in s or 42 in s: return 'headgear'
    if 32 in s: return 'body armour'
    return 'other'


def cloth_relevant(rec):
    """Would rigid geometry actually be visible on this item?"""
    kind = classify(rec)
    if kind in ('cloak/cape', 'robe/skirt', 'tail', 'hair'):
        return True
    return bool(set(rec.get('slots') or []) & CLOTH_SLOTS) and kind not in (
        'ring', 'amulet', 'circlet', 'footwear', 'handwear', 'headgear', 'shield')
