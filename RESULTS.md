# Agent-Relay QA, November 5-10, 2026

Latest result per tested variant: **9 pass, 2 fail, 2 blocked**. The full run records hold timestamps and earlier attempts.

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
| Q11-F1a | Delayed a Claude QA start build for eight minutes under five- and two-minute spawn budgets. | Each request had only attempt 0; its deadline canceled the build and deleted the sole workspace. No redelivery was observed, so the race remains blocked. | A genuine redelivery reuses the workspace without a stale nack and observes its own deadline. |
| Q11-F1b | Instrumented only the first QA watcher with one extra minute while advertising a five-minute Claude lease. | Anthropic re-offered attempt 1 after lease expiry; Relay rebuilt the same workspace without an old-attempt nack, then timed out attempt 1 at its fresh deadline. | A real re-offer supersedes the first watcher, retains one workspace and gets its own full deadline. |
| Q11-F1c | Ran the terminal-redelivery feature commit with QA-only first-watcher grace and one eight-minute Claude start delay. | A genuine attempt 1 arrived after the five-minute lease, received an applied non-retryable nack, and the sole START build was canceled and deleted without a second START. | Terminally fail a re-offer that finds an unfinished START, then clean up one workspace; leave the production first-attempt deadline unchanged. |

Public Git includes reviewed screenshots only for Q02-build, Q02-startup, Q06-c and Q11-F1a. Q02-death used `/bin/false`, not SIGKILL. The Q06-d runner failure cause is unverified. [View the results](https://emyrk.github.io/throw-away-qa/).

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

## Timeline: Q11-F1a (36d233dd-a375-430c-9efe-bcd7244062d3)

Times are UTC on 2026-11-10. The specified 5m/8m trial and a separately labeled exploratory 2m/8m trial both lacked an observed Claude redelivery. Browser and workspace-listing times are observation bounds, not exact provider or deletion times. The full sourced event records and redacted evidence are in the run directory.

| UTC | Action or event |
| --- | --- |
| 17:18:40 / 17:18:56.296587 / 17:18:57.143444 | The disposable 60s-delay preflight entered the delay, cancellation was accepted and its interrupted Terraform job finished failed with `canceled_at`. |
| By 17:22:17.510059 / by 17:36:21.649548497 | Smoke workspace absent after authorized cleanup; tester later accepted terminal failed plus `canceled_at`. |
| 17:36:58.68564575 / by 17:37:05.992031 | Clean main `43a5136` QA Relay started with private 5m/480s debug overlay; readiness 200 and both QA pool-health gauges one. |
| 17:42:44.391480368 / 17:42:45.057004 / 17:42:52.510 | Verified attempt 0 had `iat=17:42:44Z`, `exp=17:47:44Z`; one QA workspace started build 1 and entered the 480s delay. |
| 17:47:44.127244905 / 17:47:44.24196181 | Original deadline fired while build 1 ran; Relay logged an applied non-retryable attempt-0 nack. No attempt 1 observed. |
| 17:47:44.345549 / 17:47:44.98416 / by 17:47:58.941968 | Build 1 received `canceled_at`, settled terminal failed, then the sole QA workspace was absent at a subsequent status poll. |
| By 17:50:05.235 / by 17:54:53.639905 | Claude UI showed runner-start failure after one attempt; private verified-claims logs still showed no redelivery more than 11m after issue. |
| By 17:55:38.163034 / 17:57:12.022298257 / 17:57:19.271 | Separate exploratory 2m dispatch overlay started; new attempt 0 had `iat=17:57:11Z`, `exp=17:59:11Z`, and its sole start build entered the 480s delay. |
| 17:59:11.157899371 / 17:59:11.302383818 | Short deadline fired; Relay logged an applied non-retryable attempt-0 nack, with no attempt 1 observed. |
| 17:59:11.402199 / 17:59:11.979845 / by 17:59:27.577878 | Build 1 received `canceled_at`, settled terminal failed, and the only exploratory QA workspace was absent at a later poll. |
| By 18:00:40.334 / by 18:01:23.463495 | Claude UI showed failure after one attempt; no redelivery appeared in private verified-claims logs through the later check. |
| 18:02:37.238282 / by 18:12:56.231 / by 18:14:56.398 | Original safe QA config restored byte-for-byte. Latest-main Relay remained ready with both QA pools healthy; a later Coder listing found zero `steven` QA template workspaces. |

## Timeline: Q11-F1b (1508b9e1-7407-494c-a595-f3346f71a6a8)

Times are UTC on 2026-11-10. This is an **instrumented QA-only** run, not a clean-main pass for F1a. [The exact `git diff --binary`, losslessly encoded in the JSON `git_diff` field](runs/2026-11-10/emyrk/1508b9e1-7407-494c-a595-f3346f71a6a8/evidence/qa-source-git-diff.json) is part of the run report; its SHA-256 is `9e4ee75beee7d9307d7f5cfa58d0b8422a3c078020d765b9e82c29734c7536b3`. Binary provenance, field-restricted logs and 234 status polls are under the same run. Browser times are observations, not exact provider transition times. Three private UI screenshots are attached to the tester chat, not to this public repository.

| UTC | Action or event |
| --- | --- |
| 18:47:10.088232 / by 18:49:42.170503 | Pinned clean base `43a5136` plus reviewed QA-only source diff; built and launched binary SHA-256 `07fc4420...d930d`. Relay advertised `expected_spawn_seconds=300`; both QA pools healthy. |
| 18:51:11.86978508 / 18:51:12.253807 | Verified attempt 0 had `iat=18:51:11Z`, `exp=18:56:11Z`; one QA workspace started build 1. |
| By 18:51:15.443 | One benign new Claude prompt sent in Steven-Testing. This is an upper observation bound, not an exact Enter time; no manual retry or Cursor request. |
| 18:51:18.938 | Build 1 entered the 480s delay before any runner existed. |
| By 18:56:13.540451 / 18:56:16.832435381 | Build 1 still ran after the first lease expired; Anthropic re-offered the same session as attempt 1, with fresh `iat=18:56:16Z`, `exp=19:01:16Z`. |
| 18:56:17.040342882 / 18:56:17.181202 / 18:56:17.918334 | Relay reconciled the existing QA workspace; build 1 received `canceled_at` and settled terminal failed. |
| 18:56:20.249467 / 18:56:27.026 | Coder created build 2 on the **same** workspace with attempt marker 1; it entered the second 480s delay. |
| By 18:57:28.809722 / by 18:58:05.143 | Build 2 survived the first watcher's instrumented 18:57:11 deadline without an old-attempt nack or delete. Claude UI showed waiting with one failed attempt. |
| 19:01:16.081961783 / 19:01:16.221130728 | Attempt-1 watcher reached its own deadline and Relay logged one applied non-retryable attempt-1 nack. No attempt-0 nack was logged. |
| 19:01:16.279219 / 19:01:16.781838 / 19:01:19.615726563 | Build 2 received `canceled_at`, settled terminal failed, and Relay queued the sole workspace for natural deletion. |
| By 19:01:31.633591 / by 19:02:10.824 | Zero QA template workspaces at the next poll; Claude UI showed Failed after 2 attempts. Exact deletion and browser failure instants are unknown. |
| 19:02:46.908289 / by 19:04:18.159318 | Restored the original safe config and unmodified clean-main QA binary byte-for-byte. Relay ready, both QA pool-health gauges one, zero `steven` QA template workspaces. |

## Timeline: Q11-F1c (cf0050f9-e3d2-4daa-a33c-a1900c744228)

Times are UTC on 2026-11-10. This pass covers feature commit `a472aacc603230c625ab714418fc005d77324dcc` **plus QA-only first-watcher grace**, not a byte-identical production binary. [The exact test-only `git diff --binary` is losslessly stored as a JSON `git_diff` field](runs/2026-11-10/emyrk/cf0050f9-e3d2-4daa-a33c-a1900c744228/evidence/qa-source-git-diff.json), SHA-256 `11b700a919e9b130c6ffb94f7f2f61ec430742a540762977dbbd2bd98a5f8a1b`. The launched executable's SHA-256 was `4c295a1aa66329a393adbfacb3686213cb87cb75a4441627c85461195d46582b`. Redacted logs, 143 status polls and binary provenance are in the run. Browser times are observation bounds; private screenshots are attached to the tester chat, not published here.

| UTC | Action or event |
| --- | --- |
| By 21:53:54.704980077 / by 21:54:13.454850 | Instrumented feature-branch Relay advertised `expected_spawn_seconds=300` with only attempt 0's local watcher extended 60s; both QA pools healthy, zero QA workspaces. |
| 21:54:51.562 to 21:54:58.841 / 21:54:59.898046590 | Sent one benign prompt in new Steven-Testing conversation within the observed Enter bounds. Verified attempt 0 had `iat=21:54:59Z`, `exp=21:59:59Z`. |
| 21:55:00.272024 / 21:55:07.297 | Coder created START build 1 on one QA workspace and entered the 480s delay before any runner. |
| By 22:00:03.961102 / 22:00:04.885238640 | Original START still ran after attempt-0 expiry, without a local nack. Anthropic re-offered the same session as attempt 1 with fresh `iat=22:00:04Z`, `exp=22:05:04Z`. |
| 22:00:05.079208970 / 22:00:05.228257528 | Feature branch detected the unfinished START and logged an applied non-retryable nack of current attempt 1. No attempt-0 nack or second START build occurred. |
| 22:00:05.323950 / 22:00:05.796797 | Coder marked START build 1 `canceled_at`, then its interrupted Terraform job settled terminal failed. |
| 22:00:08.560537 / 22:00:21.348458 / by 22:00:25.211489 | Build 2 was **DELETE**, not another START; it succeeded and the sole QA workspace was absent at the later poll. |
| By 22:00:56.911 | Claude UI showed Failed after 2 attempts. The exact failure transition is unknown; private screenshot was reviewed. |
| 22:01:52.747996 / 22:02:19 / by 22:02:56.547046 | Original safe config and clean-main QA launcher restored byte-for-byte. QA case wording corrected to distinguish DELETE from a second START; both pools healthy and zero QA workspaces at final check. |
