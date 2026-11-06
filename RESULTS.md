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

## Timeline: Q05-a (e0912a27-7154-40a5-bf8e-44887730dfd7)

Times are UTC on 2026-11-05 unless marked Nov 6. "By" marks an observation or tester confirmation, not an exact provider reply time. Only secret presence, never values, was checked.

| UTC | Action or event |
| --- | --- |
| 23:24:29.176 / 23:24:29.465 / 23:24:39.759 / by 23:25:04.042 | Cursor request claimed, workspace created and built; build-secret presence confirmed. |
| 23:25:46.684 | Relay claimed a second Cursor request. |
| 23:26:17.885 / 23:26:38.791 / by 23:26:43.868 | Claude workspace created and built; build-secret presence confirmed. |
| By 23:27:48.542 | Tester identified the second Cursor request as a separate session and excluded it. |
| By 23:28:26.675 | Tester confirmed normal replies from the two original sessions; exact reply times unknown. |
| 23:30:36.319 / 23:30:47.488 / by 23:31:29.928 | Original Cursor and Claude workspaces stopped; their stop builds had no build secrets. |
| By 23:32:06.038 | Tester reported a follow-up in the original Cursor conversation; receipt time was unverified. |
| 23:32:13.593 / 23:32:13.873 / by 23:32:29.292 | Relay claimed the excluded Cursor session and built a different workspace; the original did not rebuild. |
| 23:38:12.729 / 23:38:23.513 | Relay recognized and rebuilt the original Claude session successfully. |
| By 23:39:23.159 / by 23:40:24.659 | Claude rebuild had a fresh secret; tester marked original Cursor rebuild failed. Cause unknown. |
| 23:43:25.039 / 23:53:59.857 | Relay queued natural deletion of the excluded Cursor and rebuilt Claude workspaces. |
| Nov 6 by 00:02:36.930 | Tester confirmed Claude's rebuilt reply; both naturally cleaned-up workspaces were absent. |
| Nov 6 00:05:30.242 / by 00:05:42.675 | After specific approval, original stopped Cursor workspace was deleted; no QA workspace remained. |

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

## Timeline: Q06-d (a6759911-a3d8-45dd-9032-af3973f7c89b)

Times are UTC on 2026-11-06. Browser times are observation bounds or "by" times, not exact completion times. Relay and Coder source times are rounded to milliseconds.

| UTC | Action or event |
| --- | --- |
| 01:19:22.015 / 01:19:54.163 | Set only Claude idle release to zero; restarted dedicated QA Relay with both pools healthy. |
| 01:21:01.37 to 01:21:08.27 | Submitted one benign Claude prompt; exact Enter time unknown. |
| 01:21:10.004 / 01:21:22.100 | Relay created the first workspace and handed off a runner; no turn completion confirmed. |
| 01:21:48.477 / 01:21:48.652 | Relay observed first runner done 2 and applied a retryable nack; exact exit time unknown. |
| By 01:21:58.600 | Browser showed a runner-start failure and automatic retry. |
| 01:22:15.004 / 01:22:27.159 | Automatic retry created and handed off a second workspace under zero idle. |
| 01:22:49.478 / 01:22:49.646 | Relay observed second runner done 2 and applied a second retryable nack. |
| 01:23:25.973 | Stopped dedicated QA Relay and restored the original 10m idle settings; no manual workspace delete. |
| 01:23:38.771 / 01:23:49.523 / by 01:24:09.110 | Baseline retry built a third workspace; the same Claude session replied normally. |
| 01:34:10.256 / 01:34:37.898 / by 01:35:12.802 | Baseline workspace stayed running, then exited cleanly and was deleted naturally. |
| 01:35:21.951 / 01:36:14.033 | No QA workspaces remained and both pools were healthy. Zero-idle retention and Cursor untested; exit-2 cause unknown. |
