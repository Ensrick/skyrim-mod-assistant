# Crash evidence and closure standard

Scope: native crash investigations and claims made to the user. Complements
the broader testing/lifecycle work in #227/#102; does not declare it complete.

1. **Identify the run before diagnosing.** Preserve logs, exact input-save
   hash, executable/DLL identity, profile, load order and event timeline.
   Distinguish a live probable frame from an incidental scanned-stack value.
2. **State the evidence level.** Observed signature, suspected cause, controlled
   reproduction, implemented repair, targeted runtime verification, sustained
   play and campaign recovery are different claims. A successful callback,
   process exit0, build, unit test or CI run cannot substitute for another level.
3. **Match the test to the claim.** A fresh character does not prove an old
   campaign repaired. Diagnostic-forced coverage is useful but must be labeled;
   disclose untested production preconditions and empty populated-object tests.
4. **Negative evidence overrides success.** Death, fresh matching crash report,
   admission rejection or required feature failure fails that scenario even
   after a successful load event. Observe beyond initialization; the launch
   harness's60-second floor is only a bounded smoke test, not a soak certificate.
5. **Treat scope as part of the result.** A mechanism-level bug may close with
   controlled failing/passing evidence, applicable regression tests and clear
   exclusions. The parent gameplay/campaign incident stays open until its own
   acceptance criteria pass. Put unresolved blockers in the final user message.
6. **Respond to every recurrence.** Compare signatures and inputs, attach the
   new evidence, and reopen the same defect if it recurs. Otherwise link an open
   incident; do not dismiss it simply because it differs from the last repair.
7. **Improve detection without hiding faults.** Add a relevant regression or
   diagnostic when supported. Do not replace a corrupt-pointer crash with a
   silent skip and call the underlying fault fixed. Do not automatically clean
   saves, restore rejected mods or choose a campaign migration for the user.
8. **No universal stability claim.** Finite tests establish the recorded cases,
   not a100% guarantee over all saves/actions. Clearly distinguish empirical
   verification of a specific repair from completion of the user's experience.
