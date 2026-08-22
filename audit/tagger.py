"""Derive tags from what a mod ships, and keep them in an index that accumulates.

Nexus tags are author-declared and describe intent. These describe contents, so
they can answer questions the mod page cannot: which mods fight over the same
files, which need a Bashed or Synthesis patch, which edit cells, which will not
equip alongside each other.

Three kinds of tag:
  role:*    what the mod fundamentally is
  touches:* which asset domains it writes into, using the game's own folder names
  tech:*    how it delivers changes, which predicts what it conflicts with
  flag:*    warning signs the inspector found

Alongside the tags the index stores the mod's full Data-relative path set, which
is what actually decides overwrites. Tags group; paths adjudicate.
"""
import json, os, re
from collections import Counter

SP = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(SP, 'mod_tags.json')

# Asset domains, taken from the game's own folder layout rather than invented.
DOMAINS = {'terrain', 'actors', 'clutter', 'architecture', 'water', 'armor',
           'effects', 'clothes', 'weapons', 'dungeons', 'landscape', 'interface',
           'lod', 'plants', 'sky', 'cubemaps', 'furniture', 'magic', 'traps',
           'creationclub', 'dlc01', 'dlc02', 'auxbones', 'grass'}

# Record types worth tagging: each predicts a distinct class of conflict.
RECORD_TAGS = [
    (b'LVLI', 'tech:leveled-lists', 'edits leveled lists, so it needs a Bashed or '
                                    'Synthesis patch to coexist with others that do'),
    (b'LVLN', 'tech:leveled-npcs', 'edits NPC leveled lists'),
    (b'CELL', 'tech:cell-edits', 'edits cells, the most common source of silent conflicts'),
    (b'NAVM', 'tech:navmesh', 'ships navmesh, which does not merge cleanly'),
    (b'WRLD', 'tech:worldspace', 'touches or adds a worldspace'),
    (b'NPC_', 'tech:npc-records', 'edits NPC records'),
    (b'ARMO', 'tech:equipment', 'adds or edits equipment'),
    (b'SPEL', 'tech:spells', 'adds or edits spells'),
    (b'QUST', 'tech:quests', 'adds or edits quests'),
    (b'PERK', 'tech:perks', 'edits perks'),
    (b'GMST', 'tech:game-settings', 'changes game settings, which are global and last-wins'),
    (b'RACE', 'tech:race-records', 'edits race records, a frequent compatibility pinch point'),
    (b'WEAP', 'tech:weapons', 'adds or edits weapons'),
]


