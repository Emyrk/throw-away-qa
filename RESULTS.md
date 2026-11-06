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

Only Q02-build, Q02-startup and Q06-c have reviewed screenshots. Q02-death used `/bin/false`, not SIGKILL. The Q06-d runner failure cause is unverified. [View the results](https://emyrk.github.io/throw-away-qa/).

## Timeline: Q06-c (918b5a54-4dba-4120-82e0-9f4de2936e8e)

Times below are UTC on 2026-11-06. Browser submission and reply times are observation bounds; Relay and Coder source times are rounded to milliseconds.

| UTC | Action or event |
| --- | --- |
| 05:31:30.162 to 05:31:38.115 | Sent a new Claude QA prompt asking for a harmless command exit. |
| 05:31:38.595 / 05:31:51.117 | Coder created the workspace; Relay handed off the runner. |
| By 05:32:09.950 | The command exited 1; Claude replied normally, not with a runner failure. |
| 05:41:16.916 to 05:41:17.982 | Same runner was serving at the pre-follow-up T+9 sample. |
| 05:41:35.662 to 05:41:46.167 / by 05:41:59.144 | Sent a same-session follow-up; saw its reply. |
| 05:52:00.444 / 05:52:09.723 | Runner still served beyond the follow-up's ten-minute boundary; Relay observed clean done 0. |
| By 05:52:31.799 | First workspace was absent; browser subsequently showed the session paused. |
| 05:55:43.775 to 05:55:52.627 / by 05:56:24.742 | Resumed on a new workspace; saw a reply retaining earlier context. |
| 06:06:46.399 / by 06:07:26.944 | Relay observed the second clean exit; the second workspace was absent. |
