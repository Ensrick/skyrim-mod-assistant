# Dependency provenance

The parser, CLI and tests in this directory are original MIT source. Format
structure is independently implemented against the project's read-only Python
ESS/co-save gates and existing SKSE Serialization.cpp layouts; no Bethesda
code, player save data, or licensed mod assets are included.

The currency checkpoint contract is the existing original repository file
`mods/currency-integration/native/src/SaveMarkerPolicy.h`, compiled by include.

## zlib1.3.2

[Official release and published SHA256](https://zlib.net/), checked2026-09-09.
Source URL: `https://zlib.net/fossils/zlib-1.3.2.tar.gz`.
Identical upstream GitHub release asset (preferred build mirror):
`https://github.com/madler/zlib/releases/download/v1.3.2/zlib-1.3.2.tar.gz`.
GitHub asset357391855 reports the same SHA256 and1502830-byte length.
SHA256: `bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16`.
Fetched unchanged into the build directory, built statically. The MIT license
on our source does not replace zlib's license. Preserve this notice with any
future source/binary package including zlib. CMake source overrides are local
development escape hatches, not hash-attested release inputs.

Upstream LICENSE:

```text
Copyright notice:

 (C) 1995-2026 Jean-loup Gailly and Mark Adler

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.

  Jean-loup Gailly        Mark Adler
  jloup@gzip.org          madler@alumni.caltech.edu
```
