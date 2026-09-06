# Playtest repairs and evidence — 2026-09-06

Repairs installed and statically checked; currency-script candidate held for further
bytecode-preservation proof. No assistant game launch; gameplay acceptance remains open.

## Approved Sons of Skyrim physics adoption

The user explicitly requested an existing physics mod, not a new cloth simulation.
[Sons of Skyrim - HDT Physics for Cloaks Patch](https://www.nexusmods.com/skyrimspecialedition/mods/114690)
v1.1 remains the current main release, confirmed by the official API on September 6.
Main file483316 is the right input; Sentinel optional484635 is not applicable.
SoS2.0.2 and the installed FSMP satisfy its declared dependencies. The ESP is
already ESL-flagged and contains only12 ARMO overrides; no new equipment or
distribution choices are introduced.

Archive SHA256: C2037FE08D4CF4EA6B3B8BB24E1C7C3B64F608F72D491C59C8E5D3C32DC97FB0.
The deterministic plan installs48 NIFs, two XMLs and the unchanged ESP, omitting
only the promotional PNG. All51 payload files matched archive bytes on both
passes. Disabled inspection transaction20260906T021231736Z-b62e0a3b6e19 was rolled
back before enabled transaction20260906T021323812Z-97fa561473b9. Vendor priority287;
ESP271, after SoS/Xtudo and before WeaponBalancePatch272. Existing unrelated order
was not sorted or rewritten. Keep114690 was queued with naru1305/user5045881 author
metadata; queued is not the same as applied in Firefox.

Activation audit: the game-side Plugins.txt had preexisting ordering differences
from the MO2 list. An orchestration error initially allowed the single SoS line
insertion after the broader exact-order guard failed. That owned insertion was
immediately reverted and the original full hash89D12457…3F27B verified restored;
no game/MO2 process was running. The subsequent approved operation pinned that
original file, backed it up, and added only SoS before WeaponBalance while
preserving every other row's exact order. Final hashD847F830…B5A35D. Future
orchestration must inspect the guard command's exit status before applying writes.

The author's plugin changes the12 cloak masks40+46 to46 and reorders otherwise
identical keywords. It does not replace our cross-mod slot58 exclusion overlay.
Dependent full-cloak reservation and weapon-source manifests were regenerated.
The weapon ESP and all27 translations remained byte-identical: only receipts changed.
The refreshed cloak overlay still has the same240 directives; all48 SoS worn meshes
now resolve to the approved SMP replacement. Installed freshness gates pass.
All48 installed meshes contain references to installed, well-formed SMP XMLs.
An initial raw-string suspicion about four female officer/pauldron variants was
DISPROVEN in #244: their root-linked NiStringExtraData correctly selects capeF_SoS.xml;
the male path is an unused header string. No mesh edit is appropriate. Audit the
actual string reference, not merely the presence of text in a binary string table.

Existing author reports include double-cape and no-physics complaints. The optional
Sentinel file also has reports of incompatible form mappings; it is not installed.
We verify actual winning meshes rather than assume a successful download proves
physics. Source: [author's posts](https://www.nexusmods.com/skyrimspecialedition/mods/114690?tab=posts),
[bug list](https://www.nexusmods.com/skyrimspecialedition/mods/114690?tab=bugs).
In-engine male/female animation, re-equip and NPC checks remain required.

Vendor permission forbids reupload and identifies other authors' assets. Public
deliverables are original recipes/records; vendor payloads remain external downloads.

## Bruma helmet — #242

Human/elf Cyrodiil iron helmet mesh uses BSDismember partition31 instead of131;
Bruma's beast-race siblings and six vanilla iron helmet meshes use131. The winning
ARMO/ARMA equipment masks are already correct. The isolated user-local repair changes
only byte586 from31 to131, with99,650 remaining bytes and all geometry unchanged.
Independent parser read-back and root/agent repeat builds agree. No vendor BSA or
ESP is edited. See `audit/bruma-iron-helmet-decapitation.md` and the original recipe.
The generated mesh is not approved for redistribution; users generate it locally.
Installed at priority288 in transaction20260906T022223092Z-a95265063f98; source-build
receipt `records/source-builds/bruma-iron-helmet-decapitation-0.1.0.json`. No claim of
in-game acceptance is made before fresh decapitation/equip tests.

## Arrow lethal timing

Version0.3.2's player eligibility repair is visible in the latest log. Its supposedly
post-damage callback is not reliably post-damage: this runtime can queue ProcessHit
and return before applying damage. A killing shot can therefore be evaluated using
the old health state. Source-built0.3.3 now observes actual queue submission and
completion, and gates visual processing until damage completion plus Skyrim's
handled marker. Exact executable audit proves the reviewed false-return path does
not clean up the arrow, and preserving the marker bypasses both damage replay
branches. No queue scheduling order is assumed. Killing blows use committed death
state before health/region rules; no predictive fatal flag or damage estimate.

Author, independent reviewer and root checks passed; four final CTest groups,
three negative source controls, binary audit,19 package manifest entries and
deterministic repackaging pass. Installed transaction20260906T024735778Z-7d0cdb78853b
preserves config,priority249,all367 mod entries and plugin list bytes.
DLL SHA511F4CEF0D11B348EC8CE2D4FEAB704761CAB352D42B1A9005F41B2A171532EA.
Receipt `records/source-builds/conditional-arrow-embedding-0.3.3.json`.
Stale/ambiguous/canceled/overloaded/expired hits retain vanilla; pending state is
limited to256 entries and2seconds. Destroy-after-hit paths are deliberately vanilla.
Cross-load and real combat acceptance remain open. Runtime issue
[ConditionalArrowEmbedding#1](https://github.com/Ensrick/ConditionalArrowEmbedding/issues/1)
stays open; no predictive damage estimate substitutes for committed damage.

## Currency menu-script errors — #209

Current logs contain44 null-error triplets in Papyrus.0 and11 in Papyrus.1 from
ECE's `checkMintExchanger`. An isolated source candidate resets the stale flag and
guards both the actor and its base form while preserving Eyrir/Galos recognition.
Independent review confirms that function's logic. It is **not installed**:
the vendor source was decompiled, so unchanged text in other functions is not
proof that recompiling the whole script preserves their original bytecode behavior.
The current0.2.6 package/oracle and installed vendor script remain unchanged.
Keep the original recipe public and generated vendor-derived PSC/PEX private if
this is completed later. See the log report for exact evidence and staged receipt.

## Logs and Solitude — #37 / #243

Independent triage covers available recent and retained logs. Earlier session logs
may have been overwritten; absence of a report is not proof of no rendering defect.
Bards College wall flicker is tracked in #243. Do not disable whole overhauls or
change Fable's shader/INI work without identifying the overlapping geometry or
other concrete cause. Findings are recorded in `records/log-triage-2026-09-06.md`.

## Confirmed container-count fault — #230

The retained CDF log shows a signed -12 item delta becoming4294967284, then clamped
to32767. Reused the independently reviewed, already source-built CDF PR2 candidate
(code78fdfd9, canonical CI artifact9955063110). Root rebuilt and executed its native
count tests and the onlyVendors regression. The five-file owned overlay replacement
preserves priority275 and every vendor distribution config; transaction
20260906T023351175Z-7c83c3949254. Installed DLL hash69F3CA64…37A7F5D verified.
No old inventory or save was edited; this prevents future invalid-count work and
does not establish whether a particular past container received excess items.
Runtime behavior remains open. Receipt:
`records/source-builds/ensrick-cdf-nonpositive-counts-20260906.json`.

## Remaining evidence and acceptance gates

- Solitude #243: the currently retained session ends in Bruma, not near the college.
  No exact duplicate placement was proved. Grand's college/ground-cover references
  AFC5BE/AFC5C0 share a transform but are not equivalent geometry. A screenshot plus
  clicked reference/position is needed before any targeted A/B change.
- Missing Forsworn body-morph TRI is independently tracked in #245; no arbitrary
  mesh from a different topology was substituted.
- Only four Papyrus rotations and mostly singleton SKSE logs survive. No crash file
  newer than September1 was found; that does not prove all later sessions exited
  cleanly or that the earlier wall flicker was recorded.
- Firefox has not yet acknowledged the queued Keep114690. Installed195 Nexus IDs
  versus194 liveKeeps is an explicit current gate failure, not a completed sync.
- No game was launched. Launch/load under60 seconds and feature-specific disposable
  gameplay tests are still required. No existing real save needs deletion for these
  DLL/mesh fixes; use fresh victims/equipment and a fresh process for verification.

Final scoped checks after arrow deployment: zero-error MO2 audit; installed arrow
and CDF runtime metadata PASS; installed cloak and weapon freshness PASS;21 cloak
tests plus12 strict-reader tests PASS; original helmet recipe AST and pinned hash
PASS; all current JSON receipts parse. Four unrelated dirty conflict reports still
match their original hashes. Full project preflight was not rerun and is not
claimed clean; the explicit Keep acknowledgment and runtime gates remain open.
