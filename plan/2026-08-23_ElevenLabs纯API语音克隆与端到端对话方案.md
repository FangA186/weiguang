# [未完成] ElevenLabs 纯 API 语音克隆与端到端对话方案

> **状态**：未完成 (Pending)
> **创建时间**：2026-08-23
> **最后调整**：2026-08-23
> **完成时间**：
> **范围**：纯 API 架构设计；不表示功能已经接入或已通过运行验收。

## 1. 架构决策

按最新要求，运行时只保留轻量业务服务，语音识别、对话模型和语音合成全部调用云端 API。

推荐采用 ElevenLabs Speech Engine + 外部 LLM API：

```text
Vue 浏览器
  │ 通过服务端签发的短期 conversation token 建立语音会话
  ▼
ElevenLabs Speech Engine
  │ 负责实时 STT、VAD/turn-taking、打断处理和克隆音色 TTS
  ▼
项目 API 服务
  │ 负责用户、会话、记忆、额度、审计和工具权限
  ▼
外部 LLM API（OpenAI / Anthropic / Gemini / 火山方舟等）
```

ElevenLabs 官方 Speech Engine 的设计正是“ElevenLabs 负责 STT/TTS，业务服务负责 LLM”；每条 WebSocket 连接代表一个会话，SDK 负责 turn-taking 和 interruption。业务服务收到完整会话转写后调用任意外部 LLM，并把流式文本交还给 ElevenLabs 播放。[Speech Engine 原理](https://elevenlabs.io/docs/overview/capabilities/speech-engine)

因此，第一版只维护外部语音、ASR 和 LLM API adapter；前端保留现有播放、字幕、打断和会话 UI，具体供应商通过后端配置切换。

## 2. 两种纯 API 方案的取舍

### 2.1 推荐：Speech Engine + 自有 LLM API

适合微光当前产品，因为可以继续由项目控制：

- 角色设定和系统提示词；
- PostgreSQL/Redis 会话和长期记忆；
- LLM 供应商切换；
- 用户额度、审计和工具调用权限；
- Vue 自定义 UI。

ElevenLabs 服务端 SDK 的 `on_transcript` 回调会收到当前转写和完整会话历史；`send_response` 支持字符串、异步迭代器以及 OpenAI、Anthropic、Gemini 流。用户打断时 SDK 提供 abort signal，可以取消正在进行的 LLM API 请求。[Speech Engine 官方 Quickstart](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/speech-engine)

### 2.2 备选：ElevenAgents + Custom LLM API

如果希望 ElevenLabs 托管 Agent 会话、VAD、TTS、工具和部分状态，可以使用 Agent WebSocket：

```text
wss://api.elevenlabs.io/v1/convai/conversation?agent_id=<agent_id>
```

ElevenAgents 支持接入 OpenAI-compatible 的 `/v1/chat/completions` 或 `/v1/responses` 自定义 LLM 服务，并返回文本、音频、转写和 interruption 事件。[Custom LLM](https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm)、[Agent WebSocket](https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket)

但它会把更多会话编排和策略放到 ElevenLabs 控制台，后续自有记忆、权限和业务工具的边界更复杂。因此不作为第一版主方案。

## 3. SDK 调研与选型

### 3.1 官方 SDK 分层

ElevenLabs 当前把 SDK 分成三类，不能混用：

| 运行位置 | 官方包 | 用途 | 微光是否使用 |
|---|---|---|---|
| 服务端 Python | `elevenlabs` / `AsyncElevenLabs` | IVC/PVC、TTS、STT、Speech Engine | 可用；适合 FastAPI |
| 服务端 Node/TypeScript | `@elevenlabs/elevenlabs-js` / `ElevenLabsClient` | REST API、Speech Engine attach/server、LLM 流适配 | 推荐主服务使用 |
| 浏览器 JavaScript | `@elevenlabs/client` / `Conversation` | WebRTC 麦克风、conversation token、会话事件 | Vue 使用，不用 React Hook |
| React | `@elevenlabs/react` | `useConversation` 等 React 封装 | 不使用，项目是 Vue |

官方 Python SDK 提供 `ElevenLabs`/`AsyncElevenLabs`、`voices.ivc.create`、TTS streaming 和 Speech Engine `serve`；官方 Node SDK 提供 `ElevenLabsClient`、`voices.search`、TTS streaming，以及 Speech Engine `attach`/`SpeechEngine.Server`。[官方 Python SDK](https://github.com/elevenlabs/elevenlabs-python)、[官方 JavaScript SDK](https://github.com/elevenlabs/elevenlabs-js)

### 3.2 推荐技术组合

当前 Vue 项目建议采用：

```text
服务端：Node.js + TypeScript
  @elevenlabs/elevenlabs-js
  openai（或其他 LLM SDK）
  Fastify/Express + WebSocket

浏览器：Vue + TypeScript
  @elevenlabs/client
```

原因：官方 Node SDK 可以把 Speech Engine 直接 `attach` 到已有 Node HTTP server，并自动校验 `X-Elevenlabs-Speech-Engine-Authorization`；这样不需要再维护独立的 Python Speech Engine 进程。Speech Engine 服务端回调为 `onInit`、`onTranscript`、`onClose`、`onDisconnect`、`onError`，`onTranscript` 的 `signal` 用于取消被用户打断的 LLM 请求。[JavaScript Speech Engine SDK reference](https://elevenlabs.io/docs/eleven-api/resources/libraries/speech-engine/javascript-sdk-reference)

如果希望继续使用 Python，则使用 `AsyncElevenLabs().speech_engine.get(engine_id)` 后调用 `engine.serve(...)`，或在 ASGI 中使用 `engine.create_session()`。Python 方案可行，但 Node/TypeScript 更容易和现有 Vue 前端共享类型与会话事件。

### 3.3 服务端 SDK 骨架

```ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import OpenAI from "openai";

const elevenlabs = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY!,
});
const openai = new OpenAI({
  apiKey: process.env.LLM_API_KEY!,
  baseURL: process.env.LLM_BASE_URL,
});

await elevenlabs.speechEngine.attach(
  process.env.ELEVENLABS_ENGINE_ID!,
  httpServer,
  "/api/speech-engine/ws",
  {
    onInit(conversationId) {
      // 创建项目 conversation 映射
    },
    async onTranscript(transcript, signal, session) {
      const stream = await openai.responses.create({
        model: process.env.LLM_MODEL!,
        input: buildMessagesWithMemory(transcript),
        stream: true,
      }, { signal });
      await session.sendResponse(stream);
    },
    onClose(session) {
      // 异步写入会话和用量
    },
  },
);
```

生产代码必须把 `signal` 传给 LLM SDK，使用 `try/finally` 清理会话，并将数据库写入放入异步任务，不能阻塞 Speech Engine 音频通道。

### 3.4 Vue 浏览器骨架

```ts
import { Conversation } from "@elevenlabs/client";

let conversation: Awaited<ReturnType<typeof Conversation.startSession>> | null = null;

export async function startVoice() {
  await navigator.mediaDevices.getUserMedia({ audio: true });
  const token = await fetch("/api/speech/token", {
    credentials: "include",
  }).then((r) => r.text());

  conversation = await Conversation.startSession({
    conversationToken: token,
    onConnect: () => emit("connected"),
    onDisconnect: () => emit("disconnected"),
    onError: (error) => emit("error", error),
    onModeChange: ({ mode }) => emit("mode", mode),
  });
}

export async function stopVoice() {
  await conversation?.endSession();
  conversation = null;
}
```

`@elevenlabs/client` 是通用 JavaScript 浏览器 SDK；`@elevenlabs/react` 只是 React Hook 封装，不应直接安装到 Vue 页面。浏览器只能拿短期 token，不能拿 `ELEVENLABS_API_KEY`。[官方浏览器 SDK](https://elevenlabs.io/docs/eleven-agents/libraries/java-script)

### 3.5 IVC/TTS REST 调用

IVC 可以直接用 Node SDK：

```ts
const voice = await elevenlabs.voices.ivc.create({
  name: "Weiguang Companion",
  files: [sampleFile],
  description: "Authorized voice clone",
});
```

普通文本试听可以使用：

```ts
const audio = await elevenlabs.textToSpeech.convert(voiceId, {
  text: "你好，我是微光。",
  modelId: "eleven_flash_v2_5",
  outputFormat: "pcm_24000",
});
```

实时 Speech Engine 不需要在项目服务端自己处理 TTS 音频帧；只有独立的文本朗读、批量生成或 Speech Engine 不可用时，才使用 `textToSpeech.stream` 或 TTS WebSocket。

### 3.6 版本与安装

服务端：

```bash
npm install @elevenlabs/elevenlabs-js openai fastify ws dotenv
```

浏览器：

```bash
cd frontend
npm install @elevenlabs/client
```

Python 备选：

```bash
pip install elevenlabs openai python-dotenv
```

SDK 是生成式官方客户端，升级时必须锁定版本并执行 IVC、token、5 轮语音、打断和断线回归；不要直接用旧版 `conversational_ai` 方法名，Python SDK v2 已有方法重命名。[Python SDK v2 upgrade](https://github.com/elevenlabs/elevenlabs-python/wiki/v2-upgrade-guide)

## 4. 语音克隆 API

### 3.1 IVC 创建

```http
POST https://api.elevenlabs.io/v1/voices/add
Content-Type: multipart/form-data
xi-api-key: <server-side-secret>
```

字段：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `name` | 是 | 克隆音色名称 |
| `files[]` | 是 | 一个或多个音频文件 |
| `remove_background_noise` | 否 | 默认 false；无噪音时不要打开 |
| `description` | 否 | 音色说明 |
| `labels` | 否 | 语言、口音、性别、年龄等标签 |

响应为 `voice_id` 和 `requires_verification`。项目只保存 `voice_id` 和状态，不保存可导出的模型文件；ElevenLabs 的声音克隆留在账户中，通过 voice ID 使用。[Create IVC voice](https://elevenlabs.io/docs/api-reference/voices/ivc/create)

素材建议：1–2 分钟、单人、无背景噪声和混响，录音音量与语气保持一致。必须在产品侧记录“本人或权利人同意克隆”的确认，不允许把任意第三方声音直接做成公开音色。[IVC 素材与合规](https://elevenlabs.io/docs/eleven-creative/voices/voice-cloning/instant-voice-cloning)

### 3.2 PVC 生产音色

PVC 需要 Creator 及以上套餐，约 30–180 分钟高质量素材，包含说话人分离、授权验证、训练和状态轮询。推荐先用 IVC 完成端到端链路，再用相同测试集比较 PVC 的稳定性和情绪表现。[PVC API 流程](https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/professional-voice-cloning)

## 5. 纯 API 端到端会话

### 4.1 服务端组件

建议增加轻量 Node.js + TypeScript 服务。官方 Node SDK 可以把 Speech Engine `attach` 到已有 HTTP server，和当前 Vue + Go 项目更容易通过独立 API 进程解耦；若团队更偏 Python，可将同一回调模型迁移到 FastAPI/ASGI：

```text
api_server/
├── src/server.ts          # HTTP/WebSocket 启动与鉴权
├── src/speech-engine.ts   # ElevenLabs Speech Engine attach/callback
├── src/llm-provider.ts    # OpenAI-compatible / Anthropic / Gemini adapter
├── src/voice-clone.ts     # IVC/PVC API、授权和状态
├── src/conversation-store.ts # PostgreSQL 会话/消息
├── src/memory.ts          # 可选 Redis + PostgreSQL 记忆检索
└── src/quota.ts           # 字符、LLM token、会话并发额度
```

### 4.2 语音会话时序

```text
1. Vue -> GET /api/speech/token
2. API 服务校验登录用户、voice_id 和额度
3. API 服务调用 ElevenLabs 获取短期 WebRTC conversation token
4. Vue 使用 token 建立 Speech Engine 会话
5. ElevenLabs 将用户语音实时转写后回调项目 on_transcript
6. 项目拼接 system prompt + 记忆 + 当前会话历史
7. 项目调用外部 LLM API，使用流式输出
8. 项目 session.send_response(stream)
9. ElevenLabs 用克隆 voice_id 将文本流转换成语音并播放
10. 用户打断时 ElevenLabs 触发 abort，取消 LLM 请求和未完成回复
11. 会话结束后异步保存最终转写、LLM 文本和计费明细
```

官方 Quickstart 推荐服务端 token endpoint，把 API key 保留在服务端，并用 WebRTC 获得更好的音频质量。Vue 不是 React，不能直接照搬 Hook；应在 `frontend/src/lib/elevenSession.ts` 封装 JavaScript SDK 或底层 WebSocket/WebRTC 客户端，再由 `VoiceView.vue`/`ChatView.vue` 调用。[Token 与客户端流程](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/speech-engine)

### 4.3 文本聊天

文本聊天不必经过 Speech Engine：

```text
Vue -> POST /api/chat
API -> 记忆检索 + 外部 LLM API stream
API -> SSE/WebSocket chat.delta
Vue -> 文本展示
```

点击“朗读”时再调用：

```http
POST /v1/text-to-speech/{voice_id}/stream
```

或者使用独立 TTS WebSocket。实时语音主链路不建议自行拼接 STT + TTS，因为 Speech Engine 已经提供了 turn-taking 和 interruption。

## 6. LLM API 抽象

不在代码中绑定某一家模型，使用统一配置：

```text
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=<server-side-secret>
LLM_MODEL=<selected-model>
```

推荐定义：

```python
class LLMProvider(Protocol):
    async def stream_reply(
        self,
        messages: list[dict],
        signal: AbortSignal | None = None,
    ) -> AsyncIterator[str]: ...
```

首选模型 API 可以是 OpenAI Responses/Chat Completions；如果使用火山方舟、Anthropic 或 Gemini，则只实现 adapter，不改变语音层。Speech Engine 能直接消费 OpenAI、Anthropic、Gemini 流，也能消费普通异步文本迭代器。[官方支持的 LLM 接口](https://elevenlabs.io/docs/overview/capabilities/speech-engine)

## 7. 配置和密钥

```text
ELEVENLABS_API_KEY=<managed-secret>
ELEVENLABS_ENGINE_ID=<speech-engine-id>
ELEVENLABS_VOICE_ID=<ivc-or-pvc-voice-id>
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=<provider-base-url>
LLM_API_KEY=<managed-secret>
LLM_MODEL=<provider-model>
DATABASE_URL=<managed-secret>
REDIS_URL=<managed-secret>
```

禁止把 API key、token、数据库密码写入 `config.json`、Vue、日志、测试样例或方案文档。前端只获得短期 conversation token，不接触 ElevenLabs 和 LLM 长期密钥。

## 8. 数据模型

如果重新启用后端账户/数据库，新增迁移必须放在 `internal/auth/migrations/`，按序号递增。建议至少增加：

```text
voice_profiles
- id
- user_id
- provider                 # elevenlabs
- voice_id
- clone_type               # ivc / pvc
- status                   # pending / ready / failed / deleted
- authorization_confirmed_at
- created_at / updated_at

speech_conversations
- id
- user_id
- eleven_conversation_id
- voice_profile_id
- llm_provider / llm_model
- status
- started_at / ended_at

usage_events
- request_id               # unique, idempotent
- user_id
- conversation_id
- stt_seconds
- tts_characters
- llm_input_tokens / llm_output_tokens
- status / error_code
```

语音录音默认不持久化；只有用户明确启用历史或训练功能时才保存，并设置保留周期、删除接口和授权状态。

## 9. 价格与并发（2026-08-23 官方页面）

### 8.1 ElevenLabs TTS/STT

| 产品 | 单价 |
|---|---:|
| Flash / Turbo TTS | $0.05 / 1,000 字符 |
| v3 Conversational | $0.05 / 1,000 字符 |
| Multilingual v2 | $0.10 / 1,000 字符 |
| Scribe v2 STT | $0.22 / 小时 |
| Scribe v2 Realtime | $0.39 / 小时 |
| Speech Engine | $0.08 / 分钟；套餐外 burst 约 $0.16 / 分钟 |

纯 Speech Engine 方案主要按会话分钟计费；如果自行拆出 Realtime STT + TTS，则还要分别按输入小时和输出字符计费。[官方 API 定价](https://elevenlabs.io/pricing/api?price.platform=api)

### 8.2 Speech Engine 并发

官方价格表列出的 Speech Engine concurrent calls 为：Free 4、Starter 6、Creator 10、Pro 20、Scale 30、Business 40。这个并发模型与普通 TTS 并发不同，应按“同时活跃通话”压测，而不是按网页在线人数估算。

普通 TTS 模型并发仍为：Free Flash 4、Starter 6、Creator 10、Pro 20、Scale/Business 30；Multilingual v2/v3 则分别是 2、3、5、10、15、15。[模型并发限制](https://elevenlabs.io/docs/overview/models)

服务端应：

- 使用套餐上限 70%–80% 作为内部保护值；
- 每个用户最多一个活跃会话；
- 超限排队或友好拒绝，不做客户端无限重试；
- 记录 `conversation_id`、TTFB、会话时长、429、LLM 延迟和断线原因；
- 用户打断时取消 LLM 流，避免无意义 token 和 TTS 费用。

## 10. 实施顺序

### 阶段 A：API 账号和声音

1. 创建 ElevenLabs API key、Speech Engine 资源和 IVC voice。
2. 用固定中文句验证 cloned voice、中文语言、WebRTC 音频播放和授权状态。
3. 确认目标套餐的 Speech Engine 并发和实际区域延迟。

### 阶段 B：服务端 Speech Engine

1. 新建轻量 API 服务，提供 `/api/speech/token`。
2. 实现 `on_init`、`on_transcript`、`on_close`、`on_error`。
3. 接入外部 LLM 流，并把 abort signal 传入 LLM SDK。
4. 先使用固定 system prompt，不接记忆，完成 5 轮连续语音对话。

### 阶段 C：接入微光业务

1. 接入用户登录、voice profile、会话历史和异步计费记录。
2. 将长期记忆检索结果压缩后注入 LLM messages。
3. 接入文本聊天和手动 TTS，共用同一 voice profile。
4. 替换前端旧 WebSocket 状态机，保留光球状态、字幕、打断和播放 UI。

### 阶段 D：生产验收

1. 10 轮中文语音对话：转写准确性、声音一致性和中断延迟。
2. 10 个并发会话：首字延迟、首音延迟、丢音、断线和恢复。
3. 以 70%、100%、120% 套餐并发做压测，验证排队、降级和费用记录。
4. 验证 API key 不出现在浏览器、日志和异常响应中。

## 11. 当前明确边界

- 本轮只完成架构切换和方案文档更新；没有声称已经创建真实 voice、Speech Engine 或 LLM API 资源。
- 需要用户提供目标 LLM API 供应商/模型后，才能锁定 `LLM_BASE_URL`、模型上下文和成本估算。
- 如果目标是最快上线，使用 ElevenAgents + Custom LLM 会减少业务语音编排代码；如果要保留微光自己的记忆、权限和产品逻辑，使用 Speech Engine 更合适。

## 12. 官方资料

- [Speech Engine 概览](https://elevenlabs.io/docs/overview/capabilities/speech-engine)
- [Speech Engine Quickstart](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/speech-engine)
- [Realtime Speech-to-Text](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/server-side-streaming)
- [Create IVC voice](https://elevenlabs.io/docs/api-reference/voices/ivc/create)
- [Instant Voice Cloning](https://elevenlabs.io/docs/eleven-creative/voices/voice-cloning/instant-voice-cloning)
- [Professional Voice Cloning](https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/professional-voice-cloning)
- [Custom LLM](https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm)
- [Agent WebSocket](https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket)
- [API Pricing](https://elevenlabs.io/pricing/api?price.platform=api)
- [Models and concurrency](https://elevenlabs.io/docs/overview/models)
