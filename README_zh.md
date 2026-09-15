# 微光云 API 语音对话

当前项目采用纯云 API 架构，不在本地部署模型或 GPU 推理服务。

## 当前默认链路

```text
Vue 3 浏览器
  → Python/FastAPI API 服务
  → 浏览器 SpeechRecognition
  → 阿里云百炼北京 qwen3.5-flash
  → 阿里云百炼 qwen-audio-3.0-tts-flash
  → 浏览器音频播放
```

- 文本、图片和视频交给阿里云百炼北京 `qwen3.5-flash`。
- 麦克风由浏览器 `SpeechRecognition` 转成文本后进入 LLM；第一阶段不接入 Qwen、MiMo 或其他独立 ASR。
- 用户参考音频通过阿里云百炼 Qwen-Audio-TTS API 创建克隆音色。
- PostgreSQL 保存用户、会话、消息、音色和用量；Redis 负责队列、限流和幂等；对象存储保存上传文件。
- 首期采用轮次语音对话，不承诺全双工打断式实时交互。

## 开发入口

- 前端：`frontend/`（Vue 3 + TypeScript + Vite）
- 后端 API：`backend/`（FastAPI，已包含百炼 LLM/TTS 和 OSS 签名上传骨架）
- 架构与实施计划：[`plan/2026-08-23_云API语音对话架构与分阶段实施方案.md`](plan/2026-08-23_云API语音对话架构与分阶段实施方案.md)
- 详细模型、价格和并发方案：[`plan/2026-08-23_Qwen云API语音对话方案.md`](plan/2026-08-23_Qwen云API语音对话方案.md)

## 本地开发准备

依赖已经安装后，推荐直接在项目根目录执行：

```bash
./scripts/start-weiguang.zsh
```

脚本会启动缺失的 PostgreSQL、FastAPI 和 Vite；已运行的服务会跳过。后台日志位于 `.run-logs/`。

1. 阿里云百炼账号、API Key 和本地环境变量已完成；仍需确认 Workspace ID、北京 Base URL 和模型配额。第一阶段不需要 MiMo/Qwen ASR API Key。
2. 准备 PostgreSQL、Redis 和阿里云 OSS（华北 2/北京、标准-LRS 私有 Bucket）。当前 Bucket 为 `weiguang-dev-20260823`，OSS RAM 凭据只放在本地 `.env`。
3. 安装前端依赖并运行：

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

后端当前已建立 Python/FastAPI 骨架，并使用 OpenAI Python SDK 调用百炼 LLM；Qwen-Audio-TTS 使用百炼官方 HTTP 接口。启动前激活虚拟环境并执行：

```bash
source .venv/bin/activate
uvicorn backend.app:app --reload --port 8080
```

百炼官方环境变量名为 `DASHSCOPE_API_KEY`，请在启动服务的同一个终端确认它可见；项目也兼容 `QWEN_API_KEY`。

检查配置：

```bash
curl http://127.0.0.1:8080/api/health
```

文本调用：

```bash
curl -X POST http://127.0.0.1:8080/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"你好"}]}'
```

TTS 调用（`voice` 使用百炼声音复刻接口返回的 voice ID；暂时也可以省略，使用系统音色）：

```bash
curl -X POST http://127.0.0.1:8080/api/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"你好，这是语音测试。","voice":"your_voice_id","instruction":"用温柔的语气，语速稍慢"}'
```

生成音频参考文件的 OSS 临时上传地址：

```bash
curl -X POST http://127.0.0.1:8080/api/uploads/presign \
  -H 'Content-Type: application/json' \
  -d '{"filename":"reference.wav","content_type":"audio/wav"}'
```

浏览器或客户端拿到 `upload_url` 后，使用返回的 `headers` 直接 `PUT` 文件；不要把 OSS 长期 AccessKey 下发到浏览器。

音频上传完成后，使用返回的 `object_key` 创建 Qwen-Audio-TTS 克隆音色：

```bash
curl -X POST http://127.0.0.1:8080/api/voice-clones \
  -H 'Content-Type: application/json' \
  -d '{"object_key":"voice-references/上传接口返回的文件名","prefix":"weiguang","language_hints":["zh"]}'
```

当前接口为同步最小实现，成功后返回 `voice_id`；生产版仍需补充后台任务、状态持久化、幂等和音频时长/采样率校验。

OSS 签名配置自检（不会打印签名 URL 或密钥）：

```bash
python scripts/smoke_oss.py
```

真实调用测试（会产生 API 费用）：

```bash
python scripts/smoke_bailian.py
```

声音克隆任务、数据库迁移和前端套餐/用量改造按方案中的后续阶段逐步实现；独立 ASR 暂不接入。
