"""Read what a mod actually ships, so overlapping mods can be compared on facts.

Handles the three things that make this awkward:
  * archives (7z/rar/zip) with FOMOD option folders,
  * BSAs, including SSE's LZ4-block-compressed entries (pure-python decoder,
    no dependency), so packed mods index the same as loose ones,
  * DDS and NIF headers, for resolution/format and shape/parallax facts.

Everything is keyed on the Data-relative path, which is what the game actually
resolves and therefore what decides who overwrites whom.
"""
import json, os, re, struct, subprocess, glob, sys, urllib.request, urllib.parse, hashlib

SEVENZ = r'C:\Program Files\7-Zip\7z.exe'
KEY = json.load(open(r'C:\Users\danjo\source\repos\crusader-de-tweaker\scripts\nexus\nexus.local.json'))['ApiKey']
UA = {'apikey': KEY, 'User-Agent': 'SkyrimModAssistant/0.1', 'Accept': 'application/json'}
CACHE = os.path.join(os.environ['TEMP'], 'modassets')
os.makedirs(CACHE, exist_ok=True)


def v1(path):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        'https://api.nexusmods.com/v1/games/skyrimspecialedition' + path, headers=UA), timeout=90))


def _enc(u):
    s = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((s.scheme, s.netloc, urllib.parse.quote(s.path), s.query, s.fragment))


def pick_file(mid, prefer=None, category='MAIN'):
    """Newest file in `category`; `prefer` is a regex to disambiguate variants
    (mods often ship 1K/2K/4K as separate MAIN files)."""
    files = [f for f in v1(f'/mods/{mid}/files.json')['files'] if f['category_name'] == category]
    if not files:
        raise RuntimeError(f'mod {mid}: no {category} file')
    if prefer:
        rx = re.compile(prefer, re.I)
        m = [f for f in files if rx.search(f['name']) or rx.search(f['file_name'])]
        if m:
            files = m
    return sorted(files, key=lambda x: -x['uploaded_timestamp'])[0]


def download(mid, f):
    dest = os.path.join(CACHE, f"{mid}-{f['file_id']}{os.path.splitext(f['file_name'])[1] or '.arc'}")
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        return dest
    links = v1(f"/mods/{mid}/files/{f['file_id']}/download_link.json")
    u = ([l for l in links if l['short_name'] in ('Chicago', 'Dallas', 'Miami')] or links)[0]['URI']
    tmp = dest + '.part'
    with urllib.request.urlopen(urllib.request.Request(
            _enc(u), headers={'User-Agent': 'SkyrimModAssistant/0.1'}), timeout=1800) as r, open(tmp, 'wb') as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    os.replace(tmp, dest)
    return dest


def extract(archive, out):
    if os.path.isdir(out) and os.listdir(out):
        return out
    os.makedirs(out, exist_ok=True)
    p = subprocess.run([SEVENZ, 'x', '-o' + out, archive, '-y', '-bso0', '-bse0'], capture_output=True)
    if p.returncode not in (0, 1, 2):
        raise RuntimeError(f'7z failed {p.returncode}: {p.stderr[:200]}')
    return out


# ---------------------------------------------------------------- LZ4 block
def lz4_frame(src, max_blocks=0):
    """Decode an LZ4 frame (magic 0x184D2204). SSE BSAs wrap each compressed
    entry in a frame, not a bare block."""
    if struct.unpack_from('<I', src, 0)[0] != 0x184D2204:
        raise ValueError('not an LZ4 frame')
    flg, _bd = src[4], src[5]
    p = 6
    if flg & 0x08:                      # content size present
        p += 8
    if flg & 0x01:                      # dictionary id
        p += 4
    p += 1                              # header checksum
    block_csum = bool(flg & 0x10)
    out = bytearray()
    blocks = 0
    while p + 4 <= len(src):
        bsize = struct.unpack_from('<I', src, p)[0]
        p += 4
        if bsize == 0:
            break
        blocks += 1
        n = bsize & 0x7FFFFFFF
        if p + n > len(src):
            break                       # truncated read (head=True); keep what decoded
        if bsize & 0x80000000:
            out += src[p:p + n]
        else:
            # Blocks may be linked, so matches can reach back into earlier
            # blocks. Decoding into one shared buffer handles both modes.
            lz4_block(src[p:p + n], out)
        p += n
        if block_csum:
            p += 4
        if max_blocks and blocks >= max_blocks:
            break
    return bytes(out)


