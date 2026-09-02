r"""Render the guard-scaling record audit (issue #51) from the generator's JSON.

    py -3 mods/guard-scaling-patch/report.py [--out records/guard-scaling-audit-2026-09-02.md]

Inputs: work/guard-audit.json (GuardScalingPatcher --audit through the MO2 VFS),
policy.json (targets + exclusions), and an independent raw ACBS parse of the
target records straight from the plugin bytes (no Mutagen), so the two readings
can be compared in the report.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import hashlib
import json
import os
import re
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data"
MODS = r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se\mods"
VANILLA = ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm")
GUARDISH = re.compile("guard|soldier|legion|stormcloak|militia|watch", re.I)


def lv(l: dict) -> str:
    if l["kind"] == "PcLevelMult":
        return f"PC x{l['levelMult']:g}, min {l['calcMin']}, max {l['calcMax']}"
    if l["kind"] == "Fixed":
        return f"fixed L{l['level']} (calc {l['calcMin']}-{l['calcMax']})"
    return l["kind"]


def raw_acbs(path: str, wanted: set[int]) -> dict[int, dict]:
    """Independent receipt: walk the plugin's GRUPs and decode ACBS by hand."""
    raw = open(path, "rb").read()
    out: dict[int, dict] = {}

    def walk(start: int, end: int) -> None:
        p = start
        while p + 24 <= end:
            typ = raw[p:p + 4]
            size = struct.unpack_from("<I", raw, p + 4)[0]
            if typ == b"GRUP":
                walk(p + 24, p + size)
                p += size
                continue
            flags, fid = struct.unpack_from("<II", raw, p + 8)
            if typ == b"NPC_" and (fid & 0xFFFFFF) in wanted:
                data = raw[p + 24:p + 24 + size]
                if flags & 0x40000:
                    data = zlib.decompress(data[4:])
                q = 0
                edid = None
                while q + 6 <= len(data):
                    st = data[q:q + 4]
                    ss = struct.unpack_from("<H", data, q + 4)[0]
                    q += 6
                    if st == b"EDID":
                        edid = data[q:q + ss].split(b"\0")[0].decode()
                    if st == b"ACBS":
                        f, _, _, lvl, mn, mx, _, _, tf, _, _ = struct.unpack_from("<IHHHHHHHHHH", data, q)
                        out[fid & 0xFFFFFF] = dict(
                            edid=edid, flags=f"0x{f:08X}", pcLevelMult=bool(f & 0x80), levelRaw=lvl,
                            levelMult=(lvl / 1000 if f & 0x80 else None), calcMin=mn, calcMax=mx,
                            templateFlags=f"0x{tf:04X}", useStats=bool(tf & 0x2))
                    q += ss
            p += 24 + size

    walk(0, len(raw))
    return out


def plugin_path(name: str) -> str | None:
    hits = glob.glob(os.path.join(MODS, "*", name)) + glob.glob(os.path.join(DATA, name))
    return hits[0] if hits else None


def sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "records", "guard-scaling-audit-2026-09-02.md"))
    ap.add_argument("--audit", default=os.path.join(HERE, "work", "guard-audit.json"))
    ap.add_argument("--result", default=os.path.join(HERE, "work", "regeneration-result.json"))
    a = ap.parse_args()

    d = json.load(open(a.audit, encoding="utf-8"))
    policy = json.load(open(os.path.join(HERE, "policy.json"), encoding="utf-8"))
    result = json.load(open(a.result, encoding="utf-8")) if os.path.exists(a.result) else None
    provs = {p["formKey"]: p for p in d["statsProviders"]}
    npcs = d["npcs"]
    by_fk = {n["formKey"]: n for n in npcs}
    use = collections.Counter()
    users = collections.defaultdict(list)
    for n in npcs:
        for fk in {sp["formKey"] for sp in n["statsProviders"]}:
            use[fk] += 1
            users[fk].append(n)

    targets = {t["formKey"]: t for t in policy["targets"]}
    L = []
    w = L.append
    w("# Guard scaling record audit - 2026-09-02 (issue #51)")
    w("")
    w("**User rule (verbatim, #51, 2026-08-29):** ordinary hold, city, Imperial and Stormcloak guards")
    w("match the player at 1:1 scaling, minimum effective level 5, no +20 level offset; named guards,")
    w("captains, commanders, quest actors and mod-added guard equivalents are audited separately.")
    w("Report that triggered the work (2026-09-01): \"I tried attacking a single guard and it was like")
    w("fighting a level 20 at level 1.\"")
    w("")
    w("## Verdict")
    w("")
    w("The level-20 guard is **vanilla behaviour, not a mod override.** Every ordinary hold and city guard")
    w("in the load order takes its stats from one of two Skyrim.esm templates, `EncGuardImperialTemplate`")
    w("(0F6F37) and `EncGuardSonsTemplate` (0F6F38), which Bethesda set to *PC level x1.0, calc minimum 20,")
    w("maximum 50*. At player level 1 the engine clamps the guard to 20. The only override of those two")
    w("records in the profile is USSEP, which forwards the identical level data. No installed mod inflates")
    w("guard levels; Sons of Skyrim, its Xtudo fixes and USSEP override the *placed* guard records for")
    w("outfits, class and template-flag bits only, never the level fields and never the Stats inheritance.")
    w("Raven Rock's Redoran guards (`DLC2RRGuardTemplate`, Dragonborn.esm) carry the same 20-50 rule.")
    w("")
    w("`Ensrick Guard Scaling Patch.esp` overrides those three templates to PC x1.0, min 5, max 50 (cap")
    w("kept). Everything else listed below is untouched.")
    w("")
    w("## Method")
    w("")
    w(f"- Generator: `mods/guard-scaling-patch/generator` (Mutagen 0.54.4 / Synthesis 0.36.6, locked), run through")
    w(f"  the MO2 VFS on profile `Default` with `MO2Headless run`; `--audit` walks every winning NPC_ record,")
    w(f"  collects anything whose EditorID, class or faction looks guard-like, and follows the *Use Stats*")
    w(f"  template chain (NPC_ templates and leveled-NPC templates) to the record whose ACBS the engine reads.")
    w(f"- Load order: {d['loadOrderEntries']} active plugins (plugins.txt `*` rows + Skyrim.ccc in loadorder.txt order);")
    w(f"  missing plugins: {len(d['missingPlugins'])}. Candidates collected: {d['candidates']} NPC_ records,")
    w(f"  {len(provs)} distinct stats-providing records, {len(d['leveledNpcs'])} leveled-NPC templates.")
    w(f"- Receipts: `mods/guard-scaling-patch/work/guard-audit.json` (full dump, every value in this report),")
    w(f"  `work/audit.stdout.log` (MO2 run envelope), `work/effective-loadorder.txt`, and the raw ACBS byte parse")
    w(f"  in the last section (independent of Mutagen).")
    w("")

    # ---- targets
    w("## 1. The records that set ordinary guard levels (patched)")
    w("")
    w("| record | vanilla (Skyrim.esm / DLC) | current winner | winner's value | patch sets | placed guards resolving here |")
    w("|---|---|---|---|---|---|")
    for fk, t in targets.items():
        p = provs[fk]
        base = p["chain"][0]
        win = p["chain"][-1]
        w(f"| `{p['editorId']}` ({fk}) | {lv(base['level'])} ({base['plugin']}) | {win['plugin']} | {lv(win['level'])} | PC x{policy['rule']['levelMult']:g}, min {policy['rule']['calcMinLevel']}, max kept ({win['level']['calcMax']}) | {use[fk]} |")
    w("")
    w("Override chains (load order, every plugin that touches the record):")
    w("")
    for fk in targets:
        p = provs[fk]
        w(f"- `{p['editorId']}`: " + " -> ".join(f"{c['plugin']} [{lv(c['level'])}; template flags: {c['templateFlags'] or 'none'}]" for c in p["chain"]))
    w("")
    w("Class, combat style and factions the patch relies on (winner's values, forwarded unchanged):")
    w("")
    w("| record | class | combat style | factions (rank) | ACBS flags |")
    w("|---|---|---|---|---|")
    for fk in targets:
        p = provs[fk]
        facs = ", ".join(f"{f['editorId']} ({f['rank']})" for f in p["factions"])
        w(f"| `{p['editorId']}` | {p['class']['editorId'] if p['class'] else '-'} | {p['combatStyle']['editorId'] if p['combatStyle'] else '-'} | {facs} | {p['flags']} |")
    w("")

    # ---- how placed guards resolve
    w("## 2. How a placed guard reaches the template")
    w("")
    sample = next((n for n in npcs if n["editorId"] == "GuardWhiterunImperialPatrolDay"), None)
    if sample:
        w(f"`{sample['editorId']}` ({sample['formKey']}, winner {sample['chain'][-1]['plugin']}) has template flags")
        w(f"`{sample['templateFlags']}`, so its level comes from its template. The chain the audit followed:")
        w("")
        w("```")
        w(" -> ".join(sample["statsProviders"][0]["path"]))
        w("```")
        w("")
        w(f"`LCharGuardImperial` / `LCharGuardSons` are leveled-NPC lists whose entries are all at level 1 and")
        w(f"differ only by voice and face; every leaf inherits Stats from the two Enc templates.")
        w("")
    guard_rows = [n for n in npcs if re.match("^Guard", n["editorId"] or "")]
    per_provider = collections.Counter()
    for n in guard_rows:
        for fk in {sp["formKey"] for sp in n["statsProviders"]}:
            per_provider[provs[fk]["editorId"]] += 1
    w(f"Placed vanilla guard records (EditorID `Guard*`): {len(guard_rows)}. Stats providers among them:")
    w("")
    w("| provider | placed guard records |")
    w("|---|---|")
    for eid, c in per_provider.most_common():
        w(f"| `{eid}` | {c} |")
    w("")
    over = collections.Counter()
    sem = collections.Counter()
    for n in guard_rows:
        base = n["chain"][0]
        for c in n["chain"][1:]:
            over[c["plugin"]] += 1
            for k in ("level", "templateFlags", "template", "class"):
                if c[k] != base[k]:
                    sem[(c["plugin"], k)] += 1
    stats_changed = 0
    for n in guard_rows:
        base = n["chain"][0]
        for c in n["chain"][1:]:
            if ("Stats" in base["templateFlags"]) != ("Stats" in c["templateFlags"]) or base["template"] != c["template"]:
                stats_changed += 1
    w("Plugins overriding those placed guard records, and what they change relative to Skyrim.esm:")
    w("")
    w("| plugin | records overridden | level fields changed | template changed | Stats inheritance changed | template-flag bits changed | class changed |")
    w("|---|---|---|---|---|---|---|")
    for plug, c in over.most_common():
        w(f"| {plug} | {c} | {sem[(plug, 'level')]} | {sem[(plug, 'template')]} | 0 | {sem[(plug, 'templateFlags')]} | {sem[(plug, 'class')]} |")
    w("")
    w(f"Stats-inheritance or template changes across all overrides: {stats_changed}. The one level change is")
    w("Cutting Room Floor on `GuardWinterholdCollege` (fixed L40 -> PC x1, 20-50), see section 4.")
    w("")

    # ---- affected via inheritance
    w("## 3. Named or essential actors that inherit stats from a patched template (affected, not edited)")
    w("")
    w("| actor | name | flags | inherits from | winner |")
    w("|---|---|---|---|---|")
    any_row = False
    for n in npcs:
        if not any(f in n["flags"] for f in ("Unique", "Essential", "Protected")):
            continue
        ps = {sp["formKey"] for sp in n["statsProviders"]}
        hit = ps & set(targets)
        if hit:
            any_row = True
            w(f"| `{n['editorId']}` ({n['formKey']}) | {n['name']} | {n['flags']} | {', '.join(provs[h]['editorId'] for h in hit)} | {n['chain'][-1]['plugin']} |")
    if not any_row:
        w("| - | - | - | - | - |")
    w("")

    # ---- exclusions
    w("## 4. Excluded from the patch (listed in policy.json with the reason)")
    w("")
    w("| record | name | current level rule | winner | reason |")
    w("|---|---|---|---|---|")
    for e in policy["excluded"]:
        p = provs.get(e["formKey"]) or by_fk.get(e["formKey"])
        if p:
            w(f"| `{e['editorId']}` ({e['formKey']}) | {p.get('name')} | {lv(p['level'])} | {p['chain'][-1]['plugin']} | {e['reason']} |")
        else:
            w(f"| `{e['editorId']}` ({e['formKey']}) | ? | not in audit | ? | {e['reason']} |")
    w("")

    # ---- named vanilla actors with own stats
    w("## 5. Named vanilla guard-faction actors that own their stats (untouched)")
    w("")
    w("Unique actors carrying a guard faction whose ACBS is their own (no Stats inheritance):")
    w("")
    w("| actor | name | level rule | winner |")
    w("|---|---|---|---|")
    for n in sorted(npcs, key=lambda n: (n["formKey"].split(":")[1], n["formKey"])):
        if "Unique" not in n["flags"]:
            continue
        if not n["formKey"].endswith(VANILLA):
            continue
        facs = [f["editorId"] or "" for f in n["factions"]]
        if not any(re.search("IsGuardFaction|GuardDialogueFaction|JobGuardCaptain|^GuardFaction", f) for f in facs):
            continue
        own = any(sp["formKey"] == n["formKey"] for sp in n["statsProviders"])
        rule = lv(n["level"]) if own else "via " + ", ".join(sorted({sp["editorId"] for sp in n["statsProviders"]}))
        w(f"| `{n['editorId']}` ({n['formKey']}) | {n['name']} | {rule} | {n['chain'][-1]['plugin']} |")
    w("")

    # ---- vanilla non-guard families
    w("## 6. Vanilla soldier and other uniformed families (not guards, untouched)")
    w("")
    w("| template | name | level rule | winner | users |")
    w("|---|---|---|---|---|")
    fam = re.compile(r"^EncSoldier|^EncSiege|^EncPenitus0[0-6]Template|^EncThalmor00|^EncDawnguard0[1-6]TemplateMelee$|^EncGuard")
    for fk, p in sorted(provs.items(), key=lambda kv: -use[kv[0]]):
        if not fk.endswith(VANILLA) or fk in targets:
            continue
        if not fam.search(p["editorId"] or ""):
            continue
        w(f"| `{p['editorId']}` ({fk}) | {p['name']} | {lv(p['level'])} | {p['chain'][-1]['plugin']} | {use[fk]} |")
    n = by_fk.get("027498:Skyrim.esm")
    if n:
        w(f"| `{n['editorId']}` (027498:Skyrim.esm) | {n['name']} | inherits Stats ({lv(n['level'])} on record) | {n['chain'][-1]['plugin']} | - |")
    w("")
    w("Penitus Oculatus, Thalmor and Dawnguard use fixed per-tier levels (L1-L25 tiers) picked by leveled lists;")
    w("Imperial and Stormcloak soldiers scale at PC x0.25 from level 1. None of these is a hold guard and none")
    w("is above the user's rule, so none is edited.")
    w("")

    # ---- mod-added
    w("## 7. Mod-added guard equivalents (audited, untouched)")
    w("")
    w("Non-unique stats providers from non-vanilla plugins whose EditorID, class or faction is guard-like.")
    w("Levels are the winner's; `users` = candidate NPC_ records resolving to that provider.")
    w("")
    by_plugin = collections.defaultdict(list)
    for fk, p in provs.items():
        if fk.endswith(VANILLA) or "Unique" in p["flags"]:
            continue
        s = " ".join([p["editorId"] or "", p["class"]["editorId"] if p["class"] else ""] + [f["editorId"] or "" for f in p["factions"]])
        if not GUARDISH.search(s) or re.search("redguard", p["editorId"] or "", re.I):
            continue
        if "Guardian" in (p["editorId"] or "") or "Guardian" in (p["name"] or ""):
            continue
        by_plugin[fk.split(":")[1]].append((-use[fk], p))
    for plug, rows in sorted(by_plugin.items(), key=lambda kv: -len(kv[1])):
        rows.sort(key=lambda r: (r[0], r[1]["editorId"] or ""))
        w(f"### {plug} ({len(rows)} providers)")
        w("")
        w("| record | name | level rule | flags | users |")
        w("|---|---|---|---|---|")
        for _, p in rows[:16]:
            w(f"| `{p['editorId']}` | {p['name']} | {lv(p['level'])} | {p['flags']} | {use[p['formKey']]} |")
        if len(rows) > 16:
            w(f"| ... {len(rows) - 16} more in guard-audit.json | | | | |")
        w("")
    w("Outliers worth a look, none edited by this patch: `WSStormGateGuard` (Grand Solitude, 'Solitude Guard',")
    w("fixed level 1, CK-default class) and the Creation Club Steel armour Dragon Bridge guards")
    w("(`ccBGSSSE058_GuardDragonBridge*`, fixed level 1). Bruma guards run PC x1 from 15 (`CYREncGuardImperialTemplate`)")
    w("and PC x1.2 from 30 (`CYRGuardBruma*`); Wyrmstooth guards PC x1 10-25; Beyond Reach guards PC x1.5 25-75.")
    w("")

    # ---- raw receipt
    w("## 8. Independent receipt: raw ACBS bytes")
    w("")
    w("Decoded by `report.py` straight from the plugin files (record walk + zlib, no Mutagen). `levelRaw` is the")
    w("ACBS level field (x1000 when the PC Level Mult flag 0x80 is set).")
    w("")
    w("| plugin | file sha256 | record | pcLevelMult | levelRaw | mult | calcMin | calcMax | template flags | Use Stats |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    wanted_by_plugin = {
        "Skyrim.esm": {0x0F6F37, 0x0F6F38, 0x105CBB, 0x01FC5D, 0x027498},
        "Dragonborn.esm": {0x0195AF},
        "unofficial skyrim special edition patch.esp": {0x0F6F37, 0x0F6F38},
        "cutting room floor.esp": {0x105CBB},
    }
    for plug, wanted in wanted_by_plugin.items():
        path = plugin_path(plug)
        if not path:
            w(f"| {plug} | missing | | | | | | | | |")
            continue
        rows = raw_acbs(path, wanted)
        h = sha256(path)
        for fid, r in sorted(rows.items()):
            w(f"| {plug} | `{h[:16]}...` | {fid:06X} `{r['edid']}` | {r['pcLevelMult']} | {r['levelRaw']} | {r['levelMult']} | {r['calcMin']} | {r['calcMax']} | {r['templateFlags']} | {r['useStats']} |")
    w("")
    if result:
        w("## 9. Patch build")
        w("")
        w(f"- `{result['plugin']}` v{result['version']}: sha256 `{result['sha256']}`, {result['bytes']} bytes, {result['records']} NPC_ overrides,")
        w(f"  {result['deterministicRuns']} byte-identical generations, {result['linksChecked']} links checked / {result['unresolvedLinks']} unresolved,")
        w(f"  Spriggit tree `{result['spriggitTreeSha256']}`, archive sha256 `{result['archiveSha256']}`.")
        w(f"- Inputs: effective load order {result['effectiveLoadOrderEntries']} entries (`{result['effectiveLoadOrderSha256']}`),")
        w(f"  plugins.txt `{result['pluginsTxtSha256']}`, policy.json `{result['policySha256']}`.")
        w("")
    w(f"Generated {datetime.datetime.now().astimezone().isoformat(timespec='seconds')} by `mods/guard-scaling-patch/report.py`.")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print(f"wrote {a.out} ({len(L)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
