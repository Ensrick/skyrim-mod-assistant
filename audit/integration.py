"""Split a mod's companions into repair and integration.

Repair keeps a mod working. Integration makes it belong in a modern load order:
retextures, NPC-overhaul patches, creature replacers, framework distribution.
The ratio, and the date of the newest integration, says whether the community
is maintaining a mod or actually still investing in it.
"""
import sys, io, re
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from ecosystem import search, LANG

REPAIR = re.compile(r'\bfix|\bpatch|unofficial|cleaned|bug|stuck|crash|synergy|compatib', re.I)
INTEGRATE = re.compile(r'retextur|replacer|overhaul|\bhd\b|4k|2k|addon|npc|khajiit|'
                       r'armou?r|outfit|spid|distribut|animation|physics|parallax|pbr|'
                       r'grass|tree|lod|dyndolod|music|voice|expansion|extended', re.I)


def split(term, mid, label=None):
    hits = [h for h in search(term, 50)
            if h['modId'] != mid and not LANG.search(h['name'])]
    repair, integrate, other = [], [], []
    for h in hits:
        n = h['name']
        if INTEGRATE.search(n) and not REPAIR.search(n):
            integrate.append(h)
        elif REPAIR.search(n):
            repair.append(h)
        else:
            other.append(h)
    print(f'\n{label or term}: {len(hits)} companions')
    print(f'   repair      {len(repair):>3}   newest '
          f'{max([(h.get("updatedAt") or "")[:7] for h in repair] or ["-"])}')
    print(f'   integration {len(integrate):>3}   newest '
          f'{max([(h.get("updatedAt") or "")[:7] for h in integrate] or ["-"])}')
    print(f'   other       {len(other):>3}')
    for h in sorted(integrate, key=lambda x: -(x.get('endorsements') or 0))[:7]:
        print(f"      {h['modId']:<8}{(h.get('updatedAt') or '')[:7]}  "
              f"{h['name'][:52]:<54}{h.get('endorsements')}")


for term, mid, label in (('Moonpath', 4341, 'Moonpath to Elsweyr'),
                         ('Falskaar', 2057, 'Falskaar'),
                         ('Wyrmstooth', 45565, 'Wyrmstooth')):
    try:
        split(term, mid, label)
    except Exception as e:
        print(f'{label}: failed {str(e)[:80]}')
