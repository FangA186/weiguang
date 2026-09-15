# 微光云 API 语音架构交接文档

> 目标架构版本：2026-08-27（浏览器转写 + 纯 API LLM/TTS，轮次链路已接入）  
> 当前状态：百炼 LLM/TTS 与 OSS 适配已完成真实 smoke 验证；前端聊天和全屏语音已切换到 FastAPI `/api/chat-and-tts/stream`。账户、HttpOnly 会话、角色设置、聊天记录、遗留故事寄语、套餐、兑换码、用量流水和音色操作恢复账本均以 PostgreSQL 为权威数据源。六类套餐权益已接入原子预留/确认/释放，续费周期已分离，Pro 多音色和购买前失败关闭已实现；全局仍为 `shadow`，1个内部账号处于 hard 灰度。链动小铺 Plus / Pro 商品已发布并完成真实小额支付/发码/兑换/退款/人工回滚，微信/支付宝直连暂缓，API自动对账仍未接入。内部监控API和成本告警脚本已上线；长期记忆后移。独立 ASR 暂不接入；真实声音克隆、浏览器长回复端到端验收和并发压测仍未完成。  
> 安全原则：本文不保存 API Key、Token、Cookie、数据库密码或可直接登录远端的凭据。

## 1. 最新决策

当前目标运行拓扑为（阿里云百炼使用华北 2/北京地域）：

```text
Vue 3 浏览器
    ├── SpeechRecognition：当前语音转文本方案，暂不接独立 ASR
    │
    │ HTTPS（只提交转写文本与业务数据）
    ▼
Python/FastAPI API 服务
    ├── 阿里云百炼 qwen3.5-flash：文本、图片、视频理解与回答
    ├── 阿里云百炼 qwen-audio-3.0-tts-flash：用户克隆音色 TTS
    ├── PostgreSQL：用户、会话、消息、音色、用量
    ├── Redis：队列、并发信号量、限流、幂等
    └── 阿里云 OSS（华北 2/北京、标准-LRS）：参考音频和附件
```

首期采用轮次语音对话：浏览器语音转写 → LLM → TTS → 网页播放，不承诺全双工打断式实时交互。

## 2. 代码边界

旧的模型运行代码、部署资源和旧测试目录已经从工作目录清理。Python/FastAPI 的第一版 `backend/` API 骨架已经建立：LLM 使用 OpenAI Python SDK 接入百炼北京兼容接口，TTS 使用百炼 Qwen-Audio HTTP 接口，OSS 使用 `oss2` 生成私有 Bucket 的临时签名上传 URL；真实 LLM/TTS 已验证，克隆 API 的前端上传链路已接入。独立 ASR 已决定暂不接入；真实声音克隆和浏览器端到端验收仍待完成。

不得把旧的模型协议端口、GPU Worker 或本地模型启动方式报告为新生产服务。当前有效方案见：

- `plan/2026-08-27_浏览器转写保留与套餐前端改造方案.md`
- `plan/2026-08-27_产品套餐与商业化计费方案.md`
- `plan/2026-08-29_链动小铺套餐兑换码售卖接入方案.md`
- `plan/2026-08-23_Qwen云API语音对话方案.md`（ASR 部分仅作历史研究）
- `plan/2026-08-23_云API语音对话架构与分阶段实施方案.md`（架构历史基线）
- `plan/README.md`

## 3. 目标服务模块

```text
backend/
├── app.py                 # FastAPI 启动、鉴权和健康检查
├── app_data_store.py      # PostgreSQL 用户、会话、设置、聊天、故事与旧数据迁移
├── billing_store.py       # 套餐、原子用量、兑换码批次、订阅授权与周期切换
├── api/                   # 会话、上传、音色、用量接口
├── providers/             # qwen_llm、qwen_tts、oss；当前不增加 ASR provider
├── services/              # 对话编排、音色、配额、多模态路由
├── jobs/                  # 音色创建、清理、账单汇总
└── repositories/          # PostgreSQL、Redis、对象存储
```

前端复用现有聊天、录音、字幕和播放 UI；聊天和语音均通过 HTTP API 轮次调用，不再依赖旧 provider 协议 adapter、MiniCPM Gateway 或本地 AudioWorklet。

## 4. 关键流程

### 4.0 OSS 上传（当前已实现）