def lz4_block(src, out=None):
    """Decode one raw LZ4 block, appending into `out` so linked blocks resolve."""
    if out is None:
        out = bytearray()
    s, n = 0, len(src)
    d = len(out)
    while s < n:
        tok = src[s]; s += 1
        ln = tok >> 4
        if ln == 15:
            while True:
                b = src[s]; s += 1
                ln += b
                if b != 255:
                    break
        out += src[s:s + ln]
        s += ln; d += ln
        if s >= n:
            break
        off = src[s] | (src[s + 1] << 8); s += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[s]; s += 1
                ml += b
                if b != 255:
                    break
        ml += 4
        p = d - off
        if off >= ml:                           # non-overlapping: bulk copy
            out += out[p:p + ml]
        else:                                   # overlapping match, byte by byte
            for i in range(ml):
                out.append(out[p + i])
        d += ml
    return bytes(out)


# ---------------------------------------------------------------- BSA reader
class BSA:
    """Bethesda archive v103/104/105. Reads the index eagerly, file bytes lazily."""

    COMPRESSED = 0x004          # archive flag: entries compressed by default
    EMBEDNAME = 0x100           # entry names embedded before data

    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as fh:
            magic, self.ver, off, self.flags, nfold, nfile, foldnl, filenl, self.fileflags = \
                struct.unpack('<4sIIIIIIII', fh.read(36))
            if magic != b'BSA\x00':
                raise ValueError('not a BSA')
            rec = 24 if self.ver >= 105 else 16
            fh.seek(off)
            fdata = fh.read(rec * nfold)
            folders = []
            for i in range(nfold):
                if self.ver >= 105:
                    _h, cnt, _pad, o = struct.unpack_from('<QIIQ', fdata, i * rec)
                else:
                    _h, cnt, o = struct.unpack_from('<QII', fdata, i * rec)
                folders.append((cnt, o))
            # Folder-record offsets are biased by totalFileNameLength (not the
            # folder-name length - getting these two backwards silently lands
            # you in the file-name block and yields plausible-looking garbage).
            start = min(o for _c, o in folders) - filenl
            block_len = foldnl + nfold + 16 * nfile      # names (+1 length byte each) + records
            fh.seek(start)
            buf = fh.read(block_len)
            q = 0
            dirs = []
            for cnt, _o in folders:
                ln = buf[q]
                dname = buf[q + 1:q + ln].decode('cp1252', 'replace')
                q += 1 + ln
                for _ in range(cnt):
                    sz, fo = struct.unpack_from('<QII', buf, q)[1:]
                    dirs.append((dname, sz, fo))
                    q += 16
            names = fh.read(filenl).split(b'\x00')
            self.entries = [(f"{d}\\{fn.decode('cp1252', 'replace')}", fo, sz)
                            for (d, sz, fo), fn in zip(dirs, names)]

    def names(self):
        return [e[0] for e in self.entries]

    def read(self, index, limit=None, head=False):
        """Bytes of entry `index`. head=True stops after the first LZ4 block,
        which is all a DDS/NIF header needs and avoids decompressing whole
        4K textures in pure python."""
        _name, off, szf = self.entries[index]
        size = szf & 0x3FFFFFFF
        inverted = bool(szf & 0x40000000)
        compressed = bool(self.flags & self.COMPRESSED) ^ inverted
        with open(self.path, 'rb') as fh:
            fh.seek(off)
            raw = fh.read(min(size, 1 << 17) if head else size)
        p = 0
        if self.flags & self.EMBEDNAME:
            ln = raw[0]
            p = 1 + ln
        if not compressed:
            return raw[p:p + limit] if limit else raw[p:]
        want = struct.unpack_from('<I', raw, p)[0]
        payload = raw[p + 4:]
        if self.ver >= 105:
            out = lz4_frame(payload, max_blocks=1 if head else 0)
        else:
            import zlib
            out = zlib.decompressobj().decompress(payload, limit or 0) if head else zlib.decompress(payload)
        if head:
            return out
        if want and len(out) != want:
            raise ValueError(f'size mismatch: got {len(out)}, header says {want}')
        return out


# ---------------------------------------------------------------- DDS
FOURCC = {b'DXT1': 'BC1', b'DXT3': 'BC2', b'DXT5': 'BC3', b'ATI2': 'BC5', b'BC4U': 'BC4',
          b'ATI1': 'BC4', b'DX10': 'DX10', b'\x00\x00\x00\x00': 'uncompressed'}
