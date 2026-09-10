# Read-only Papyrus inventory

`SavePapyrusInventory.java` is an original diagnostic consumer, not a cleaner,
save editor, mod, or campaign migration tool. It requires an exact input SHA256,
headless Java, a bounded input file, successful parser completion and unchanged
input bytes. It calls no writer or cleaning API. Reports contain private save
state and must remain outside source control.

The locally verified parser is Apache-2.0 FallrimTools source from
<https://github.com/mdfairch/FallrimTools>, commit
`61bb57d895f023617cb55045a4907849fd1ff566`. This is a pinned format reference,
not a claim that its old GUI is the latest release. Its tracked compiled files
were not used. Java 24 compiled the consumer and transitive parser source:

```powershell
javac -encoding UTF-8 -cp '.readonly-deps/*' -sourcepath src/main/java -d .readonly-classes C:\path\SavePapyrusInventory.java
java '-Djava.awt.headless=true' -cp '.readonly-classes;.readonly-deps/*;src/main/resources' SavePapyrusInventory C:\path\save.ess EXPECTED_SHA256
```

Dependencies are the upstream pom's Maven Central versions: annotations16.0.2,
picocli4.6.3, universalchardet1.0.3, lz4-pure-java1.7.0, j2html1.5.0, and
OpenJFX base/graphics/controls/swing11 Windows classifiers. Keep their licenses;
none are repackaged here. Headless AWT prevents interactive window creation.

Known upstream display defect: `Variable.Array.getElementType()` subtracts 7
from the array enum ordinal although the array enum starts at11. Its string
formatter can misleadingly describe a string array as boolean. The consumer
does not use that formatter: it prints the parsed variable type, referenced
array ID, length and array's own parsed element type. No upstream source was
modified. Absence of parser errors is not proof of engine/save compatibility.

## Serialized position inspection (experimental)

`SavePlayerLocation.java` uses the same pinned source/dependencies and compile
command, substituting its class/file name. The default invocation requires the
player ACHR body to parse fully. That **refused** the current Save5 fixture even
though the outer ESS parsed; this is not evidence that the save is corrupt.

An explicitly supplied third argument `--prefix-only` permits a bounded INITIAL
prefix read when full ACHR decoding is unsupported. Types 4 and 6 follow the
pinned parser's flag rules; the player is the existing RefID14, not a created
reference. The diagnostic reports `fullAchrParsed=false` and never upgrades that
to a full-record certificate. Positions/rotations must be finite, and the
prefix must have its exact size. The serialized field called CELL may contain a
worldspace (the tested exterior fixture resolves to Tamriel 0000003C); do not
equate it with the live parent cell automatically. Global data type2 stays opaque.

The prefix agreed with live X/Y and approximately Z, and all three agreed
exactly immediately after a cold load. Scope and runtime results are recorded
in `docs/PLAYER_OBSERVATION_2026-09-10.md`. The Java consumer was compiled and
tested locally on Java24, not by the portable Python CI job. Private ESS files,
raw reports and compiled parser artifacts are not shipped.