1. `POST /api/uploads/presign` 校验音频 MIME 类型并生成 `voice-references/` 对象键。
2. 浏览器使用返回的临时 URL 和 `Content-Type` 直接 PUT 到私有 OSS Bucket。
3. `POST /api/voice-clones` 为已上传对象生成临时 GET URL，并调用百炼 `voice-enrollment` 创建 Qwen-Audio-TTS 音色。
4. 服务端不向浏览器下发长期 AccessKey；签名 URL 默认 15 分钟有效，最长 1 小时。

### 4.1 音色克隆

1. 服务端生成对象存储短时上传地址；浏览器上传用户授权参考音频。
2. 服务端校验 MIME、时长、采样率、文件哈希和授权声明。
3. 后端在 Provider 调用前写入 `voice_clone_operations`；调用 Qwen 声音克隆 API 后保存 `voice_id`、目标 TTS 模型、OSS 对象键和参考音频元数据。远端成功、本地失败会留下可抢占租约的持久恢复状态。
4. 设置页读取 `/api/voice-clones` 展示全部 active 音色；Pro 可保留、选择和删除 3 个音色。删除先登记操作、再删远端、最后停用本地记录；远端已删而本地失败时只重试本地停用，不重复删除远端。
5. 未完成补偿的远端孤儿持续占用套餐音色槽位；请求前和列表读取会有界 reconcile，`FOR UPDATE SKIP LOCKED` 防止多进程重复恢复。

### 4.2 语音轮次

1. 浏览器使用 SpeechRecognition 将一轮语音转成文本。
2. 语音轮次把角色设定、历史消息和本轮文本提交到 `POST /api/chat-and-tts/stream`；纯文本轮次提交到 `POST /api/chat/stream`，不触发 TTS。
3. qwen3.5-flash 通过 OpenAI-compatible streaming 增量生成文本；服务端按完整句子排队调用 qwen-audio-3.0-tts-flash 的 SSE 流式合成。
4. FastAPI SSE 同时下发 `text.delta` 和 `audio.delta`；浏览器用单一 AudioContext 时间线立即播放 PCM 分片，并在结束事件后保留完整音频 URL。
5. 第一阶段保留浏览器转写；只有达到重新评估条件后，才另行比较 Qwen/MiMo ASR。

### 4.3 账户与业务数据持久化

1. 登录/注册由 `/api/auth/*` 写入 PostgreSQL，浏览器使用 `HttpOnly + SameSite=Lax` 会话 Cookie，不保存账户数据或用户 ID 到 Local Storage。
2. 角色设置使用 `/api/voice-settings`；聊天历史使用 `/api/chat-history`；数据库是唯一权威数据源。
3. `/api/migrations/local-storage` 仅允许本机执行：先事务写入并回读用户、设置、聊天和故事，成功后前端才删除五个 `weiguang*` 遗留 Key。
4. `Cache Storage` 仅保存可回源的 TTS WAV 缓存，不作为业务数据源。

### 4.4 链动小铺套餐兑换码

1. 受限运维脚本预生成 Plus / Pro 卡密，数据库只保存兑换码哈希，原码仅一次性上传链动小铺库存。
2. 链动小铺负责外部支付与卡密交付，不直接修改微光套餐。
3. 登录用户通过 `POST /api/billing/redeem` 兑换；服务端在同一事务中锁码、写入授权流水并更新 `user_subscriptions`。
4. 同档套餐可顺延 30 天；有效付费套餐跨档兑换首期拒绝且不消耗码。
5. `GET /api/billing/channels` 只暴露已通过 HTTPS 和 `ldxp.cn` 域名校验的商品链接；未配置时套餐页保持“即将开放”。
6. `/pricing` 先进入 `/purchase/{plus|pro}` 独立购买页；该页根据数据库订阅状态展示同档顺延或跨档拦截，再跳链动小铺。
7. 支付后用户从链动订单复制卡密回微光兑换；成功页只显示卡密掩码、套餐和到期日，不保存或回显完整卡密。
8. 购买按钮只有在用户已登录、套餐摘要成功回读且无跨档冲突时才开放；后端兑换仍做最终跨档校验。
9. 链动小铺 API、回调、退款和自动履约未核验，首期只允许兑换码模式。
10. 2026-08-31 已用真实小额订单验证人工闭环：支付/发码/兑换后，退款订单由商家端判定买家胜诉；微光仅撤销对应未来 grant 并将卡密标记 revoked，当前周期与已用量不回滚。

