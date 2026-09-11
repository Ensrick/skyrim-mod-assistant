# WITHDRAWN 2026-09-10 - do not send

SlavicPotato was excluded the same day (`docs/EXCLUDED_AUTHORS.md`, commit 985c074: no forking, no code copied, his function moved in-house). Asking him to publish the framework so IED could be ported contradicts that decision. Kept only as a record of what was considered; the successor is #269 (own framework) and #36 (rules layer).

---

# Draft: request to SlavicPotato for the IED framework (user sends; edit freely)

**Where to send:** GitHub issue on `SlavicPotato/ied-dev`, or Nexus PM (Immersive Equipment Displays, mod 62001). Not sent by the assistant.

**Subject:** Would you publish sse-build-resources (or a 1.7.x IED build)?

Hi SlavicPotato,

I run a Skyrim SE 1.7.104 build and rebuild plugins from source when authors are away, so I tried to port Immersive Equipment Displays. `ied-dev` builds against `..\sse-build-resources\` (the vcxproj include path), but that repo is no longer public, and the only mirror is from February 2022, before the 51 `ext/` headers current IED needs existed. I checked every SlavicPotato repo, the fork network, Software Heritage and Wayback: none carries the current `ext/`.

Your Simple Dual Sheath 1.5.9 (2026-08-29) shows the framework is alive and already targets 1.7.x, so IED is likely a short port for you and impossible for anyone else. Would you consider either:

1. publishing `sse-build-resources` again (even a snapshot, no support implied), or
2. shipping a 1.7.x build of IED?

IED is MIT, so I would be glad to do the porting work and send it back as a PR if the headers were available. Happy to test 1.7.104 builds as well. Thank you for IED and SDS; they are still the only tools of their kind.

- Ensrick
