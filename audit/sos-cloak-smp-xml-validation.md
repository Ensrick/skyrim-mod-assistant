# Sons of Skyrim female SMP XML check — no repair warranted

[Issue #244](https://github.com/Ensrick/skyrim-mod-assistant/issues/244) began
with a suspected wrong-sex physics configuration in four female cloak meshes.
The suspicion is **disproven**. No vendor file was changed and no repair overlay
was generated.

The approved Sons of Skyrim HDT cloak patch (Nexus SSE114690, file483316)
contains48 worn NIFs. Decoding each actual root extra-data link gives:

| Mesh family | Files | Active root-linked XML |
|---|---:|---|
| Female, both weight endpoints |24|`capeF_SoS.xml`|
| Male, both weight endpoints |24|`capeM_SoS.xml`|

All48 parsed and each had exactly one root-linked NiStringExtraData named
`HDT Skinned Mesh Physics Object`. There were zero sex/config mismatches.
The four initially suspected files contain **both** XML filenames in their
header string tables. The male filename is an unused leftover, not the active
configuration. The Scene Root links the following blocks, which point to the
female string:

| File under `Meshes/NordWar/SonsOfSkyrim/Cloack/` | Extra-data block | String index | Actual value |
|---|---:|---:|---|
| `CloackOfficerF_0.nif` |913|885|`capeF_SoS.xml`|
| `CloackOfficerF_1.nif` |916|888|`capeF_SoS.xml`|
| `CloackPauldronF_0.nif` |916|888|`capeF_SoS.xml`|
| `CloackPauldronF_1.nif` |916|888|`capeF_SoS.xml`|

The four paths were separately resolved as current MO2 loose winners from
`Sons of Skyrim - HDT Physics for Cloaks Patch`. Their shapes are the female
`VirtualLegs`, `VirtualArms`, `VirtualBreasts`, `VirtualButt` collider family,
matching the already-linked female XML. Ordinary female and male cloak meshes
were inspected as controls.

Audit rule: follow `NiNode.ExtraDataList` → the actual NiStringExtraData block →
its `StringData` reference. Do not infer active behavior from a raw string search
or the presence of a filename in the NIF header table.

Local full48-file inventory and read-only reproducer are retained under
`records-work/sos-female-xml-2026-09-06/`. Inventory SHA256:
`CFC2661995CECF46229E7DC7CA9EED8303479F545F06633E38EE86FF675E552B`.
Inspection used NiflySharp from the existing HouseCARL build, binary SHA256
`B8410282CBC48388E07C1099A7FDA79F1533410F6A3E1C2E3DDBE0818D76EA22`.

This confirms config linkage only. It is not a claim that cloth motion,
collision behavior, performance or every FSMP setting has passed gameplay
acceptance. Changing an unused string would not improve the active physics.
