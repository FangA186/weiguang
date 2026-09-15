# 阶段 0：基础设施与统一数据标准

## 1. 业务目标

建立后续记忆功能依赖的统一入口、数据标准和异步任务机制。不同平台的聊天记录最终都转换成同一种内部格式，避免 RAG、摘要和语音接入重复适配。

## 2. 标准导入格式

第一版支持 JSON 和包含媒体目录的 ZIP。

```json
{
  "version": "weiguang-chat-export/v1",
  "title": "工作聊天记录",
  "memory_subject_id": "me",
  "participants": [
    { "id": "me", "name": "我" },
    { "id": "other", "name": "同事" }
  ],
  "messages": [
    {
      "id": "m_001",
      "sender_id": "other",
      "timestamp": "2026-08-20T10:00:00+08:00",
      "text": "你最近是不是准备换工作？",
      "attachments": [
        { "type": "image", "path": "media/image-001.jpg" }
      ]
    }
  ]
}
```

ZIP 结构：

```text
chat.zip
├── chat.json
└── media/
    ├── image-001.jpg
    └── image-002.png
```

后续微信、QQ、Telegram 等适配器只负责转换成该格式。

## 3. 异步任务状态

```text
uploaded
  ↓
validating
  ↓
processing
  ↓
cleaning
  ↓
indexing
  ↓
summarizing
  ↓
ready
```

异常状态：

- `partial_ready`：文字可用，但图片分析或摘要部分失败；
- `failed`：核心导入失败；
- `cancelled`：用户主动取消；
- `deleting`：正在清理数据库和文件。

## 4. 配置项

```text
MEMORY_STORAGE_DIR
MEMORY_MAX_IMPORT_BYTES=209715200
MEMORY_MAX_IMAGE_BYTES=20971520
MEMORY_MAX_ARCHIVE_FILES=2000
MEMORY_MAX_UNCOMPRESSED_BYTES=524288000
MEMORY_EMBEDDING_MODEL=BAAI/bge-m3
MEMORY_EMBEDDING_DIM=1024
MEMORY_RETRIEVAL_CACHE_TTL=120s
MEMORY_WORKER_CONCURRENCY=2
MEMORY_TEXT_CONTEXT_LIMIT=8192
MEMORY_VOICE_CONTEXT_LIMIT=4096
```

所有限制由后端配置，前端只展示后端返回的限制，不在两端维护两套数值。

## 5. API

```http
POST /api/memories/imports
GET /api/memories/imports/:id
GET /api/memories/imports/:id/status
POST /api/memories/imports/:id/retry
POST /api/memories/imports/:id/cancel
```

上传返回：

```json
{
  "import_id": "uuid",
  "collection_id": "uuid",
  "status": "uploaded",
  "progress": 0
}
```

## 6. Worker 设计

使用 PostgreSQL 保存最终任务状态，Redis 只作为队列和短期进度通道，防止 Redis 数据清空后任务彻底丢失。

Worker 每次领取任务时：

1. 数据库原子更新任务为 `processing`；
2. 写入 worker ID 和心跳时间；
3. 分阶段提交结果；
4. 超时任务可以重新领取；
5. 重试必须具备幂等性；
6. 成功后更新 collection 版本。

## 7. 安全边界

- ZIP 文件名必须进行 `filepath.Clean` 后校验目标仍在临时目录内。
- 不执行上传内容中的脚本、HTML 或可执行文件。
- 不信任文件扩展名和浏览器 MIME。
- 用户只允许查询自己的 import 和 collection。
- 临时目录使用随机 UUID，并在成功、失败或超时后清理。
- 日志中不记录完整聊天正文，只记录任务 ID、数量和错误摘要。

## 8. 验收标准

- JSON Schema 校验有效。
- ZIP 路径穿越和压缩炸弹会被拒绝。
- worker 重启后未完成任务可以恢复。
- 重复重试不会产生重复消息。
- Redis 故障不会导致数据库任务消失。
- 聊天 WebSocket 不会被导入任务阻塞。

## 9. 业务交付物

- 标准格式说明和示例文件；
- 上传限制说明；
- 导入状态和错误文案；
- 后续平台转换器接入说明；
- 用户隐私和数据删除说明。

