# STAGED upstream issue (needs user OK to post)

Target: github.com/ryobg/JContainers/issues
Title: v4.3.1 declares 1.6.318, refused on 1.7.99

Body:

**Symptom:** SKSE (official 2.3.0 and master builds) refuses
JContainers64.dll v4.3.1 at load: `disabled, incompatible with current
version of the game`.

**Evidence:** the dll's `SKSEPlugin_Version` struct declares
`compatibleVersions = [0x10613E0]` (= 1.6.318). Runtime 1.7.99 packs as
`0x1070630`. The skse64 **v2.3.0 tag** defined `RUNTIME_VERSION_1_7_99` as
`MAKE_EXE_VERSION(1, 6, 318)` by mistake; ianpatt fixed it in master commit
614c755 ("oops #59") after the tag - a 4.3.1 build against the tag headers
inherits the wrong constant.

The same constant is compiled into the plugin's own runtime check: after
correcting the version-data struct, the dll still self-disabled with
`unsupported runtime version 01070630` in JContainers64.log.

**Fix:** rebuild against skse64 master (or current headers) so both the
`compatibleVersions` entry and the internal check carry `0x1070630`.
Locally verified: patching both compiled constants makes the same dll
accept 1.7.99.

**Refs:** ianpatt/skse64@614c755, ianpatt/skse64 issue #59.
