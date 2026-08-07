# Original two-handed archive versus 2024 SSE upload

Audited 2026-07-31. The 2024 upload is not used as a porting source.

| Area | Original Nexus 26261 file | 2024 Nexus 126568 file | Finding |
|---|---|---|---|
| Intended edition | Two-handed | One-handed | Different editions; the newer ESP cannot replace the requested plugin. |
| ESP header/records | Form 40, header 0.94 | Form 40, header 0.94 | The newer ESP was not resaved as an SSE form-44 plugin. |
| Weapon behavior | `TwoHandSword`, `TwoHanded`, usually speed 0.80/stagger 0.90 | `OneHandSword`, `OneHanded`, usually speed 0.85/stagger 0.80 | Intentional edition-level changes, not conversion fixes. |
| NIF files | 12, Skyrim LE stream 83 | 12, Skyrim LE stream 83 | Every purportedly ported mesh still reports the LE stream version. |
| DDS files | 73 | 73 | All 73 pairs are byte-identical; no texture conversion occurred. |
| Text record tree | 131 files | 130 files | The distribution differs because the editions edit different 1H/2H leveled lists. |
| Duplicate download | n/a | Two local copies | Both newer archives have SHA-256 `D18A57CADF09A46C050032A052B69BBFF1C7A803F274C3AECA86B305EB2E97B9`. |

The newer NIFs differ byte-for-byte from the originals and have rewritten shape data,
but retaining stream 83 means the rewrite did not complete an LE-to-SE conversion.
Loading without unknown blocks is not sufficient evidence of an SSE port.

The private local build instead starts from the user's two-handed original, converts
the meshes to stream 100/BSTriShape, removes Dragonbone records and assets, and emits
a form-44/header-1.7 plugin through Spriggit.
