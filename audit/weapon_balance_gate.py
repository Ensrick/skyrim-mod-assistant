"""Read-only preflight bridge to the weapon generator's freshness verifier.

Does not generate, install, launch the game, or invoke MO2's VFS. The generator
owns the manifest semantics; this bridge only turns its exit status into a
normal preflight failure. A disabled balance plugin is not silently enabled.
"""

from pathlib import Path
import subprocess


PLUGIN = "WeaponBalancePatch.esp"
MOD_FOLDER = "Ensrick - Weapon Speed Balance"


def run(fails, warns, *, repo, instance, profile="Default", runner=subprocess.run):
    repo, instance = Path(repo), Path(instance)
    plugins = instance / "profiles" / profile / "plugins.txt"
    if not plugins.is_file():
        fails.append("weapon balance: profile plugins.txt is missing")
        return
    active = {
        line.strip()[1:].casefold()
        for line in plugins.read_text(encoding="utf-8-sig").splitlines()
        if line.strip().startswith("*")
    }
    if PLUGIN.casefold() not in active:
        return
    script = repo / "mods" / "weapon-balance" / "audit.ps1"
    artifact_root = instance / "mods" / MOD_FOLDER
    if not script.is_file() or not artifact_root.is_dir():
        fails.append("weapon balance: active patch lacks its owned verifier/artifact directory (#239)")
        return
    command = [
        "pwsh", "-NoProfile", "-NonInteractive", "-File", str(script),
        "-FreshnessOnly", "-Instance", str(instance), "-Profile", profile,
        "-ArtifactRoot", str(artifact_root),
    ]
    try:
        result = runner(command, capture_output=True, text=True, timeout=180,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        fails.append(f"weapon balance: freshness verifier could not complete ({type(exc).__name__})")
        return
    if result.returncode != 0:
        detail = " | ".join((result.stderr or result.stdout or "no diagnostic").strip().splitlines()[-4:])
        fails.append("weapon balance is stale or invalid (#239); review/regenerate before play: " + detail[-700:])
