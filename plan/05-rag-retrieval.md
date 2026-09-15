# 阶段 4：混合 RAG 快速检索

## 1. 业务目标

用户提问时只向模型提供最相关的历史，降低延迟和上下文污染，并让回答可以说明引用了哪些历史消息。

例如用户问“我之前是不是想过换工作”，系统应当召回“想离职”“公司没有发展”“准备简历”等语义相关内容，即使原文没有完全相同的关键词。

## 2. 技术选型

```text
PostgreSQL tsvector + GIN：关键词、时间、人名和专有名词
pgvector + HNSW：同义表达和语义相似内容
Redis：查询向量和检索结果缓存
```

默认 Embedding 使用 BGE-M3，向量维度 1024；模型名称和维度写入配置与索引版本，后续更换模型需要重建 Embedding。

## 3. `memory_chunks`

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE memory_chunks (
    id BIGSERIAL PRIMARY KEY,
    collection_id UUID NOT NULL REFERENCES memory_collections(id) ON DELETE CASCADE,
    collection_version INTEGER NOT NULL,
    chunk_type VARCHAR(32) NOT NULL DEFAULT 'conversation',
    content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    start_message_id BIGINT,
    end_message_id BIGINT,
    occurred_from TIMESTAMPTZ,
    occurred_to TIMESTAMPTZ,
    importance SMALLINT NOT NULL DEFAULT 0,
    confidence NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    source_quality NUMERIC(4,3) NOT NULL DEFAULT 1.0,
    search_vector TSVECTOR,
    embedding vector(1024),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

索引：

```sql
CREATE INDEX idx_memory_chunks_collection_version
ON memory_chunks(collection_id, collection_version, occurred_from DESC);

CREATE INDEX idx_memory_chunks_search
ON memory_chunks USING GIN(search_vector);

CREATE INDEX idx_memory_chunks_embedding
ON memory_chunks USING hnsw (embedding vector_cosine_ops);
```

## 4. Chunk 切分

不能只按固定字符数切分。使用组合规则：

- 6～12 条连续消息作为候选窗口；
- 时间间隔大于 30 分钟时优先断开；
- 主题显著变化时断开；
- 目标长度 400～800 中文字符；
- 前后重叠一个对话轮次；
- 图片 OCR/描述使用 `chunk_type=image`；
- 结构化事实使用 `chunk_type=fact`；
- 摘要使用 `chunk_type=summary`。

## 5. 在线检索流程

```text
当前问题
  ↓
轻量规范化
  ↓
识别人名、时间、主题、历史意图和图片意图
  ↓
全文检索 Top 50
  ↓
向量检索 Top 50
  ↓
按 user_id、collection_id、version 过滤
  ↓
混合排序
  ↓
MMR 去重
  ↓
相关性阈值过滤
  ↓
文本取 4～8 条，语音取 2～3 条
```

## 6. 混合评分

```text
final_score =
    0.40 × semantic_score
  + 0.25 × lexical_score
  + 0.15 × importance_score
  + 0.10 × recency_score
  + 0.10 × confidence_score
```

后续可通过离线评测调整权重，但第一版固定使用上述权重，避免运行时配置过多。

相关性低于 0.35 的结果不注入。用户明确询问历史时可将阈值降低到 0.30，但必须在回答中说明资料不足。

## 7. 去重与多样性

使用 MMR 保证结果不是同一段话的多个重复切片：

```text
MMR λ = 0.75
```

同一消息组最多保留两个 chunk，同一图片最多保留一个图片 chunk。

## 8. 时间和事实检索

- “上个月”“去年”转换为时间范围过滤；
- 精确日期优先使用 B-tree 时间索引；
- 长期事实先按 predicate/subject 查询，再与向量结果融合；
- 用户置顶事实无需相似度很高，但仍需与当前主题有关；
- `user_hidden=true` 的事实永远过滤。

## 9. 缓存设计

缓存键：

```text
memory:embedding:{model}:{query_hash}
memory:query:{collection_id}:{version}:{query_hash}
```

缓存值保存候选 ID、分数、引用来源和构建后的短上下文，不缓存用户无权访问的原始图片 URL。

collection version 变化后旧缓存自然失效。

## 10. 性能目标

| 环节 | 目标 |
|---|---:|
| 查询 Embedding | ≤150ms |
| 全文候选 | ≤50ms |
| 向量候选 | ≤150ms |
| 混合排序与去重 | ≤50ms |
| RAG 总耗时 | ≤400ms |
| Redis 命中 | ≤10ms |

图片 OCR、图片描述、历史 Embedding 和摘要都必须离线完成，不能放在实时语音请求中。

## 11. 可解释引用

Retriever 输出：

```json
{
  "context": "...",
  "references": [
    {
      "chunk_id": 123,
      "message_ids": [456, 457],
      "occurred_at": "2026-08-10T12:00:00+08:00",
      "score": 0.83,
      "reason": "semantic+importance"
    }
  ]
}
```

前端可以折叠展示“本次参考了 3 条记忆”。

## 12. 验收标准

- 精确关键词和同义表达都能召回。
- 普通寒暄不会注入无关历史。
- 两个记忆库互不污染。
- 高重要度事实优先于普通消息。
- 结果来源可追溯。
- 大数据量下 P95 检索延迟可控。
- 更换 Embedding 模型后通过版本重建，不混用不同向量空间。