def derive(res, ents, plugins, items):
    """res: inspector result. ents: path -> facts. plugins: list of esp.Plugin."""
    tags = set()
    dds = [k for k in ents if k.endswith('.dds')]
    nifs = [k for k in ents if k.endswith('.nif')]
    pex = [k for k in ents if k.endswith('.pex')]
    dll = [k for k in ents if k.endswith('.dll')]
    hkx = [k for k in ents if k.endswith('.hkx')]

    # ---- role
    if dll:
        tags.add('role:skse-plugin')
    if hkx:
        tags.add('role:animation')
    if pex and not dll:
        tags.add('role:script-mod')
    replaced = res.get('_replaced', 0)
    if dds and not nifs and replaced > len(dds) * 0.5:
        tags.add('role:texture-replacer')
    elif dds and replaced > len(dds) * 0.5:
        tags.add('role:asset-replacer')
    elif nifs and replaced > len(nifs) * 0.3:
        tags.add('role:mesh-replacer')
    if items:
        tags.add('role:new-equipment' if replaced == 0 else 'role:equipment-replacer')
    if any('facegendata' in k for k in ents):
        tags.add('role:npc-visuals')
    if plugins and not dds and not nifs and not pex:
        tags.add('role:patch-only')
    if not tags and dds:
        tags.add('role:new-assets')

    # ---- touches
    dom = Counter()
    for k in ents:
        p = k.split('/')
        if len(p) < 2 or p[0] not in ('textures', 'meshes'):
            continue
        d = p[1]
        # DLC and CC folders mirror the whole tree inside themselves, so the
        # domain that matters is one level further down
        if d in ('dlc01', 'dlc02', 'creationclub', '_byoh', '_resourcepack') and len(p) >= 3:
            d = p[2]
        if d in DOMAINS:
            dom[d] += 1
    for d, n in dom.items():
        if n >= 3 or n >= len(ents) * 0.1:
            tags.add(f'touches:{d}')

    # ---- delivery mechanism
    if any(k.endswith('_distr.ini') for k in ents):
        tags.add('tech:spid')
    if any(k.endswith('_kid.ini') for k in ents):
        tags.add('tech:kid')
    if any('skypatcher' in k for k in ents):
        tags.add('tech:skypatcher')
    if any('openanimationreplacer' in k for k in ents):
        tags.add('tech:oar')
    elif any('dynamicanimationreplacer' in k for k in ents):
        tags.add('tech:dar-only')
    if any(k.endswith('.bsa') for k in ents):
        tags.add('tech:bsa-packed')
    elif dds or nifs:
        tags.add('tech:loose-files')
    if any(k.endswith('_p.dds') for k in ents):
        tags.add('tech:parallax')
    if any(re.search(r'^textures/pbr/|^materials/.*\.json$', k) for k in ents):
        tags.add('tech:pbr')
    if any('hdtskinnedmeshconfigs' in k or 'hdtsmp' in k for k in ents):
        tags.add('tech:hdt-smp')
    if any('cbpconfig' in k for k in ents):
        tags.add('tech:cbpc')

    # ---- plugin shape
    for pl in plugins:
        tags.add('tech:esl' if pl.esl else 'tech:esp')
        for rec, tag, _why in RECORD_TAGS:
            if pl.records.get(rec):
                tags.add(tag)
    if plugins:
        masters = {m for pl in plugins for m in pl.masters}
        if masters - {'Skyrim.esm', 'Update.esm', 'Dawnguard.esm',
                      'HearthFires.esm', 'Dragonborn.esm'}:
            tags.add('tech:needs-other-mods')

    # ---- equip slots, so wearables that cannot coexist are visible
    for r in items:
        for s in r.get('slots') or []:
            if 30 <= s <= 61:
                tags.add(f'slot:{s}')

    # ---- warning signs. The inspector sets the nuanced ones explicitly; the
    # rest are mirrored from finding text, which is why findings use stable
    # wording.
    tags |= set(res.get('_flags') or [])
    FLAGMAP = [('no matching normal map', 'flag:missing-normals'),
               ('uncompressed rather than', 'flag:uncompressed-textures'),
               ('without mipmaps', 'flag:no-mipmaps'),
               ('unconverted Oldrim', 'flag:oldrim-meshes'),
               ('junk files', 'flag:archive-junk'),
               ('stored as BC1', 'flag:bc1-normals'),
               ('LOWER resolution than the vanilla', 'flag:below-vanilla-res'),
               ('JPEG blocking', 'flag:jpeg-source'),
               ('rigid geometry', 'flag:no-cloth-physics'),
               ('canned skirt animation', 'flag:no-cloth-physics'),
               ('inert without a separate physics patch', 'flag:rig-needs-smp'),
               ('flat placeholders', 'flag:flat-normals'),
               ('embossed from the diffuse', 'flag:embossed-normals')]
    blob = ' '.join(res.get('findings', []))
    for needle, tag in FLAGMAP:
        if needle in blob:
            tags.add(tag)
    return sorted(tags)


def load():
    if os.path.exists(INDEX):
        return json.load(open(INDEX, encoding='utf-8'))
    return {}


def save(mid, label, tags, paths, findings, size_mb):
    idx = load()
    idx[str(mid)] = {'label': label, 'tags': tags, 'size_mb': size_mb,
                     'findings': findings,
                     'paths': sorted(p for p in paths
                                     if p.endswith(('.dds', '.nif', '.pex', '.hkx',
                                                    '.esp', '.esl', '.esm')))}
    tmp = INDEX + '.tmp'
    json.dump(idx, open(tmp, 'w', encoding='utf-8'), indent=0)
    os.replace(tmp, INDEX)
    return len(idx)


def collisions(mid=None):
    """Which indexed mods write the same Data paths."""
    idx = load()
    owner = {}
    for m, rec in idx.items():
        for p in rec['paths']:
            owner.setdefault(p, []).append(m)
    shared = {p: ms for p, ms in owner.items() if len(ms) > 1}
    pairs = Counter()
    for p, ms in shared.items():
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                pairs[tuple(sorted((ms[i], ms[j])))] += 1
    if mid:
        pairs = Counter({k: v for k, v in pairs.items() if str(mid) in k})
    return pairs, shared, idx
