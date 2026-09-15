# 阶段 6：图片理解与 MiMo-V2.5 多模态扩展

## 1. 业务目标

让聊天记录中的图片不仅可以保存和预览，还能在相关问题中提供信息。

分两个层次实施：

1. OCR 和视觉描述参与 RAG；
2. MiMo-V2.5 在必要时直接读取原图。

## 2. 第一层：OCR 与图片描述

导入图片时生成：

```text
OCR：会议时间为 2026-08-20，项目进度 80%。
视觉描述：这是一张项目进度表截图，展示了后端任务完成情况。
```

这些内容作为 `chunk_type=image` 写入 `memory_chunks`，并保存对应 `asset_id` 和 `message_id`。即使当前模型不支持视觉输入，也可以通过文字检索使用图片中的信息。

OCR 与视觉描述都必须携带：

- 来源图片 ID；
- 来源消息 ID；
- 发生时间；
- 分析模型和版本；
- 置信度；
- 分析状态。

## 3. 第二层：MiMo-V2.5 直接视觉输入

MiMo-V2.5 官方支持图片、视频、音频和文本输入，输出文本；图片支持公网 URL 或 Base64 传入。当前多模态理解统一通过云端模型 API 实现。[MiMo-V2.5 模型说明](https://mimo.mi.com/models/zh-CN/mimo-v2.5)、[MiMo 图片理解说明](https://mimo.mi.com/docs/zh-CN/usage-guide/multimodal-understanding/image-understanding)

Qwen3 TTS 只接收文本，因此 TTS 服务本身不能理解图片。需要新增 MiMo 多模态 provider adapter，由 MiMo 生成文本回答后再交给 Qwen3 TTS 朗读，不能把图片直接传给 TTS。

## 4. 多模态消息结构

当前纯文本消息应升级为 provider 可适配的内容部分：

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "请看看这张截图里的项目进度"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "/api/memories/collection-id/assets/asset-id"
      }
    }
  ]
}
```

内部类型建议：

```go
type ContentPart struct {
    Type     string `json:"type"`
    Text     string `json:"text,omitempty"`
    ImageURL string `json:"image_url,omitempty"`
    AssetID  string `json:"-"`
}

type ProviderMessage struct {
    Role    string        `json:"role"`
    Content []ContentPart `json:"content"`
}
```

纯文本 provider adapter 将内容合并成字符串，多模态 adapter 保留结构化内容。

## 5. 图片进入上下文的条件

只有以下条件同时满足时才附带原图：

- 用户问题明确涉及图片、照片或截图；
- RAG 命中该图片或相关消息；
- OCR/描述不足以回答；
- 当前 provider 声明 `vision_enabled=true`；
- 当前上下文和显存预算允许。

每轮限制：

- 最多 1～2 张图片；
- 长边缩放到 768～1024；
- 总大小不超过 5～10MB；
- 同一图片只发送一次；
- 不加载整个记忆库的图片历史。

## 6. 图片检索策略

用户说“之前那张进度截图”时：

1. 根据“进度截图”检索图片 OCR/描述 chunk；
2. 使用时间、来源人和对话主题过滤；
3. 返回图片缩略图和来源消息；
4. 如果用户只问图片中文字，优先 OCR；
5. 如果问画面关系或整体含义，再使用视觉模型读取原图。

## 7. 鉴权读取

```http
GET /api/memories/:collectionId/assets/:assetId
GET /api/memories/:collectionId/assets/:assetId/thumbnail
```

每次读取验证：

- 当前登录用户；
- collection 归属；
- asset 属于 collection；
- collection 未删除；
- storage key 没有路径穿越；
- 返回正确的 `Content-Type` 和缓存策略。

模型服务读取私有图片时，优先由 Go 后端读取并转发字节或使用短期签名 URL，不能给远程模型永久公开地址。

## 8. 降级策略

```text
视觉模型可用 → 按需附带原图
视觉模型不可用 → 使用 OCR + 图片描述
OCR 不可用 → 使用图片描述
全部不可用 → 明确提示当前图片尚未完成分析
```

不允许在降级时根据文件名猜测图片内容。

## 9. 语音询问图片

```text
用户说“之前那张图写了什么”
  ↓
ASR 得到文本
  ↓
RAG 找到图片
  ↓
OCR/视觉模型生成文本答案
  ↓
页面展示文本
  ↓
TTS 朗读同一文本
```

图片本身不进入 TTS，TTS 仍只处理最终文本。

## 10. 验收标准

- 图片 OCR 能被关键词检索。
- 图片描述能被语义检索。
- 用户能查看引用图片和来源消息。
- 多模态 provider 可以直接读取命中的原图。
- 普通问题不会加载无关图片。
- 不支持视觉时能够稳定降级。
- 语音询问图片时页面正文和朗读一致。
- 用户无法访问其他用户的图片。

## 11. 风险

| 风险 | 处理 |
|---|---|
| 图片 token/显存消耗高 | 每轮限制数量、尺寸和触发条件 |
| OCR 与视觉结果冲突 | 保留两种来源和置信度，必要时直接看原图 |
| 新 API 链路尚未实现多模态上传 adapter | 增加鉴权上传、对象存储/Base64 转换和 MiMo provider adapter |
| 私有图片泄露 | 后端转发或短期签名 URL |
| 全双工模式延迟增加 | 第一版仍采用 ASR→文本模型→TTS 两阶段链路 |
