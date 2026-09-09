"""Read-only SSE save admission check: missing plugins forbid automated reload.

This checks the serialized plugin table, NOT Papyrus integrity or full save
compatibility. Never edits saves. Format references (independent implementation):
FallrimTools Header.java, ESS.java and PluginInfo.java at
https://github.com/mdfairch/FallrimTools/tree/main/src/main/java/resaver/ess
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAX_BYTES = 256 * 1024 * 1024
DEFAULT_GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition')


class InvalidSave(ValueError):
    pass


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise InvalidSave('truncated save field')
        data = self.data[self.pos:self.pos + size]
        self.pos += size
        return data

    def num(self, fmt):
        return struct.unpack('<' + fmt, self.take(struct.calcsize('<' + fmt)))[0]

    def string(self):
        return self.take(self.num('H')).decode('utf-8', errors='strict')


def lz4_decode(data, expected):
    """Bounded raw block decoder, including overlapping matches."""
    r, out = Reader(data), bytearray()

    def length(n):
        if n == 15:
            while True:
                extra = r.num('B')
                n += extra
                if extra != 255:
                    break
        return n

    while r.pos < len(data):
        token = r.num('B')
        literal = length(token >> 4)
        if len(out) + literal > expected:
            raise InvalidSave('LZ4 output exceeds declared size')
        out.extend(r.take(literal))
        if r.pos == len(data):
            break
        offset = r.num('H')
        match = length(token & 15) + 4
        if not offset or offset > len(out) or len(out) + match > expected:
            raise InvalidSave('invalid LZ4 match')
        # Repeating the preceding offset-byte window handles overlap without
        # a Python iteration per output byte; allocation remains bounded.
        window = out[-offset:]
        out.extend((window * ((match + offset - 1) // offset))[:match])
    if len(out) != expected:
        raise InvalidSave('LZ4 size mismatch')
    return bytes(out)


def parse(data):
    if len(data) > MAX_BYTES:
        raise InvalidSave('save exceeds reader safety limit')
    r = Reader(data)
    if r.take(13) != b'TESV_SAVEGAME':
        raise InvalidSave('not a Skyrim save')
    header = Reader(r.take(r.num('I')))
    version = header.num('I')
    if version != 12:
        raise InvalidSave(f'unsupported SSE save header version {version}')
    number, name, level = header.num('I'), header.string(), header.num('I')
    location, date, race = header.string(), header.string(), header.string()
    header.take(2 + 4 + 4 + 8)  # sex, current XP, required XP, FILETIME
    width, height, compression = header.num('I'), header.num('I'), header.num('H')
    if header.pos != len(header.data):
        raise InvalidSave('unrecognized header extension')
    r.take(width * height * 4)
    if compression:
        size, packed_size = r.num('I'), r.num('I')
        if not 0 < size <= MAX_BYTES:
            raise InvalidSave('invalid decompressed size')
        packed = r.take(packed_size)
        if r.pos != len(data):
            raise InvalidSave('trailing compressed save data')
        if compression == 1:
            decoder = zlib.decompressobj()
            body = decoder.decompress(packed, size + 1)
            if (len(body) != size or not decoder.eof or decoder.unused_data
                    or decoder.unconsumed_tail):
                raise InvalidSave('invalid zlib payload/size')
        elif compression == 2:
            body = lz4_decode(packed, size)
        else:
            raise InvalidSave(f'unknown compression {compression}')
    else:
        body = r.take(len(data) - r.pos)
    b = Reader(body)
    form_version = b.num('B')
    if form_version < 78:
        raise InvalidSave(f'unsupported SSE form version {form_version}')
    p = Reader(b.take(b.num('I')))
    full = [p.string() for _ in range(p.num('B'))]
    light = [p.string() for _ in range(p.num('H'))]
    if not full or len(light) > 4096 or p.pos != len(p.data):
        raise InvalidSave('invalid plugin table')
    names = full + light
    if any(not n.lower().endswith(('.esm', '.esp', '.esl')) for n in names):
        raise InvalidSave('invalid plugin filename')
    if len(set(n.casefold() for n in names)) != len(names):
        raise InvalidSave('duplicate plugin table entry')
    return dict(version=version, form_version=form_version, number=number,
                name=name, level=level, location=location, game_date=date,
                race=race, compression=compression, full=full, light=light)


def inspect(path):
    path = Path(path)
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    result = parse(data)
    result.update(save=str(path), sha256=hashlib.sha256(data).hexdigest())
    return result


def active_plugins(profile, game=DEFAULT_GAME):
    # MO2 uses '*' for active plugins, not '+' (which is modlist.txt).
    lines = (Path(profile) / 'plugins.txt').read_text(encoding='utf-8-sig').splitlines()
    active = {line[1:].strip().casefold() for line in lines if line.startswith('*')}
    # Engine-forced base masters can be omitted/unstarred in plugins.txt.
    active.update(n.casefold() for n in ('Skyrim.esm', 'Update.esm',
                  'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm'))
    # Official Creations listed in Skyrim.ccc are engine-forced too. Do not
    # treat every cc*.esl filename as forced; use the actual manifest and files.
    ccc = Path(game) / 'Skyrim.ccc'
    if ccc.exists():
        for line in ccc.read_text(encoding='utf-8-sig').splitlines():
            name = line.strip()
            if name and Path(name).name == name and (Path(game) / 'Data' / name).is_file():
                active.add(name.casefold())
    return active


def compare(result, active):
    return [n for n in result['full'] + result['light'] if n.casefold() not in active]


def check_save(profile, save):
    if save is None:
        return []  # no load requested; does not certify a new game
    try:
        missing = compare(inspect(save), active_plugins(profile))
    except (OSError, ValueError, struct.error, zlib.error) as exc:
        return [f'save admission cannot inspect {save}: {exc}']
    if missing:
        return ['save admission REFUSED: save contains removed/inactive plugins: '
                + ', '.join(missing) + '. Use a truly new test character; do not '
                'dismiss missing-content warnings or clean the original save.']
    return []


def saves_directory(profile, global_saves):
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(Path(profile) / 'settings.ini', encoding='utf-8-sig')
    local = settings.getboolean('General', 'LocalSaves', fallback=False)
    return Path(profile) / 'saves' if local else Path(global_saves)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--game', type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    try:
        result = inspect(args.save)
        result['missing_plugins'] = compare(result, active_plugins(args.profile, args.game))
        result['verdict'] = 'REFUSED' if result['missing_plugins'] else 'PLUGIN-TABLE-OK'
        result['scope'] = 'Plugin presence only; not proof of save health or script compatibility.'
        print(json.dumps(result, indent=2))
        return 1 if result['missing_plugins'] else 0
    except (OSError, ValueError, struct.error, zlib.error) as exc:
        print(json.dumps(dict(verdict='REFUSED', error=str(exc))))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