### 4.5 套餐额度与安全边界

1. `GET /api/plans` 是免费、Plus、Pro 权益单一来源；前端只负责展示。
2. 所有 LLM、TTS、多模态、声音复刻和截图提取入口先写 `reserved`，成功写 `completed`，失败/取消写 `released`；TTL 未知结果进入 terminal `expired`，同一请求 ID 不会再次触发 Provider，迟到结果仍可确认。
3. 图片/视频统计覆盖提交给 Provider 的所有 messages；流式文字和 PCM 已下发即确认，PCM 按预留字节上限裁剪。
4. 用户 ID 只来自 HttpOnly Session；伪造 Header 无效。生产环境 Cookie 强制 Secure，写请求校验可信 Origin，数据库不可用时 hard 模式失败关闭。
5. 全局仍为 `shadow`；`BILLING_HARD_USER_IDS` 已用于内部账号定点 hard 灰度，其他账号继续显示“影子统计中”。连续 7 天账单核对与全量 hard 前不得对外宣传硬额度已全面生效。

### 4.6 生产监控与独立运营管理后台 (`frontend-admin/`)

1. **架构完全解耦**：运营管理后台与用户端客户端彻底分离，作为独立的 Vue 3 + TypeScript 工程（`frontend-admin/`）；本地开发运行在 `:5174`，线上构建以 `/admin/` 为公共路径并由宿主 Nginx 静态托管，避免普通用户构建产物泄露管理员路由、组件与内部运维接口。
2. **唯一管理员鉴权与门禁**：
   - 管理后台拥有专属登录页（`/login`）；
   - 通过 `settings.billing_hard_user_ids` 作为白名单判定管理员权限，`/api/auth/me` 回传 `is_admin: true/false`；
   - 所有 `/api/admin/*` 路由均受 `require_admin_user_id` 保护，非白名单严格 403。
3. **生产监控** (`/monitoring`)：
   - 24h / 7d 动态时间桶（小时/天）；
   - 4大核心指标：预估成本（含部分估算标记）、请求总数、失败/取消率、悬挂预留（超过 TTL 自动超时告警）；
   - 原生 SVG 趋势曲线（成本渐变面积与请求双线对比）；
   - 6类用量进度条与各模型 Provider 消耗拆分表；
   - 30 秒自适应刷新与 Page Visibility API 智能休眠/唤醒。
4. **Token 与成本分析** (`/costs`)：用户级输入/输出 Token、TTS 计费字符、产品语音秒数及遥测完整性（完整/部分/无遥测）。
5. **权益交易流水** (`/transactions`)：卡密兑换账本，实付标注“渠道未同步”，标明套餐标价仅供参考。
6. **用户管理与对话审查** (`/users`, `/users/:userId`)：
   - 支持搜索、账号状态/套餐筛选、资料与内部运维备注更新；
   - 禁用账号确认并原子销毁全部活跃 Session，Provider 入口直接拒绝；
   - 用户对话会话流与消息正文审查（气泡角色、语音时长、附件元数据，不自动加载私有媒体）。
7. **访问入口**：线上入口为同源 `/admin/`，本地开发入口为 `http://localhost:5174/admin/`；后端仍以白名单进行最终权限判断。
8. **Session 恢复**：管理端只允许路由守卫调用 `auth.ensureReady()`；不要在 `App.vue` 再次初始化，否则并发调用会在 profile 尚未回填时误跳登录页。

### 4.7 Ex-Skill 五层人格蒸馏与多角色记忆工坊

