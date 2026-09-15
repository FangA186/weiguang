# Weiguang Cloud API Voice Conversation

Weiguang now uses cloud APIs only. No local model weights, GPU workers, or model inference services are part of the target architecture.

```text
Vue 3 browser
  -> browser SpeechRecognition (no standalone ASR in phase 1)
  -> Python/FastAPI API service
  -> qwen3.5-flash
  -> qwen-audio-3.0-tts-flash
  -> browser audio playback
```

See the Chinese documentation for the active architecture and staged implementation plan:

- [`plan/2026-08-23_云API语音对话架构与分阶段实施方案.md`](plan/2026-08-23_云API语音对话架构与分阶段实施方案.md)
- [`plan/2026-08-23_Qwen云API语音对话方案.md`](plan/2026-08-23_Qwen云API语音对话方案.md)
- [`plan/2026-08-27_浏览器转写保留与套餐前端改造方案.md`](plan/2026-08-27_浏览器转写保留与套餐前端改造方案.md)
# weiguang