DXGI = {71: 'BC1', 72: 'BC1', 74: 'BC2', 77: 'BC3', 80: 'BC4', 83: 'BC5', 95: 'BC6H',
        98: 'BC7', 99: 'BC7'}


def dds_info(head):
    if len(head) < 148 or head[:4] != b'DDS ':
        return None
    h, w = struct.unpack('<II', head[12:20])
    mips = struct.unpack('<I', head[28:32])[0]
    fourcc = head[84:88]
    fmt = FOURCC.get(fourcc)
    if fmt is None:
        fmt = fourcc.decode('latin1', 'replace').strip('\x00') or 'raw'
    if fmt == 'DX10':
        fmt = DXGI.get(struct.unpack('<I', head[128:132])[0], 'DX10?')
    return {'w': w, 'h': h, 'mips': mips, 'fmt': fmt}


# ---------------------------------------------------------------- NIF
def _sized_str(b, p):
    n = struct.unpack_from('<I', b, p)[0]
    return b[p + 4:p + 4 + n].decode('cp1252', 'replace'), p + 4 + n


def nif_info(data):
    """Header-level facts plus triangle counts for BSTriShape variants.

    The NiAVObject flags field is 16- or 32-bit depending on stream version, so
    the shape parse validates itself against dataSize and retries the other
    width rather than guessing."""
    if not data.startswith(b'Gamebryo File Format'):
        return None
    nl = data.index(b'\n')
    p = nl + 1
    ver, endian, uver, nblocks, uver2 = struct.unpack_from('<IBIII', data, p)
    p += 17
    for _ in range(2):                                   # export info strings
        ln = data[p]; p += 1 + ln
    ln = data[p]; p += 1 + ln
    if uver2 >= 130:                                     # FO4+, not expected here
        ln = struct.unpack_from('<I', data, p)[0]; p += 4 + ln
    ntypes = struct.unpack_from('<H', data, p)[0]; p += 2
    types = []
    for _ in range(ntypes):
        s, p = _sized_str(data, p)
        types.append(s)
    idx = struct.unpack_from('<%dH' % nblocks, data, p); p += 2 * nblocks
    sizes = struct.unpack_from('<%dI' % nblocks, data, p); p += 4 * nblocks
    nstr, _maxlen = struct.unpack_from('<II', data, p); p += 8
    strings = []
    for _ in range(nstr):
        s, p = _sized_str(data, p)
        strings.append(s)
    ngroups = struct.unpack_from('<I', data, p)[0]; p += 4 + 4 * ngroups

    counts = {}
    for t in types:
        counts[t] = 0
    for i in idx:
        counts[types[i]] = counts.get(types[i], 0) + 1

    tris = verts = 0
    shapes = 0
    pos = p
    for i, bi in enumerate(idx):
        bt = types[bi]
        blk = data[pos:pos + sizes[i]]
        pos += sizes[i]
        if bt not in ('BSTriShape', 'BSSubIndexTriShape', 'BSDynamicTriShape', 'BSMeshLODTriShape'):
            continue
        shapes += 1
        for flagwidth in (4, 2):
            try:
                q = 4                                    # name ref
                n_extra = struct.unpack_from('<I', blk, q)[0]; q += 4 + 4 * n_extra
                q += 4                                   # controller
                q += flagwidth                           # flags
                q += 12 + 36 + 4                         # translation, rotation, scale
                q += 4                                   # collision object
                q += 16                                  # bounding sphere
                q += 4 + 4 + 4                           # skin, shader, alpha refs
                q += 8                                   # vertex desc
                nt, nv = struct.unpack_from('<HH', blk, q); q += 4
                dsize = struct.unpack_from('<I', blk, q)[0]; q += 4
                vsize = (struct.unpack_from('<Q', blk, q - 16 - 4)[0] >> 32) & 0xF
                if nt > 65535 or nv > 65535:
                    continue
                if dsize and abs(dsize - (len(blk) - q)) > 64:
                    continue
                tris += nt; verts += nv
                break
            except Exception:
                continue
    parallax = b'_p.dds' in data or b'_P.DDS' in data
    pbr = b'_rmaos' in data.lower() if isinstance(data, bytes) else False
    skinned = any(t in counts and counts[t] for t in
                  ('BSSkin::Instance', 'NiSkinInstance', 'BSDismemberSkinInstance'))
    van = vanilla_bones()
    boneish = {s for s in strings if s in van or BONEISH.search(s)}
    return {'ver': f'{uver2}', 'blocks': nblocks, 'shapes': shapes, 'tris': tris,
            'verts': verts, 'types': counts, 'parallax': parallax, 'pbr': pbr,
            'skinned': skinned, 'strings': strings,
            'skirt_chain': sorted(b for b in boneish if b in van and 'Skirt' in b),
            'custom_bones': sorted(b for b in boneish if b not in van)}


