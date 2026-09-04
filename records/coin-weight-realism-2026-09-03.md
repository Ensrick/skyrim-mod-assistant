# Physical Septim weight decision — 2026-09-03

## Decision

The owned regional-currency integration sets the three physical modern Septim
denominations to these carry weights:

| Physical coin | ECE form | Value | Weight |
|---|---|---:|---:|
| Copper Septim | `000B6D:exchangeCurrency_enhanced.esp` | 1 | 0.06 |
| Silver Septim | `000823:exchangeCurrency_enhanced.esp` | 25 | 0.07 |
| Gold Septim | `000824:exchangeCurrency_enhanced.esp` | 100 | 0.13 |

The hidden vanilla `Gold001` (`00000F:Skyrim.esm`) remains weight 0 because it
is the currency stack's accounting backend, not a physical inventory coin. ECE's
four display-only plural-name proxy records also remain weightless. Ancient and
regional currencies are outside this decision and retain their existing policy.

## Basis

Skyrim calls the statistic “Carry Weight” and does not define it as pounds.
For this modlist, 1.00 carry weight is treated as approximately one pound so
coin encumbrance can be tuned consistently with the later inventory overhaul.
Direct inspection found that the three installed ECE denomination meshes have
identical geometry and bounds (144 vertices and 140 triangles). Their mass
distinction should therefore follow material density, not denomination value.
The inspected inputs were `meshes/clutter/coin01.nif` (7,105 bytes, SHA-256
`05B475353833C66D646F90668D3B078B2F9949F871ED0C7E906A5EDC371451BA`),
`silvercoin.nif` (7,109 bytes,
`C9740B1098FADEA2A63C0C6BE6CB28D915F8F8B0918A82B3761CAC81847A00F6`),
and `goldcoin.nif` (7,105 bytes,
`8359271B2B4C553E840A77E8F06D12067799CF8DFDBF02ABC16A435460AF44C5`).

The 0.06 copper baseline is about 27.2 grams, comparable to unusually large
historical bronze/copper circulation coins: a Roman sestertius in the
[Metropolitan Museum](https://www.metmuseum.org/art/collection/search/248042)
is 26.6 g, another in the
[British Museum](https://www.britishmuseum.org/collection/object/C_R-6345) is
27.48 g, and Britain's 1797 cartwheel penny was specified at one ounce by the
[Royal Mint Museum](https://www.royalmintmuseum.org.uk/journal/curators-corner/penny/).
Silver 0.07 and gold 0.13 preserve rounded same-volume density ratios of about
1:1.17:2.16, using the Royal Society of Chemistry's densities for
[copper](https://periodic-table.rsc.org/element/29/copper),
[silver](https://periodic-table.rsc.org/element/47/silver), and
[gold](https://periodic-table.rsc.org/element/79/gold). This deliberately avoids
treating the visibly oversized game mesh as a literal solid-metal object, which
would produce unplayably heavy coins.

## Implementation boundary

ECE's `ECE_septims_100.ini` reapplies weights 0.01/0.02/0.03 at runtime. An ESP
override alone would therefore lose. Version 0.2.5 adds the original,
late-sorting `zz_Ensrick_Currency_SeptimWeights.ini`, containing exactly three
SkyPatcher weight assignments. It changes no name, value, model, reference,
leveled list, or script and does not modify or copy an ECE file. The ECE source
config is pinned by byte count and SHA-256 so an upstream change fails the
reproducible build instead of silently changing precedence.

## Acceptance gates

- Static validator proves the exact three weight-only rules and rejects any
  `Gold001`, value, or display-name edit.
- The package rebuild and archive are deterministic.
- The live SkyPatcher log must show the owned file processed after
  `ECE_septims_100.ini`.
- Main-menu and existing-save launch gates must pass without new native,
  Papyrus, or configuration errors.
- In-game inventory inspection of one coin of each denomination remains a
  targeted gameplay check before public release.
