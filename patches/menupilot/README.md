# MenuPilot camera experiment — not an accepted feature

`experimental-look267.patch` preserves original candidate source from local
MenuPilot commit `5e59613`, based on `9be3f58`. It is a zero-context patch:
apply only to that exact base using `git apply --unidiff-zero`, not to installed
vendor assets. The installed MenuPilot remains `1A1D5CEC` / source `b3b1b31`.
The intervening base commit adds the earlier CancelLoading diagnostic; it was
not exercised in this experiment. No new public repository or binary release.

**The experiment did not rotate the character. Do not install it as a fix.**
See `docs/MOUSE_LOOK_EXPERIMENT_2026-09-10.md` for measured evidence and remaining
limitations. Source preservation prevents an unsuccessful approach being
repeated or falsely presented as accepted functionality.

Build option `MENUPILOT_EXPERIMENTAL_LOOK` defaults OFF. An ON build additionally
requires `SKYRIM_MENU_PILOT_EXPERIMENTAL_LOOK=1`; the isolated launcher provides
an explicit `-ExperimentalMenuLook` switch after clearing inherited automation
flags. Do not change that default or enable the experiment in a user profile.
Current local CMake cache has been returned to OFF and that build was checked.

The standalone `tests/look_contract.cpp` compiles as C++20 against the existing
pinned nlohmann-json include directory. Run it as a bounded private worker;
exit0 means its15 input-contract assertions pass, not that native input works.
Its CHECKs remain active with NDEBUG and report failing lines without assert
dialogs. The source uses the existing CommonLib6.7.1 pin; no new dependency.

Acceptance gaps include input phase/ordering, actual camera motion, deadline
and lifetime-cap runtime controls, and broader travel/combat. Argument tests,
known-function bytes and a clean process exit do not fill those gaps.