# A string is treated as a bone if the vanilla skeleton names it, or if it looks
# like one. Node names like "Cape Outer" are not bones and must not count.
BONEISH = re.compile(r'^(NPC |CME |NINODE |HDT|SMP)|Bone\d*$|_skin$', re.I)
_VBONES = None


def vanilla_bones():
    """Bone names the stock character skeleton defines. Anything a mesh is
    weighted to beyond this set is a custom rig, which is what actually
    distinguishes a physics-ready mesh from one riding the canned animation."""
    global _VBONES
    if _VBONES is not None:
        return _VBONES
    _VBONES = set()
    data = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
    try:
        b = BSA(os.path.join(data, 'Skyrim - Meshes0.bsa'))
        for j, (k, _o, _s) in enumerate(b.entries):
            if k.lower().startswith('meshes\\actors\\character\\character assets\\skeleton'):
                info = nif_info(b.read(j))
                if info:
                    _VBONES |= set(info['strings'])
    except Exception:
        pass
    return _VBONES


# ---------------------------------------------------------------- indexing
ROOTS = ('textures', 'meshes', 'scripts', 'sound', 'music', 'interface', 'seq',
         'grass', 'lodsettings', 'shadersfx', 'strings', 'video', 'dialogueviews',
         'materials', 'skse', 'source', 'pandora', 'nemesis')


def data_rel(path):
    """Trim installer/FOMOD folders down to the Data-relative path."""
    parts = re.split(r'[\\/]+', path.replace('\\', '/'))
    low = [x.lower() for x in parts]
    for i, seg in enumerate(low):
        if seg in ROOTS:
            return '/'.join(low[i:])
    if low and low[-1].endswith(('.esp', '.esm', '.esl', '.bsa', '.ini', '.json', '.toml')):
        return low[-1]
    return '/'.join(low[-2:]) if len(low) > 1 else (low[0] if low else path)


def index_dir(root, deep=True):
    """Data-relative path -> facts. Descends into any BSA found."""
    out = {}
    for f in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if os.path.isdir(f):
            continue
        rel = os.path.relpath(f, root)
        low = rel.lower()
        if low.endswith('.bsa'):
            try:
                b = BSA(f)
            except Exception as e:
                out[data_rel(rel)] = {'size': os.path.getsize(f), 'err': str(e)[:60]}
                continue
            for i, (name, _o, _s) in enumerate(b.entries):
                key = data_rel(name)
                rec = {'size': b.entries[i][2] & 0x3FFFFFFF, 'bsa': os.path.basename(f)}
                if deep and (key.endswith('.dds') or key.endswith('.nif')):
                    try:
                        blob = b.read(i)
                        rec.update(_facts(key, blob))
                    except Exception as e:
                        rec['err'] = str(e)[:40]
                out[key] = rec
            continue
        key = data_rel(rel)
        rec = {'size': os.path.getsize(f)}
        if deep and (low.endswith('.dds') or low.endswith('.nif')):
            try:
                with open(f, 'rb') as fh:
                    blob = fh.read(148) if low.endswith('.dds') else fh.read()
                rec.update(_facts(key, blob))
            except Exception as e:
                rec['err'] = str(e)[:40]
        out[key] = rec
    return out


def _facts(key, blob):
    if key.endswith('.dds'):
        d = dds_info(blob[:148])
        return d or {}
    if key.endswith('.nif'):
        try:
            n = nif_info(blob)
        except Exception:
            n = None
        if n:
            return {k: n[k] for k in ('shapes', 'tris', 'verts', 'parallax', 'ver',
                                      'skinned', 'skirt_chain', 'custom_bones') if k in n}
    return {}


def index_mod(mid, prefer=None, label=None, deep=True, category='MAIN'):
    f = pick_file(mid, prefer, category)
    arc = download(mid, f)
    out = os.path.join(CACHE, f'x{mid}-{f["file_id"]}')
    extract(arc, out)
    idx = index_dir(out, deep=deep)
    return {'modId': mid, 'label': label, 'file': f['file_name'], 'version': f.get('version'),
            'size_mb': round(f['size_kb'] / 1024, 1), 'entries': idx}
