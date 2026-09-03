# Ensrick CRF Semantic Patch

This source generates the private, profile-specific `Ensrick CRF Semantic
Patch.esp` tracked by issue #71. It preserves five evidenced Cutting Room Floor
3.1.26 semantics while retaining the current Water for ENB, NFF, Lux, and
Skyrim Unbound winners.

The output contains one CELL, three LCTN, one INFO, and the INFO's required DIAL
group anchor. It is an ESL-flagged ESP containing overrides only. The ambiguous
`SolitudeHalloftheDeadCatacombs` XLCN is intentionally absent.

The generator is locked to Mutagen 0.54.4 and Synthesis 0.36.6. The reviewed
build was run twice through the project's headless MO2 VFS against the sorted
Default profile; both outputs had SHA-256
`D3EA7952099EF73AC30B1C9BF4094A3886065FC781568FAA1F05AA3D0F8A257C`.
Spriggit 0.41.0 checked serialization and a text round trip produced tree hash
`6F0032F9CE581B1641A70182644144CBD62508731AD72145CE74057711C149D3`.

The installed output is private. Cutting Room Floor requires advance author
permission before a compatibility patch may be distributed. Do not upload or
embed the generated plugin in a public collection until that permission is
recorded. Vendor files are never modified or included here.
