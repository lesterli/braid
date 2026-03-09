# OpenClaw Native Workflow

Use this reference when enabling or managing the digest inside OpenClaw.

## Core Principle

The skill should orchestrate OpenClaw's existing primitives:

- configured channels
- cron jobs
- delivery back to a channel

Do not create custom state files or external schedulers unless the host truly lacks these native capabilities.

## Delivery Target Resolution

1. If the user invoked the skill from a chat, prefer the current chat route as the delivery target.
2. If the user asked for a different destination, use OpenClaw's native channel discovery first.
3. Ask a follow-up only when the target is missing or ambiguous.

## Job Naming

Use one deterministic job name per destination:

```text
daily-rss-digest:<channel>:<target>
```

Examples:

```text
daily-rss-digest:telegram:123456789
daily-rss-digest:slack:channel-C123456
```

Reuse or update the same job on repeated `enable` requests instead of creating duplicates.

## Cron Shape

Create one isolated daily cron job whose message explicitly invokes this skill again.

Example shape:

```bash
openclaw cron add \
  --name "daily-rss-digest:telegram:123456789" \
  --cron "0 8 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --announce \
  --channel telegram \
  --to "123456789" \
  --message 'Use $daily-rss-digest to generate today'"'"'s digest from source_set=default. Read references/default-feeds.md, fetch recent entries directly from those feeds, and send one concise markdown digest. If nothing is worth reading today, output "今日无高质量内容".'
```

If OpenClaw exposes the same capability through a tool API instead of the CLI, use that native surface instead of shelling out.

## Status, Pause, Resume, Disable

- `status`: inspect the job matching the deterministic name
- `pause`: disable the existing job when the host supports pause; otherwise remove it
- `resume`: re-enable the paused job or recreate it with the same defaults
- `disable`: remove the existing job

## Verification

After `enable`, prefer one of these in order:

1. run the new cron job immediately
2. trigger the same isolated message once
3. send a short confirmation message and state when the first automatic run will happen
