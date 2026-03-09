# Defaults And UX

Use these defaults unless the user explicitly overrides them.

## Default Product Behavior

- `delivery_target`: current chat when the request comes from a chat surface
- `source_set`: `default`
- `timezone`: `Asia/Shanghai`
- `send_time`: `08:00`
- `frequency`: once per day
- `delivery_shape`: one concise markdown 摘要消息
- `empty_day_behavior`: still send one short summary saying `今日无高质量内容`
- `quality_bar`: noise-averse; prefer silence in the item list, not low-signal filler
- `first_enable_behavior`: prefer running the newly created cron job immediately and sending one actual summary for today
- `enable_message_order`: confirmation first, summary second

## User-Facing Commands

Prefer short, result-oriented phrasing:

- `开通每日摘要`
- `开始每日摘要`
- `开通每日摘要，发到 TG`
- `查看摘要状态`
- `关闭每日摘要`

When the user is already in the target TG chat, prefer `开通每日摘要` and infer the destination from context.

## Confirmation Style

Use the user's language. When the user writes Chinese, prefer a compact confirmation like:

- `已开通每日摘要`
- `推送目标：当前 TG 会话`
- `发送时间：每天 08:00 (Asia/Shanghai)`
- `信源：默认信源`
- `管理：查看状态 / 关闭`

When immediate run is available, the confirmation should be followed by one separate summary message. Do not mention `立即运行` in the confirmation itself.

## Failure Style

Keep failures concrete and actionable:

- No chat context and no explicit target: ask where to send it
- Ambiguous target: ask the user to pick one concrete channel
- Cron unavailable: explain that OpenClaw cron is not available in the current environment
- Immediate run unavailable: say the schedule is saved and the first automatic run will happen at the configured time
