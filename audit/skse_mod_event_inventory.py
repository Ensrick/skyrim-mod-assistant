"""Read-only inventory of modern SKSE PLGN/MCBR records. Never rewrites saves.

Contract: pinned fork InternalSerialization.cpp and PapyrusEvents.h, serialized
strings from Serialization.cpp. This reports saved handles, not live VM identity
or proof that a callback will execute. Unknown versions/layouts fail explicitly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAX_BYTES = 256 * 1024 * 1024


class Reader:
    def __init__(self, raw):
        self.raw = memoryview(raw)
        self.offset = 0

    def take(self, count):
        if count < 0 or count > len(self.raw) - self.offset:
            raise ValueError('truncated field')
        start = self.offset
        self.offset += count
        return self.raw[start:self.offset]

    def num(self, fmt):
        return struct.unpack('<' + fmt, self.take(struct.calcsize('<' + fmt)))[0]

    def string(self, maximum=256):
        length = self.num('H')
        if not 0 < length <= maximum:
            raise ValueError('unsupported saved string length')
        raw = bytes(self.take(length))
        if b'\0' in raw:
            raise ValueError('embedded NUL in saved string')
        return raw.decode('utf-8')

    def end(self):
        if self.offset != len(self.raw):
            raise ValueError('trailing record bytes')


def inspect(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('co-save exceeds inspection limit')
    file = Reader(raw)
    if bytes(file.take(4)) != b'SKSE' or file.num('I') != 1:
        raise ValueError('unsupported SKSE wrapper')
    skse, runtime, count = file.num('I'), file.num('I'), file.num('I')
    if count > (len(raw) - file.offset) // 12:
        raise ValueError('impossible plugin count')
    core = None
    for _ in range(count):
        uid, chunks, length = file.num('I'), file.num('I'), file.num('I')
        block = Reader(file.take(length))
        if chunks > length // 12:
            raise ValueError('impossible chunk count')
        records = []
        for _ in range(chunks):
            kind, version, size = block.num('I'), block.num('I'), block.num('I')
            records.append((kind.to_bytes(4, 'big').decode('ascii', errors='replace'), version, block.take(size)))
        block.end()
        if uid == 0:
            if core is not None:
                raise ValueError('duplicate SKSE core block')
            core = records
    file.end()
    if core is None:
        raise ValueError('missing SKSE core block')
    plugins, events = {}, []
    modern, mod_events, found_events = False, False, False
    max_name = 0
    for kind, version, payload in core:
        record = Reader(payload)
        if kind == 'PLGN':
            if modern or version != 0:
                raise ValueError('duplicate or unsupported PLGN')
            modern = True
            total = record.num('H')
            if total > 254 + 4096:
                raise ValueError('too many saved plugins')
            for _ in range(total):
                index = record.num('B')
                if index == 0xFE:
                    light = record.num('H')
                    if light >= 4096:
                        raise ValueError('invalid light index')
                    index = 0xFE000 | light
                elif index >= 254:
                    raise ValueError('invalid full index')
                name = record.string(259)
                max_name = max(max_name, len(name.encode('utf-8')))
                if index in plugins:
                    raise ValueError('duplicate saved index')
                plugins[index] = name
            record.end()
        elif kind in ('MODS', 'LMOD', 'LIMD'):
            raise ValueError('legacy plugin table unsupported by this diagnostic')
        elif kind == 'MCBR':
            if mod_events or found_events or version != 1 or len(payload):
                raise ValueError('duplicate or unsupported MCBR')
            mod_events, found_events = True, True
        elif mod_events:
            if kind == 'REGE':
                if version != 1 or len(payload):
                    raise ValueError('invalid mod-event terminator')
                mod_events = False
            elif kind == 'REGS' and version == 1:
                event, total = record.string(), record.num('I')
                if total > (len(payload) - record.offset) // 11:
                    raise ValueError('impossible registration count')
                for _ in range(total):
                    handle, callback = record.num('Q'), record.string()
                    events.append(dict(event=event, handle=f'{handle:016X}', callback=callback))
                record.end()
            else:
                raise ValueError('unexpected chunk inside mod-event registrations')
    if mod_events or not modern or not found_events:
        raise ValueError('incomplete modern plugin/event records')
    for event in events:
        handle = int(event['handle'], 16)
        mod = (handle >> 24) & 0xFF
        index = ((handle >> 12) & 0xFFFFF) if mod == 0xFE else mod
        event.update(savedIndex=f'{index:X}', formID=f'{handle & 0xFFFFFFFF:08X}',
                     savedPlugin=plugins.get(index), dynamic=(mod == 0xFF))
    return dict(skseVersion=f'{skse:08X}', runtime=f'{runtime:08X}',
                savedPlugins=len(plugins), maxPluginNameBytes=max_name,
                registrations=events, sha256=hashlib.sha256(raw).hexdigest().upper())


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('cosave', type=Path)
    cli.add_argument('--event')
    args = cli.parse_args()
    if args.cosave.stat().st_size > MAX_BYTES:
        cli.error('co-save exceeds inspection limit')
    result = inspect(args.cosave.read_bytes())
    result['totalRegistrations'] = len(result['registrations'])
    if args.event:
        result['registrations'] = [row for row in result['registrations'] if row['event'] == args.event]
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
