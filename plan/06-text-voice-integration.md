# 阶段 5：文本与语音统一记忆接入

## 1. 业务目标

文本聊天和语音聊天使用相同的长期记忆和检索规则，但根据模型上下文能力采用不同预算。同一个问题通过文字或语音提出时，应得到一致的核心事实。

## 2. 文本流程

```text
text.query
  ↓
校验 session、用户和 memory_collection_id
  ↓
MemoryRetriever.BuildContext
  ↓
组装 system + facts + summary + chunks + recent_history
  ↓
Qwen 流式生成
  ↓
保存用户消息和 assistant 最终文本
  ↓
异步更新会话摘要
```

## 3. 语音流程

```text
麦克风音频
  ↓
FunASR final 文本
  ↓
MemoryRetriever.BuildContext（语音预算）
  ↓
Qwen 生成最终文本
  ↓
chat.delta 展示文本
  ↓
按完整句子交给 TTS
  ↓
浏览器播放同一正文
```

TTS 不理解长期历史，也不允许重新组织回答正文。它只接收已经展示在页面上的句子和隐藏的语气 instruction。

## 4. WebSocket 协议扩展

启动：

```json
{
  "type": "session.start",
  "memory_collection_id": "collection-uuid",
  "speaker": "voice-id",
  "character_manifest": "角色设定"
}
```

返回：

```json
{
  "type": "session.started",
  "memory_collection_id": "collection-uuid",
  "memory_version": 3,
  "provider": "open_source"
}
```

引用事件：

```json
{
  "type": "memory.references",
  "items": [
    {
      "chunk_id": 123,
      "message_id": 456,
      "summary": "用户曾提到准备换工作",
      "occurred_at": "2026-08-10T12:00:00+08:00"
    }
  ]
}
```

## 5. 后端模块边界

建议新增：

```text
internal/memory/
├── model.go
├── store.go
├── import.go
├── cleaner.go
├── assets.go
├── facts.go
├── summary.go
├── retriever.go
├── context.go
└── worker.go
```

Provider 只依赖接口：

```go
type MemoryRetriever interface {
    BuildContext(ctx context.Context, input QueryInput) (*MemoryContext, error)
}
```

`QueryInput` 至少包含：

```text
UserID
SessionID
CollectionID
CollectionVersion
Provider
Mode(text/voice)
Query
RecentMessages
TokenBudget
```

## 6. 一致性约束

- 页面正文和 TTS 使用同一个 `assistant_message_id`。
- TTS 语气标签作为隐藏控制信息，不进入页面正文。
- 只有完整生成且未被打断的回答进入会话历史。
- 用户打断时取消检索、LLM、TTS、音频队列和浏览器播放。
- 文本生成成功但 TTS 失败时保留文本，并明确显示语音失败。
- 不允许 TTS 失败后播放上一条缓存音频。

## 7. 语音延迟控制

- 会话开始时加载摘要和高重要度事实快照。
- 每轮仅查询 2～3 个 chunk。
- 查询 Embedding 和检索结果使用 Redis 缓存。
- 回答按句号、问号、感叹号分句。
- 第一完整句生成后立即开始 TTS。
- 普通回答限制 50～150 字。
- 图片分析、Embedding 和摘要不能在线执行。

## 8. Provider 差异

### 开源模式

每轮可以由 Go 后端重新构建 messages，因此可以逐轮注入 RAG 结果。

### 字节实时模式

优先在 `session.start` 注入压缩记忆快照。若上游支持 `dialog_context` 或主动上下文接口，再逐轮/批量注入有限历史；否则切换记忆库必须重连。

不应假设两个 provider 拥有相同的上下文能力，`MemoryContext` 需要由 provider adapter 转换。

## 9. 前端改造

- 聊天页和语音页共用记忆库 store；
- 建立连接前取得当前 `memory_collection_id`；
- 连接中切换时提示并重连；
- 回复下方可以展开引用；
- 明确显示“无记忆”状态；
- 断线重连后展示恢复的会话和记忆库。

## 10. 验收标准

- 文本和语音询问同一历史问题时核心事实一致。
- TTS 朗读正文与页面文字一致。
- 语音打断后不会继续播放旧回复。
- 断线后能够恢复会话摘要。
- 切换记忆库后旧记忆不再生效。
- RAG 故障时降级为当前会话短期历史，不导致整个聊天不可用。

