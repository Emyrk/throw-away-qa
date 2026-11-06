# Agent-Relay QA, November 5-6, 2026

Nine runs covered ten distinct variants: **7 pass, 2 fail, 1 blocked**. These are the latest verdicts per variant, not a full-suite pass.

| Tests | Result | What was observed |
| --- | --- | --- |
| Q01-a/b | Pass | Claude and Cursor healthy turns succeeded after QA owner membership was corrected. |
| Q02-build/startup/death | Pass | Cursor reported scoped build, connection, and deterministic worker-exit failures safely. The death fixture was `/bin/false`, not SIGKILL. |
| Q05-a | Fail | Claude rebuilt with a fresh build secret; the original Cursor session did not rebuild. |
| Q06-a/b | Pass | Isolated processes rejected the obsolete Claude key and unitless positive Cursor timeout. |
| Q06-c | Blocked | A timed Claude follow-up kept its runner serving, then it exited cleanly; Cursor was deferred. |
| Q06-d | Fail | Under Claude zero idle, two runners failed to start. Baseline restoration succeeded; the exact cause remains unverified. |

Only Q02-build and Q02-startup have reviewed, sanitized screenshots. Other results have timestamped text evidence, not screenshots. The [QA viewer](https://emyrk.github.io/throw-away-qa/) shows the latest verdicts, screenshots, and original run timelines.
