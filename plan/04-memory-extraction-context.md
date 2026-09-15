# 阶段 3：长期事实、摘要与上下文管理

## 1. 业务目标

系统要区分“值得长期记住”“只有问到时才检索”和“不应主动使用”的内容，避免把所有聊天都当成长期事实。

## 2. 记忆等级

| 等级 | 内容 | 默认处理 |
|---|---|---|
| P0 | 用户明确说“请记住” | 强制长期保留，除非用户删除 |
| P1 | 身份、稳定偏好、长期目标 | 写入长期事实 |
| P2 | 承诺、持续项目、重要关系 | 高优先级检索 |
| P3 | 普通事件和日常状态 | 保留为 chunks，按需检索 |
| P4 | 寒暄、重复消息、模型套话 | 不主动注入上下文 |

## 3. 重要度字段

```text
importance：该内容是否值得长期使用，0～100
confidence：系统判断是否可靠，0～1
recency：相对当前时间的新鲜度
valid_from：事实开始生效时间
valid_to：事实结束生效时间
user_pinned：用户强制保留
user_hidden：用户禁止在对话中使用
```

重要度和相似度不能混成一个值。某条事实可能非常重要但与当前问题无关，也可能与问题很相似但只是低价值寒暄。

## 4. 事实提取流程

```text
清洗消息
  ↓
按时间和主题形成上下文窗口
  ↓
规则识别明确表达
  ↓
批量模型提取候选事实
  ↓
去重、合并和冲突检测
  ↓
计算重要度和置信度
  ↓
写入 memory_facts
```

规则可以直接提高重要度：

- 出现“请记住”“以后不要忘记”；
- 明确主语为用户；
- 明确长期时间范围；
- 出现未来截止日期和承诺；
- 多次重复确认同一偏好；
- 用户手动置顶。

降低重要度：

- “哈哈”“好的”“嗯嗯”；
- 单次天气、饮食、即时状态；
- 模型自己生成的客套内容；
- 没有证据的猜测；
- 与已有内容完全重复。

## 5. `memory_facts`

```sql
CREATE TABLE memory_facts (
    id BIGSERIAL PRIMARY KEY,
    collection_id UUID NOT NULL REFERENCES memory_collections(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_value TEXT NOT NULL,
    value_type VARCHAR(32) NOT NULL DEFAULT 'text',
    importance SMALLINT NOT NULL DEFAULT 0,
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    source_message_ids BIGINT[] NOT NULL DEFAULT '{}',
    user_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    user_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## 6. 冲突事实处理

例如：

```text
2025：用户准备考研
2026：用户已经开始工作
```

不直接覆盖旧事实，而是维护有效期：

```text
准备考研：valid_to = 2026-01-01
已经工作：valid_from = 2026-01-02
```

优先顺序：用户主动修订 > 时间更新 > 置信度 > 来源数量。仍无法判断时，回答中说明历史资料存在冲突。

## 7. 摘要层次

### 全局摘要

描述记忆库中的主要人物、长期关系、重要目标和主题。

### 时间摘要

按月、季度或明显事件阶段生成摘要，便于查询“去年”“上个月”。

### 主题摘要

例如工作、学习、家庭、健康、项目等。

### 会话滚动摘要

记录用户在微光当前会话中的进展，用于长会话压缩和断线恢复。

摘要必须保存来源范围和版本，不能成为无法追溯的孤立结论。

## 8. 文本上下文预算

```text
系统规则：600 token
长期事实：800 token
会话摘要：1,000 token
RAG 片段：1,500 token
近期历史：2,500 token
当前问题：完整保留
回答空间：至少 800～1,500 token
```

## 9. 语音上下文预算

```text
角色规则：300 token
长期事实：400 token
会话摘要：500 token
RAG 片段：400～600 token
近期历史：最近 2～4 轮、最多 700 token
当前 ASR 文本：完整保留
```

普通语音回答限制为 50～150 字，复杂回答最多 300～500 字并分段播放。

## 10. 上下文裁剪顺序

1. 保留当前问题。
2. 保留用户置顶事实。
3. 保留与当前问题相关的高置信事实。
4. 保留高分 RAG 片段。
5. 删除重复片段。
6. 删除最早且低重要度的短期历史。
7. 压缩摘要。
8. 不允许从字符串头部直接暴力截断导致语义残缺。

## 11. 摘要触发

满足任一条件异步更新摘要：

- 文本会话超过 8 轮；
- 语音会话超过 4 轮；
- 当前历史估算超过 4,000 token；
- WebSocket 正常关闭；
- 用户主动保存会话。

摘要失败不阻塞当前回答，继续使用上一个摘要和最近历史。

## 12. 验收标准

- 用户明确要求记住的内容可稳定召回。
- 寒暄不会生成大量长期事实。
- 事实有来源消息并可追溯。
- 新旧事实冲突不会被静默覆盖。
- 语音模式上下文小于文本模式。
- 10 万条历史不会直接进入 Prompt。
- 长会话重连后可以恢复摘要和当前记忆库。

