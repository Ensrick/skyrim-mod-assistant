"""How much ecosystem support does a new-lands mod actually attract?

A worldspace mod only stays current if other authors keep patching it: grass and
tree overhauls need per-worldspace patches, NPC and outfit overhauls need
distribution rules extended to its actors, and LOD needs regenerating. Counting
those patches, and how recently they were made, measures whether a mod is still
part of the modding ecosystem or has been left behind by it.
"""
import json, sys, io, urllib.request
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGETS = [('Falskaar', 2057), ('Wyrmstooth', 45565), ('Beyond Skyrim Bruma', 10917),
           ('Beyond Reach', 3008)]
# the classes of support that decide whether a worldspace looks current
KINDS = [('landscape/grass/trees', r'grass|tree|flora|landscape|terrain|lod|dyndolod'),
         ('NPC / outfit / body',   r'npc|outfit|armou?r|cloth|face|appearance|hair|body'),
         ('lighting / weather',    r'light|weather|enb|climate'),
         ('bugfix / patch',        r'fix|patch|cleaned|unofficial'),
         ('audio / music',         r'sound|music|audio|voice'),
         ('gameplay integration',  r'spid|distribut|leveled|skypatcher|keyword|survival|needs')]


def gql(q):
    r = urllib.request.Request('https://api.nexusmods.com/v2/graphql',
                               data=json.dumps({'query': q}).encode(),
                               headers={'Content-Type': 'application/json',
                                        'User-Agent': 'SkyrimModAssistant/0.1'})
    return json.load(urllib.request.urlopen(r, timeout=60))


def search(term, count=50):
    q = ('{ mods(filter:{ gameDomainName:[{value:"skyrimspecialedition",op:EQUALS}], '
         'name:[{value:"%s", op:WILDCARD}] }, sort:{ endorsements:{direction:DESC} }, '
         'count:%d){ nodes { modId name endorsements updatedAt createdAt uploader{name} } } }'
         % (term, count))
    return ((gql(q).get('data') or {}).get('mods') or {}).get('nodes') or []


import re
LANG = re.compile(r'translat|russian|deutsch|german|spanish|polish|italian|chinese|'
                  r'portugu|turkish|korean|japanese|fran|\bchs\b|\bcht\b|\bpl\b', re.I)

def report(label, mid):
    hits = [h for h in search(label) if h['modId'] != mid and not LANG.search(h['name'])]
    print(f'\n{"="*70}\n{label} (mod {mid}): {len(hits)} companion mods on Nexus')
    years = Counter((h.get('updatedAt') or '')[:4] for h in hits)
    print('   last updated by year: ' + ', '.join(
        f'{y}({n})' for y, n in sorted(years.items(), reverse=True) if y))
    recent = [h for h in hits if (h.get('updatedAt') or '') >= '2024']
    print(f'   touched in 2024 or later: {len(recent)} of {len(hits)}')
    for kind, pat in KINDS:
        rx = re.compile(pat, re.I)
        k = [h for h in hits if rx.search(h['name'])]
        if k:
            newest = max((h.get('updatedAt') or '')[:7] for h in k)
            print(f'      {kind:<24}{len(k):>3}   newest {newest}')
    for h in sorted(hits, key=lambda x: -(x.get('endorsements') or 0))[:6]:
        print(f"      {h['modId']:<8}{(h.get('updatedAt') or '')[:7]}  "
              f"{h['name'][:52]:<54}{h.get('endorsements')}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for a in sys.argv[1:]:
            label, mid = a.rsplit(':', 1)
            report(label, int(mid))
    else:
        for label, mid in TARGETS:
            report(label, mid)
