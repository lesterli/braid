# Defaults And UX

Use these defaults unless the user explicitly overrides them.

## Default Product Behavior

- `delivery_target`: current chat when the request comes from a chat surface
- `source_set`: `default`
- `timezone`: `Asia/Shanghai`
- `send_time`: `08:00`
- `frequency`: once per day
- `delivery_shape`: one concise markdown digest message
- `empty_day_behavior`: still send one short digest saying there is no high-quality content today
- `quality_bar`: noise-averse; prefer silence in the item list, not low-signal filler
- `first_enable_behavior`: prefer running the newly created cron job immediately as the verification step

## User-Facing Commands

Prefer short, result-oriented phrasing:

- `开通每日摘要`
- `开始每日摘要`
- `开通每日摘要，发到 TG`
- `查看摘要状态`
- `暂停每日 RSS digest`
- `恢复每日 RSS digest`
- `关闭每日 RSS digest`

When the user is already in the target TG chat, prefer `开通每日摘要` and infer the destination from context.

## Confirmation Style

Use the user's language. When the user writes Chinese, prefer a compact confirmation like:

- `已开通每日 RSS digest`
- `推送目标：当前 TG 会话`
- `发送时间：每天 08:00 (Asia/Shanghai)`
- `信源：默认 feeds`
- `测试：已立即运行`
- `管理：查看状态 / 暂停 / 关闭`

## Failure Style

Keep failures concrete and actionable:

- No chat context and no explicit target: ask where to send it
- Ambiguous target: ask the user to pick one concrete channel
- Cron unavailable: explain that OpenClaw cron is not available in the current environment
- Test run unavailable: say the schedule is saved and the first automatic run will happen at the configured time
