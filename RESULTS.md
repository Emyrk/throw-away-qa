# Agent-Relay QA, November 5-6, 2026

Latest result per tested variant: **7 pass, 2 fail, 1 blocked**. The full run records hold timestamps and earlier attempts.

| Test | Tried | Happened | Wanted |
| --- | --- | --- | --- |
| Q01-a | Sent a Claude QA prompt. | A runner connected and replied; no Cursor crossover. | Claude replies from its own QA pool. |
| Q01-b | Sent a Cursor QA prompt. | A runner connected and replied; no Claude crossover. | Cursor replies from its own QA pool. |
| Q02-build | Forced a QA-only Cursor build failure. | Cursor showed safe failure guidance. | The claimed request ends with safe guidance. |
| Q02-startup | Prevented a QA Cursor agent from connecting. | Failure followed the startup grace; Cursor showed guidance. | Wait for the deadline, then explain the failure. |
| Q02-death | Exited a QA Cursor worker with /bin/false. | Cursor received safe retry guidance. | An exited worker ends its claim safely. |
| Q05-a | Tried to rebuild both providers with build secrets. | Claude rebuilt; the original Cursor session did not. | Both original sessions rebuild with fresh secrets. |
| Q06-a | Used the obsolete Claude idle setting in an isolated process. | Startup rejected the old key and named its replacement. | Reject the old key with a useful error. |
| Q06-b | Used a unitless Cursor timeout in an isolated process. | Startup rejected the invalid value. | Require a unit on positive timeouts. |
| Q06-c | Sent a Claude follow-up before its idle release. | Claude replied and later released; Cursor was deferred. | Both providers reset idle timers and release later. |
| Q06-d | Set Claude idle release to zero and sent a prompt. | Two runners failed to start; retention was untested. | Healthy runners remain through twelve idle minutes. |

Only Q02-build and Q02-startup have reviewed screenshots. Q02-death used `/bin/false`, not SIGKILL. The Q06-d runner failure cause is unverified. [View the results](https://emyrk.github.io/throw-away-qa/).
