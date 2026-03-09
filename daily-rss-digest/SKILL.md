---
name: daily-rss-digest
description: Enable and manage an OpenClaw-native daily RSS digest. Use when a user wants one curated RSS summary delivered every day to the current chat or another configured OpenClaw channel. Default to the current chat when invoked inside Telegram, Slack, or another chat surface; default the feed bundle, timezone to Asia/Shanghai, and send time to 08:00 unless the user overrides them.
---

# Daily RSS Digest

Turn one chat message into a recurring OpenClaw automation that sends one concise RSS digest per day.

Treat OpenClaw as the runtime. Do not deploy Miniflux, Docker, custom adapters, or external schedulers for this skill.

## Product Contract

- Installing the skill does nothing by itself.
- Enablement must be explicit.
- When the request comes from a chat, deliver back to that same chat by default.
- Ask for a target only when there is no current chat context or the user explicitly wants a different destination.
- Keep defaults opinionated: built-in feeds, `Asia/Shanghai`, `08:00`, one concise digest per day.

## Preconditions

- OpenClaw Gateway is already running.
- At least one chat channel is already configured in OpenClaw.
- The runtime can use OpenClaw's native channel and cron capabilities.

## Inputs

- Default `delivery_target`: the current chat or conversation route.
- Accept optional explicit `delivery_target` when the user says `发到 TG ...` or invokes the skill outside a chat.
- Accept optional overrides for `send_time`, `timezone`, and `source_set` only when the user asks.
- Do not ask for scoring policy or feed edits unless the user wants to tune them.

## Intent Model

Map user requests to one of these actions:

- `enable`: `帮我开通每日 RSS digest`
- `status`: `查看每日 RSS digest 状态`
- `pause`: `暂停每日 RSS digest`
- `resume`: `恢复每日 RSS digest`
- `disable`: `关闭每日 RSS digest`
- `adjust`: change target, time, timezone, or source set

Resolve intent before touching cron jobs.

## Enable Workflow

1. Infer the delivery target.
   - If the request comes from a chat, use that current chat by default.
   - If the user names another target, resolve it with OpenClaw's native channel discovery.
   - Ask a follow-up only when the target is missing or ambiguous.
2. Reuse or update an existing job for the same target instead of creating duplicates. Use the deterministic naming pattern from [references/openclaw-native.md](./references/openclaw-native.md).
3. Create or update one isolated daily cron job using OpenClaw's native scheduler.
4. The scheduled message must explicitly invoke `$daily-rss-digest` to generate the digest from the built-in feed bundle and deliver it back to the resolved target.
5. Prefer a real immediate run of the scheduled job as the test. If the host cannot run jobs immediately, send one short test confirmation to the same target.
6. Return a short confirmation with target, schedule, timezone, source set, and test result.

## Daily Run Workflow

1. Read [references/default-feeds.md](./references/default-feeds.md).
2. Fetch recent items directly from those RSS or Atom feeds with the host's available retrieval tools.
3. Focus on recent entries, deduplicate obvious repeats, and score for signal over noise.
4. Send `1-5` high-signal items. If nothing clears the bar, still send one short heartbeat digest saying there is no high-quality content today.
5. Keep the output optimized for chat delivery, not long-form reading.

## Management Workflow

- `status`: inspect the existing OpenClaw cron job and report enabled or paused state, target, schedule, timezone, and source set
- `pause`: disable the existing cron job if supported; otherwise remove it and say it was removed
- `resume`: recreate or re-enable the cron job using the saved defaults
- `disable`: remove the existing cron job and confirm that daily pushes have stopped
- `adjust`: update only the requested field and preserve the rest

## Working Rules

- Prefer OpenClaw native channels, cron jobs, and channel delivery over custom scripts or state files.
- Do not ask for `delivery_target` when the current chat is already a valid destination.
- Do not ask for `source_set`, `timezone`, or `send_time` unless the user overrides them.
- Keep the enable flow to one user message plus one confirmation whenever possible.
- If the host cannot create or inspect cron jobs in the current environment, say so plainly and stop.
- If a target cannot be resolved, explain the missing prerequisite instead of inventing a channel id.

## Response Shape

For `enable`, reply with `4-6` short lines:

- enabled state
- resolved target
- send time and timezone
- source set
- test result
- management hint such as `查看状态 / 暂停 / 关闭`

For the other actions, reply with a short operational confirmation.

## References

- Read [references/defaults-and-ux.md](./references/defaults-and-ux.md) for the exact defaults and confirmation wording.
- Read [references/openclaw-native.md](./references/openclaw-native.md) for the native OpenClaw workflow, job naming, and cron command shape.
- Read [references/default-feeds.md](./references/default-feeds.md) for the built-in source set.
