# Nexus Mods API access

This repository uses the official Nexus Mods API for current metadata, file
inventory, authenticated downloads, and quota checks. Browser authentication,
cookies, and page scraping are not part of this workflow.

The procedure below contains no credential. The currently provisioned personal
API key remains in the sibling `crusader-de-tweaker` checkout's ignored file:

```text
../crusader-de-tweaker/scripts/nexus/nexus.local.json
```

That file was successfully validated against the Nexus API on 2026-08-12. Do
not copy it into this repository merely for convenience.

## Credential resolution

Resolve a key only at request time, in this order:

1. An explicit `-ApiKey` parameter supplied to the calling command.
2. The process environment variable `NEXUS_API_KEY`.
3. An ignored `nexus.local.json` beside the calling Nexus script.
4. The ignored sibling-repository file shown above.

The JSON property is `ApiKey`:

```json
{
  "ApiKey": "PASTE-YOUR-PERSONAL-NEXUS-API-KEY-HERE"
}
```

Resolution must fail closed if no non-placeholder value is available. Scripts
must never print the key, include it in an exception, add it to a command-line
argument visible to another process, or persist it in generated reports. Do not
commit `nexus.local.json` anywhere.

## Read and download API

Use `https://api.nexusmods.com/v1` with these headers:

```text
apikey: <resolved at runtime>
application-name: SkyrimModAssistant
application-version: <current tool version>
```

Relevant Skyrim Special Edition operations are:

```text
GET /users/validate.json
GET /games/skyrimspecialedition/mods/{mod_id}.json
GET /games/skyrimspecialedition/mods/{mod_id}/files.json
GET /games/skyrimspecialedition/mods/{mod_id}/files/{file_id}.json
GET /games/skyrimspecialedition/mods/{mod_id}/files/{file_id}/download_link.json
```

Use the returned download URI immediately and write the response only into an
ignored work directory. Do not log download URIs: they can contain temporary
authorization material. Record the Nexus game domain, mod ID, file ID, version,
byte length, retrieval date, and SHA-256 instead.

The authenticated account currently has Premium download access, so the API can
return download links without browser interaction. Code must still handle an
authorization or Premium-policy failure explicitly rather than falling back to
scraping.

Read the Nexus rate-limit response headers and stop before exhaustion. A `429`
response is not a reason to rotate credentials or retry aggressively; preserve
the request state and wait for the reported reset.

## Upload API separation

Publishing in `crusader-de-tweaker` uses the official v3 upload API and is a
separate, state-changing workflow. Possession of the shared credential does not
authorize Skyrim Mod Assistant to upload, edit, endorse, track, or otherwise
mutate Nexus state. This repository's default Nexus use is read-only.

## Publication boundary

Nexus archives and extracted contents remain third-party material. They belong
only in ignored work storage and must not be committed or redistributed unless
the applicable permissions explicitly allow it. Public records should contain
links, identifiers, factual metadata, hashes, and our own audit results.
