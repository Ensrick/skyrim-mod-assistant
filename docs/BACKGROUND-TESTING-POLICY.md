# Background testing policy

Autonomous Skyrim work must not create windows, modal dialogs, browser tabs,
audio, focus changes, cursor capture, or other visible activity on the user's
active desktop.

- Do not launch Skyrim, Steam URLs, MO2's GUI, or other GUI tools on the active
  desktop without the user's explicit permission for that specific launch.
- Static validation, headless tools, file inspection, and log inspection are
  permitted.
- A runtime smoke test must use a genuinely isolated Windows desktop/session or
  wait for explicit permission. A hidden console window is not UI isolation.
- Background launches must set `SKSE_AUTOMATION_SILENT_UI=1`. Our SKSE build
  then redirects plugin `MessageBoxA/W` imports to `skse64.log` and returns a
  conservative non-affirmative result.
- Our SKSE build is side-effect free by default. Its post-build deployment runs
  only when `SkseDeployOnBuild=true` and an explicit `Skyrim64Path` are passed.
- Failures and important notices are reported through logs for the managing
  agent to inspect. They are never surfaced as unattended user-facing popups.

`audit/launch_skyrim.ps1` refuses to launch unless
`-AllowInteractiveDesktop` is supplied explicitly.
