# Security and crash reporting

Please report crashes and corrupted-save concerns through a private GitHub
security advisory when the report contains personal paths or an unreleased
save. Ordinary reproducible defects may use the public issue tracker.

Attach the Bounded Encounters log, SKSE log, crash logger report, exact game and
SKSE versions, configuration, and a minimal reproduction. Remove personal data
before uploading.

The plugin must fail closed when configuration or runtime validation fails. It
must never display modal dialogs; errors go to the log and disable spawning.
