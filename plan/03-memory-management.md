# 阶段 2：多记忆库管理与生命周期

## 1. 业务目标

用户可以把不同来源的数据分开管理，并在文本或语音聊天前选择当前使用的记忆库。

典型记忆库：

```text
工作经历
家庭聊天
项目资料
学习记录
恋爱聊天
```

## 2. 核心业务规则

1. 每次上传默认创建一个独立记忆库。
2. 一个聊天会话绑定一个记忆库。
3. 会话中途切换必须停止旧回复并重连。
4. 记忆库删除后不可继续检索。
5. 记忆库重建使用新版本，完成后原子切换。
6. 用户在微光中产生的新聊天先属于会话历史，不自动写回上传记忆库。
7. 新聊天只有在用户主动“记住”或满足确认流程后才写入长期事实。

## 3. `memory_collections`

关键字段：

```text
id
user_id
name
description
memory_subject_id
status
version
message_count
image_count
dropped_video_count
summary
created_at
updated_at
```

建议索引：

```sql
CREATE INDEX idx_memory_collections_user_updated
ON memory_collections(user_id, updated_at DESC);

CREATE INDEX idx_memory_collections_user_status
ON memory_collections(user_id, status);
```

## 4. `conversation_sessions`

记录：

```text
session_id
user_id
provider
memory_collection_id
memory_version
rolling_summary
summary_token_count
status
created_at
updated_at
```

绑定版本而不只绑定 collection ID，可以保证一次会话期间检索结果稳定。新索引版本完成后，新会话使用新版本，已有会话可以继续旧版本直到结束。

## 5. API

```http
GET /api/memories
POST /api/memories
GET /api/memories/:id
PATCH /api/memories/:id
DELETE /api/memories/:id
POST /api/memories/:id/rebuild
GET /api/memories/:id/facts
PATCH /api/memories/:id/facts/:factId
DELETE /api/memories/:id/facts/:factId
POST /api/memories/:id/facts/:factId/pin
POST /api/memories/:id/facts/:factId/hide
```

## 6. 前端流程

聊天页和全屏语音页显示：

```text
记忆：无
记忆：工作聊天
记忆：项目聊天
```

切换流程：

```text
用户选择新记忆库
  ↓
停止当前回答
  ↓
停止 TTS 和音频播放
  ↓
关闭旧 WebSocket
  ↓
使用新 collection 建立会话
  ↓
页面显示新记忆库和版本
```

## 7. 删除流程

删除前展示：名称、消息数、图片数和创建时间。确认后：

1. 状态设置为 `deleting`；
2. 禁止新会话绑定；
3. 删除图片文件；
4. 数据库外键级联删除消息、chunks、facts 和 summaries；
5. 清除 Redis 缓存；
6. 写审计日志，不记录聊天正文。

## 8. 业务验收

- 两份数据能建立两个独立记忆库。
- 选择 A 后只召回 A，选择 B 后只召回 B。
- 当前页面始终显示当前记忆库。
- 重建、失败、删除状态清晰。
- 长期事实可以置顶、隐藏、修订和删除。

## 9. 风险

| 风险 | 处理 |
|---|---|
| 记忆库事实冲突 | 第一版一个会话只绑定一个记忆库 |
| 重建读到半成品 | version + 原子切换 |
| 用户误删 | 二次确认并展示影响范围 |
| 老会话使用旧数据 | 会话绑定 memory_version |
| 删除时仍有会话 | 禁止新会话，已有会话收到失效事件并结束 |