1. **AgentSkills 开放标准**：基于 [perkfly/ex-skill](https://github.com/perkfly/ex-skill) 架构，将用户自定义角色人设升级为数据驱动的五层结构化 Persona（L0 硬规则 ~ L4 冲突应对）与 Memories 共同事实库。
2. **权威存储**：PostgreSQL `personas`、`persona_versions`、`persona_corrections` 三表作为唯一事实源，彻底杜绝 Local Storage。
3. **两阶段 AI 蒸馏与 OCR 零表单全自动提炼**：
   - 后端端点 `POST /api/personas/distill-from-import` 支持从聊天截图 OCR 结果全自动推导五层人设（L0~L4）与共同回忆，自动识别非用户侧发言人昵称并由 LLM 自主推断角色名称，自动激活新角色并无缝打开角色工坊；
   - 彻底免除用户手动填写角色姓名、MBTI、依恋类型、性格标签等繁琐问卷的负担；角色工坊顶部展示金色引导横幅，方便用户随时随地按需微调与保存。
4. **运行时 Prompt 动态编译**：`backend/prompt_compiler.py` 在发起对话前将五层人设、回忆与活跃纠偏组装为统一的 System Instruction；实时双工语音与文本对话无额外阻塞。
5. **对话动态调教/纠偏**：用户在聊天界面随时点击“🎯”或指出违和之处，`correction_handler.py` 自动提炼为高优先级强约束规则并即时生效。
6. **聊天历史私有附件动态刷新签名**：在 `GET /api/chat-history` 与管理员消息审查接口中引入 `_enrich_messages_attachments`，对存储在消息中的私有 OSS 对象键动态签发有效下载链接，彻底解决 403 Forbidden (`Request has expired`) 裂图缺陷。
7. **前端交互**：用户端提供独立 `PersonaWorkshopDialog.vue`（角色工坊）、`DistillWizardDialog.vue`（蒸馏向导）、`CorrectionDialog.vue`（快捷调教），支持角色自由切换与音色绑定。

### 4.8 参考音频在线可视化裁剪工具 (Audio Trimmer)

后续同日更新：语音自动模式已由固定1.0改为六类场景映射0.96–1.04及自然语言语气指令，整轮锁定首段场景；不接受模型随意数值或自由direction。手动设置优先，自动模式忽略旧自由声音instruction和scenario，保留音色特征。短回答尽量同段合成；旧回放仍按原计划。mock回归通过，真实听感待验收。

2026-09-12语音聊天默认策略调整：`/api/chat-and-tts/stream`的adaptive_voice分支不再注入角色compiled_prompt，保留历史及音色绑定；planning_prompt使用日常口语规则及1到3句语意段。自动语速固定1.0、不加情绪/拟声标签；手动声音设置保留。旧speech turn回放仍使用原计划。仅本地更新，听感待验收。

1. **纯前端零服务端负荷架构**：基于 Web Audio API（`AudioContext.decodeAudioData`）在浏览器本地直接解析音频并利用 `<canvas>` 动态渲染发光波形图（Waveform）。
2. **百炼官方时长对齐**：对齐百炼声音复刻官方推荐 10–20 秒最佳规范（允许 5–30 秒），提供双端滑块、±0.5s 微调控制与合规状态徽标。
3. **选区试听与无损导出**：支持 `AudioBufferSourceNode` 选区播放与动态游标；裁剪后纯客户端将 PCM 数据编码封装为标准 16-bit PCM RIFF WAV 格式，保留原始录音副本并支持一键还原。
4. **裁剪与净化状态一致性**：裁剪选区在确认前不替换当前文件；此时隐藏旧DeepFilterNet试听，净化按钮保持可见并提示先确认裁剪但不可点击，同时禁止创建音色。确认裁剪会清空旧上传/净化对象，用户需按新WAV重新生成净化试听；取消则继续使用原音状态。

## 5. 配置项

会话编辑交互更新：列表铅笔展开原位标题输入和头像入口，头像选择立即保存，标题单独保存；消息头像不再可点击，API保持不变。

2026-09-14：新增PATCH /api/chat-history/conversations/{id}修改标题或会话头像，SQL按用户/会话归属校验。头像复用账号私有图片上传签名，不调用账号头像确认接口；使用现有chat_conversations列。前端点击AI头像或列表铅笔操作，本地实现，未发布。

2026-09-14最新覆盖：语音adaptive已恢复NDJSON与PlanDecoder，planning_prompt(structured=True)用于语音，文字聊天为普通正文。模型scene重新参与整轮情绪选择，手动/原始模式规则保留；未发布。

2026-09-14最新覆盖：已恢复统一日常聊天system提示，planning_prompt不再要求NDJSON/scene，语音运行流程无PlanDecoder，按普通文本分句；旧角色人设未恢复。自动场景沿用chat回退，音频回放计划保留，未发布。

2026-09-14最新试用策略：聊天四入口不向LLM发送system/developer提示词，planning_prompt注入已注释；语音普通文本分句，保留内部音频计划及TTS参数。无LLM scene选择，自动声音回退chat基调。仅本地，未发布。

最新覆盖：CosyVoice恢复instruction（100单位上限）和独立pitch，voice_style增加pitch/use_defaults。恢复默认按钮设置use_defaults=true，保存后公共Provider忽略所有声音参数仅发text/voice/format；编辑退出。新语音计划保存pitch/volume/use_defaults，直接朗读同样适配。自定义与原始两模式真实PCM验证通过，未发布。

最新覆盖：CosyVoice已按用户要求重新开放rate/volume，专用页面直接编辑；voice_style JSON存储volume（默认50，0–100）与rate（默认1，0.5–2）。合成/语音计划传两项，instruction仍不发送，采样率默认22050Hz。Qwen旧设置保留。

最新覆盖（原始试听）：CosyVoice仅发送text、voice及传输format，省略所有声音调节参数，流式PCM默认22050Hz并同步播放/存储/计费。前端保留设置但对CosyVoice无效；Qwen不变。

最新覆盖：按用户要求CosyVoice-v3.5-plus已完全停发instruction，包括直接朗读、流式聊天和旧计划重新合成；rate与sample_rate仍传。Qwen指令保持原行为；CosyVoice情绪、音色描述与方言指令暂不生效。详见2026-09-13接入方案参数表。

2026-09-13：新建音色默认cosyvoice-v3.5-plus，已有音色按数据库target_model使用原模型，默认系统音色仍用Qwen。CosyVoice合成前query_voice状态须OK，处理中或拒绝返回409。HTTP/SSE复用现有Provider，CosyVoice去除Qwen方括号标签，拟声不支持；声音指令与rate保留。成本按模型分开估算。仅本地mock及构建验收，尚无真实CosyVoice音色试听，未发布。

```text
QWEN_API_KEY=<managed-secret>
QWEN_BASE_URL=https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
QWEN_LLM_MODEL=qwen3.5-flash
QWEN_TTS_MODEL=qwen-audio-3.0-tts-flash
QWEN_TTS_FALLBACK_MODEL=qwen3-tts-vc-2026-01-22
DATABASE_URL=<managed-secret>
REDIS_URL=<managed-secret>
OSS_REGION=cn-beijing
OSS_BUCKET / OSS_PUBLIC_ENDPOINT / OSS_INTERNAL_ENDPOINT
OSS_ACCESS_KEY / OSS_SECRET_KEY
LDXP_PLUS_PRODUCT_URL=<optional-https-ldxp-product-url>
LDXP_PRO_PRODUCT_URL=<optional-https-ldxp-product-url>
APP_ENV=production
PUBLIC_BASE_URL=https://<production-origin>
TRUSTED_ORIGINS=https://<production-origin>
COOKIE_SECURE=true
BILLING_ENFORCEMENT_MODE=shadow
BILLING_HARD_USER_IDS=<comma-separated-stable-user-ids>
```

浏览器只能收到业务会话令牌，不能收到 Qwen 或对象存储长期密钥。日志不得打印完整凭据、原始音频或未脱敏供应商响应。

本地服务统一启动命令：

```text
./scripts/start-weiguang.zsh
```

脚本通过 macOS `launchctl submit` 启动缺失的 FastAPI 后端、用户端前端（`:5173`）与管理端前端（`:5174`），并复用现有 PostgreSQL（`:55433`）；服务已运行时不会重复启动。日志位于 `.run-logs/`。

## 6. 验收顺序

1. 阿里云百炼账号、服务和 API Key 已由用户完成开通并配置到本地环境；仍需登记 Workspace ID、北京地域模型可用性、价格和并发配额；第一阶段不需要开通独立 ASR。
2. 部署 FastAPI、PostgreSQL、Redis 和对象存储，完成健康检查。
3. 已安装 `.venv`、OpenAI Python SDK、FastAPI 和 `oss2`；百炼 LLM/TTS 与 OSS 签名 URL 已通过真实 smoke 验证。
4. 已建立同步声音克隆接口骨架，前端已接入“申请签名 PUT→OSS 直传→创建音色”；仍需真实音频验收、后台任务、voice/model 绑定校验和持久化。
5. 完成文本、图片、视频、浏览器转写与克隆 TTS 轮次。
6. 做 1/5/10/25 路压测、429/断线/取消/成本告警测试。
7. 通过 3–5 名内部用户灰度后再扩大到 50 名用户。

完成真实 API 验收和压测前，不得把方案文档标题改为 `[已完成]`，也不得宣称纯 API 已上线。

## 2026-09-04 TTS 参数修复

### 2026-09-05 零配置用户流程

普通用户不再进入角色工坊、Prompt编辑和纠偏分类。OCR确认调用distill-from-import并携带当前persona_id，服务端校验归属后覆盖该角色的自动提炼结果；不传persona_id仍兼容创建新角色。声音画像由OCR批次自动进入蒸馏，克隆音色成功后前端自动保存为当前音色。后台结构化字段与管理能力保留，不得重新暴露为普通用户必填设置。

### 2026-09-05 上线整改基线

范围确认：OCR长图不支持，不做自动切片；上传页保持禁止长图并提示裁成多张。用户确认链动小铺真实付款、续期和退款已完成验收，后续不再列为上线阻断项；API自动对账仍是独立增强项。

数据库迁移统一走`backend/migration_runner.py`的版本表与事务级advisory lock，各Store不得自行扫描执行SQL。生产API使用数据库限流；Compose内API不发布宿主端口，Nginx覆盖X-Forwarded-For为remote_addr，Uvicorn才可启用proxy headers。取消流关闭由guarded_events/Provider各自容错，避免并发aclose异常。

生产入口为Dockerfile与deploy/compose.production.yaml；复制环境示例和Nginx示例、配置真实域名/证书后方可启动。备份/恢复脚本要求显式DATABASE_URL，恢复额外要求CONFIRM_RESTORE=YES。生产隐藏docs/openapi并返回安全头。

### 2026-09-11 ECS 首阶段公网部署

当前已部署到华东1杭州ECS，公网为 `http://47.114.50.170/`。此阶段按用户要求暂不启用HTTPS：`APP_ENV=staging`、`COOKIE_SECURE=false`、Origin限定该IP。Docker Compose的API只绑定宿主回环`127.0.0.1:8080`，PostgreSQL不发布端口；宿主Nginx的`/etc/nginx/default.d/weiguang.conf`代理全部请求。API和数据库均healthy，公网健康/首页/套餐接口已通过，浏览器3D圆环与登录弹窗正常。正式运营前必须改回production、Secure Cookie和HTTPS。服务器无法稳定访问Docker Hub；部署更新应本地构建amd64运行镜像（前端先本地build，使用`deploy/Dockerfile.prebuilt`），加密传输并以`--no-build`启动，不能依赖服务器在线构建。

首次部署不能只执行结构迁移：链动小铺已售库存依赖 `redemption_batches/redemption_codes` 中的哈希。2026-09-11 已迁入两个有效批次的未兑换哈希，并完成首张线上 Plus 兑换；原始卡密不入迁移文件或普通日志。Nginx 需要区分 `/api/` 和 SPA 页面路由，页面 404 回退 `/index.html`，API 错误码不得被回退页面吞掉。

运营管理后台已独立部署到 `http://47.114.50.170/admin/`：静态目录为 `/var/www/weiguang-admin/admin`，Nginx 的 `/admin/` 使用独立 `try_files` 回退。线上唯一已注册账号是唯一管理员；生产环境不得继续携带指向不存在用户的开发白名单 ID。当前入口仍为 HTTP，HTTPS 启用前管理员密码没有 TLS 传输保护。

OSS Bucket的CORS规则当前精确允许 `http://127.0.0.1:5173`、`http://localhost:5173` 和 `http://47.114.50.170`，方法为GET/PUT/HEAD、请求头为`*`，暴露ETag与x-oss-request-id。2026-09-11公网签名PUT和预检均已真实通过。应用RAM密钥没有Bucket CORS管理权限；正式域名切换HTTPS时需由主账号追加对应HTTPS Origin，不能用HTTP IP规则代替。

2026-09-12本地源码已移除Google Fonts远程依赖，改用系统中文字体栈，尚未再次发布。DeepFilterNet 0.5.6已接入上传参考音频流程：浏览器原生统一48kHz单声道WAV，`POST /api/uploads/denoise` 在异步低优先级子进程中净化并写回私有OSS，弹窗提供原音/净化音试听选择。新上传对象键按用户ID隔离，创建音色拒绝跨账号对象。真实容器与OSS闭环通过，但浏览器最终克隆和生产性能未验收，不能标记完成或直接宣传上线。

后续更新统一使用 `DEPLOY_TARGET=weiguang-prod ./scripts/publish-production.zsh`；不要用首次部署用的 `package-production.zsh` 覆盖既有 `.env.production`。发布包携带 amd64 API 镜像和管理端静态文件，不含任何运行密钥。项目专用密钥位于本机 `~/.ssh/weiguang_ecs_deploy`，SSH别名为 `weiguang-prod`。服务器侧 `apply-release.sh` 先备份数据库，只重建API，并在健康失败时恢复上一镜像、Nginx/Compose和管理端静态文件。首次自动发布 `20260911T151342Z` 已真实通过，备份位于 `/opt/weiguang/releases/backup-20260911T151342Z/`。

用户端新增隐私/协议/数据权利与DELETE /api/auth/me两步注销；远端OSS/百炼清理可能pending，必须展示服务端结果。手机聊天用会话/聊天/语音三视图。普通声音设置不得显示完整System Prompt；称呼字段统一经过sanitize_persona_quality。

`scripts/test_admin_endpoints.py`必须只用随机管理员并清理，严禁再次取BILLING_HARD_USER_IDS中的真实ID做upsert。2026-09-05已因旧脚本污染恢复两名管理员邮箱/密码哈希并清理6个测试账号；复跑后不再改变真实账号。

### 2026-09-05 聊天用户头像来源

OCR审核只保留left_avatar_object_key上传入口；right_avatar历史列不删除以兼容旧数据，但前端不再读取。ChatView对所有who=user消息统一显示auth.profile.avatar_download_url，缺失/加载失败显示nickname或email首字，适用于text、voice与imported消息。who=ai仍按activeConversationId取会话avatar_download_url。不要再次根据消息kind或导入右侧头像分流用户头像。

### 2026-09-05 账号头像与注册校验

迁移015新增app_users.avatar_object_key。头像走`POST /api/auth/avatar/presign`→浏览器PUT私有OSS→`PUT /api/auth/avatar`，对象必须位于account-avatars/{user_id}/，资料响应签发avatar_download_url；限制JPEG/PNG/WEBP、5MB（客户端大小校验）。注册密码为10–72位并含字母、数字、特殊字符，邮箱格式在auth_validation.py校验，LOWER(email)唯一索引继续判重。新规则仅用于注册，登录兼容旧密码。真实用户头像不作为测试写入。

### 2026-09-05 角色头像绑定

**同日更正，以此为准**：用户明确要求不同聊天头像隔离。ChatView已改为按activeConversationId从会话列表取avatar_download_url，不再取全局activePersona头像。没有会话头像时显示首字默认头像。导入审核已移除全局角色头像同步操作，沿用目标会话头像保存/续签；此前为用户“欲.”加的全局绑定已撤销，原图和会话头像保留。下方角色头像API记录作为历史能力说明，不代表当前聊天展示来源。

迁移014新增personas.avatar_object_key。`PUT /api/personas/{id}`接收可选avatar_import_id，后端验证导入批次属于调用用户且有left_avatar_object_key，再绑定目标所属角色。列表/active/详情/更新/激活/导入蒸馏响应提供临时avatar_download_url；数据库不保存签名链接。OCR确认时头像可独立于声音画像同步；新角色生成继承左侧头像。ChatView的普通AI回复使用当前角色头像（延续现有名称跟随当前角色的展示规则），失败或空值显示名字首字。

### 2026-09-05 启动迁移兼容修复

各Store启动会重复执行历史SQL。005中的单活跃会话唯一索引创建语句已移除，012仍负责删除旧库索引；否则多会话数据会使后端在执行012前启动失败。不要恢复该旧约束。隔离schema已验证新安装和多会话后两次迁移重放，现有数据保留。OCR额度查询10秒超时，点击立即显示进度，失败保留选图。

### 2026-09-05 OCR 画像应用当前角色

`PUT /api/personas/{id}` 新增可选 `voice_style`（VoiceProfile校验）。PersonaStore在同一事务内锁定所属角色、仅合并声音字段并重编译人设；原有完整persona更新仍兼容。OCR审核页明确勾选应用目标；“确认导入”先保存批次，再调用角色局部更新并刷新前端Store，成功后继续导入。角色设置作用于各会话后续语音/新生成朗读，不改变既有音频。取消勾选或仅“保存修正”不更新角色；自动生成角色路径仍将画像写给新角色。

### 同日新增：后端语境规划与 OCR 声音画像

`POST /api/chat-and-tts/stream` 增加 JSON `adaptive_voice/persona_id/conversation_id/replay_turn_id`。开启自适应后忽略客户端声音覆盖，服务端读取所属角色/会话，复用本次 LLM 生成逐句 NDJSON；正文与官方标签分离，按句合成。原纯文本链路和没有保存计划的旧消息朗读保持原行为。

新增 `audio.asset` SSE 事件（speech_turn_id、sample_rate）；`GET /api/speech-turns/{id}/audio` 鉴权读取完整 WAV，404表示不可访问、409中断、410缓存过期。过期用replay_turn_id恢复原计划，无LLM调用；仍按实际交付音频扣语音额度。缓存7天、每用户30份、每份12MiB，计划元数据保留。迁移 `internal/auth/migrations/013_adaptive_speech.sql` 添加speech_turns、消息关联与OCR voice_style。

新语音回合最多携带本会话30条历史和最近8条中的一条视觉消息（最多4附件），私有URL续签。首计划12秒超时，队列有界；取消关闭供应商流。OCR审核与角色工坊共用VoiceProfileForm，固定值优先、旧值兼容；不使用localStorage。图片无法用于测量真实声音年龄、性别或音质。

本地mock/事务回读/构建通过，真实共情与庆祝短句返回PCM。听感、完整OCR上传和首音频延迟对照仍待验收，参见对应plan。未新增依赖或额外逐句LLM请求。

### 参数修复基线

Qwen-Audio-TTS HTTP/SSE 使用 `input.instruction`、`input.rate`、`input.sample_rate`。内部 `/api/tts`、`/api/messages/tts` 在 JSON 中接收 rate/sample_rate；`/api/chat-and-tts` 与其 `/stream` 路由通过查询参数接收。语速范围0.5–2，三档UI映射0.85/1/1.15。参数在额度预留前校验，慢速扩大预留，最终按实际交付PCM时长结算。

前端以实际音色、合成指令、语速、采样率生成版本2缓存键，并固定请求设置快照。采样率控件不再标作“高清晰度”。Provider请求体、四入口额度mock、前端7项测试通过；真实HTTP24k/1倍速与SSE48k/0.85倍速返回有效WAV，时长分别2.160/2.541秒。

### 2026-09-14 聊天背景图

聊天页右上角上传背景/恢复默认，账号级共用。复用POST /api/auth/avatar/presign和私有OSS直传；PUT /api/auth/chat-background接收object_key（null恢复默认），检查用户目录、文件头及5MB上限后存app_users.chat_background_object_key。020迁移由当前Python统一迁移器自动读取internal/auth/migrations执行。账号资料返回chat_background_download_url，刷新时重新签名；注销账号纳入已有对象清理。同步路由运行在线程池，不介入语音转发。前端构建、mock回归、迁移及按钮检查通过，真实图片上传刷新待验收。

### 2026-09-14 背景范围扩展

PUT /api/auth/chat-background增加scope（global默认/panel）。global=当前聊天整页，panel=右侧消息区（账号级）；021新增chat_panel_background_object_key并在profile签名回显。全局更新在单条用户限定UPDATE中同步清空panel；panel修改不影响全局，global+null恢复全部默认。UI提供两个上传按钮，图片仍用原有校验及OSS流程。mock/构建/迁移和入口检查通过，新范围真实上传覆盖待验收。

### 2026-09-14 最新范围：仅消息区背景

用户要求移除全局背景。前端已移除全局显示、上传及整页恢复入口，仅保存scope=panel，清除后恢复默认深色。旧全局字段/API保留兼容，不再用于当前聊天页展示。构建和Chrome确认整页无背景、消息区原背景保留。

### 2026-09-14 用户取消背景功能

背景上传需求已取消，前端入口、上传调用及背景渲染均已移除，默认深色恢复；历史数据库字段、对象及后端接口保留兼容。构建和Chrome验收通过。此前上传验收项不再继续执行。
