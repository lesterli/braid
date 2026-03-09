---
name: daily-rss-digest
description: Enable and manage an OpenClaw-native daily summary from RSS feeds. Use when the user asks in Chinese or English to start, enable, inspect, disable, or retarget a daily summary, for example `开通每日摘要`, `开始每日摘要`, `查看摘要状态`, `关闭每日摘要`, or `帮我开通每日 RSS digest`. Default to the current chat when invoked inside Telegram, Slack, or another chat surface; default the feed bundle, timezone to Asia/Shanghai, and send time to 08:00 unless the user overrides them. Do not switch to shell-script setup, cron installation, or Miniflux deployment when this skill applies.
---

# Daily Summary

Turn one chat message into a recurring OpenClaw automation that sends one concise daily summary per day.

Treat OpenClaw as the runtime. Do not deploy Miniflux, Docker, custom adapters, or external schedulers for this skill.

## Product Contract

- Installing the skill does nothing by itself.
- Enablement must be explicit.
- When the request comes from a chat, deliver back to that same chat by default.
- Ask for a target only when there is no current chat context or the user explicitly wants a different destination.
- Keep defaults opinionated: built-in feeds, `Asia/Shanghai`, `08:00`, one concise daily summary per day.

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

- `enable`: `开通每日摘要` or `开始每日摘要`
- `status`: `查看摘要状态`
- `disable`: `关闭每日摘要`
- `adjust`: change target, time, timezone, or source set

Resolve intent before touching cron jobs.

## Enable Workflow

1. Infer the delivery target.
   - If the request comes from a chat, use that current chat by default.
   - If the user names another target, resolve it with OpenClaw's native channel discovery.
   - Ask a follow-up only when the target is missing or ambiguous.
2. Reuse or update an existing job for the same target instead of creating duplicates. Use the deterministic naming pattern from [references/openclaw-native.md](./references/openclaw-native.md).
3. Create or update one isolated daily cron job using OpenClaw's native scheduler.
4. The scheduled message must explicitly invoke `$daily-rss-digest` to generate the summary from the built-in feed bundle and deliver it back to the resolved target.
5. Send the enable confirmation first.
6. After the confirmation, prefer a real immediate run that sends one actual summary for today. Do not send only a dry-run confirmation when the host can run the job immediately.
7. Only if the host cannot run jobs immediately, keep the confirmation terse and state when the first automatic run will happen.

## Daily Run Workflow

1. Read [references/default-feeds.md](./references/default-feeds.md).
2. Fetch recent items directly from those RSS or Atom feeds with the host's available retrieval tools.
3. Focus on recent entries, deduplicate obvious repeats, and score for signal over noise.
4. Send `1-5` high-signal items. If nothing clears the bar, still send one short heartbeat summary saying there is no high-quality content today.
5. Keep the output optimized for chat delivery, not long-form reading.

## Management Workflow

- `status`: inspect the existing OpenClaw cron job and report whether the daily summary is enabled, plus target, schedule, timezone, and source set
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

For `enable`, reply with `4-5` short lines before the actual summary message is sent:

- enabled state
- resolved target
- send time and timezone
- source set
- management hint such as `查看状态 / 关闭`

For the other actions, reply with a short operational confirmation.

## References

- Read [references/defaults-and-ux.md](./references/defaults-and-ux.md) for the exact defaults and confirmation wording.
- Read [references/openclaw-native.md](./references/openclaw-native.md) for the native OpenClaw workflow, job naming, and cron command shape.
- Read [references/default-feeds.md](./references/default-feeds.md) for the built-in source set.
