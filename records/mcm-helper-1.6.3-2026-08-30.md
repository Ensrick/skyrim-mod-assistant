# MCM Helper 1.6.3 adoption record — 2026-08-30

Trackers: [configuration #39](https://github.com/Ensrick/skyrim-mod-assistant/issues/39) and [persistence #40](https://github.com/Ensrick/skyrim-mod-assistant/issues/40)

## Decision and provenance

The `Default` MO2 profile now uses the unmodified official MCM Helper 1.6.3
runtime from Nexus SSE mod 53000, file 795510. Nexus describes that file as
compatible with Skyrim SE 1.7.99+ and requiring SkyUI 6+. The retained archive
is `53000-795510.7z`, 8,187,265 bytes, SHA-256
`505AF9C27062FEBD497BE09B661D5DF82E013AE4A205FFBEC99698ADF4503F52`.
That is also the hash in the file's official external virus-scan URL.

The corresponding official source is Exit-9B/MCM-Helper `main` commit
`a30334864ea46ab6ee9e74bca06187630b67c039` (*fix: update for SkyrimSE
1.7.99*). Upstream has not tagged 1.6.3. The commit changes the project version
to 1.6.3, updates CommonLibSSE, and selects the correct virtual-machine member
layout at the 1.7.99 runtime boundary. The repository is MIT-licensed. The
public modpack may therefore redistribute an exact build with the MIT notice,
but the default packaging policy remains to cite/download the official Nexus
file and keep any future source-built variant in a separately named overlay.

## Compatibility boundary

- Installed game runtime: `SkyrimSE.exe` 1.7.104.0.
- Installed SKSE runtime DLL: `skse64_1_7_104.dll` 2.3.1.
- Enabled Address Library: v12, including
  `SKSE/Plugins/versionlib-1-7-104-0.bin`.
- Enabled SkyUI: 6.11, `SkyUI_SE.esp`.
- Official source declares Address Library use, requires SKSE 2.2.5 or newer,
  and rejects only SE runtimes older than 1.6.317. These requirements are met.
- `MCMHelper.dll` reports file/product version 1.6.3.0, exports
  `SKSEPlugin_Load`, `SKSEPlugin_Query`, and `SKSEPlugin_Version`, and has
  SHA-256
  `D58F433BEF7690614D42AAAC69CC35F60D179A85429A385E21858A1F276AEF38`.
- Like other CommonLibSSE plug-ins, the official DLL imports `MessageBoxW` for
  fatal failure reporting. No such path was invoked here because no game was
  launched. Any future autonomous runtime check must use the isolated launcher
  and `SKSE_AUTOMATION_SILENT_UI=1` under the background-testing policy.

The selected FOMOD-equivalent payload is Skyrim SE + ESL + BSA. The tracked
install plan also retains the official PDB that belongs to the SE DLL choice;
it is inert at runtime but makes crash-symbol and provenance checks exact.
`MCMHelper.esp` is a 100-byte ESL-flagged header plugin with `SkyUI_SE.esp` as
its only master and no records. In the final LOOT order SkyUI is active at line
20 and MCM Helper at line 94, so the latter's BSA intentionally supplies the
extended `SKI_ConfigMenu.pex` after SkyUI's BSA.

## Installation and static acceptance

- MO2 installation transaction:
  `20260830T154334926Z-1e5681066bbe`.
- Plugin-enable transaction:
  `20260830T154335663Z-774f9f424f16`.
- Deterministic plan: `records/fomod-plans/53000-mcm-helper.json`.
- The current official LOOT pass completed after installation and retained the
  required SkyUI-before-MCM-Helper order.
- MO2 profile audit: clean, zero errors.
- Installed-ledger verification: 152 entries, zero problems.
- Master/order audit: 136 active plugins, 222 discoverable, clean.
- Loose-file conflict audit: no MCM Helper native, Papyrus, interface, plugin,
  or configuration collision. The intentional BSA-over-BSA SkyUI script
  replacement is governed by the verified plugin order described above.
- No `MCMHelper*` file or MCM Helper SkyUI configuration was copied into the
  physical game `Data` directory. Every runtime file remains in the managed
  MO2 mod.
- The Nexus curator records mod 53000 as Keep; uploader Parapets (user
  39501725) was not in Excluded.

No game or GUI tool was launched. The remaining acceptance test is a foreground
game smoke test: confirm `MCMHelper.log` reports 1.6.3 without a loader error or
dialog, open SkyUI's MCM, change a helper-backed value, and prove its INI is
written and survives save/reload. This record does not claim that traditional
save-local MCMs become portable merely because the framework is active.

## Exact rollback

The parked 1.6.2 folder remains byte-for-byte under
`.mo2-headless-trash/20260830T154334926Z-1e5681066bbe-MCM Helper`, and its
official archive remains `downloads/53000-746161.7z` with SHA-256
`24B07DADC471F58929255B5C189847E5A0B2C883C1834887CA9CB558E521BE30`.
To restore the old disabled vendor folder without undoing later global LOOT
work, while Skyrim and MO2 are closed, first disable the active plugin and then
roll back the mod-install transaction:

```text
MO2Headless.exe --root <instance> plugin-disable MCMHelper.esp
MO2Headless.exe --root <instance> rollback 20260830T154334926Z-1e5681066bbe
```

Then restore the 1.6.2 ledger row (`fileId` 746161, `enabled: false`, installation
transaction `20260823T061611548Z-1505c26a6afa`) and clear mod 53000 from Keep.
Do not delete either transaction journal, the transaction trash folder, or the
old archive until the foreground smoke test has passed.
