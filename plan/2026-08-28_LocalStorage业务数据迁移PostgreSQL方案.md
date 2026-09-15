# [未完成] Local Storage 业务数据迁移 PostgreSQL 方案

> **状态**：未完成 (Pending)
> **创建时间**：2026-08-28
> **完成时间**：待浏览器迁移与回读验收通过后填写

## 一、目标

彻底停止以 `localStorage` 作为微光业务数据源，将当前浏览器中的账户资料、角色/音色设置、聊天记录及遗留故事寄语迁移至当前 FastAPI 服务使用的 PostgreSQL，并在数据库写入与回读确认成功后删除对应 Local Storage Key。

## 二、迁移范围

| Local Storage Key | 目标数据库 | 处理方式 |
|---|---|---|
| `weiguang.local.profile.v1` | `app_users` | 保留用户 UUID、邮箱、昵称与创建时间 |
| `weiguang.local.profile-id.v1` | `app_users.id` / `app_sessions` | 迁移后由 HttpOnly 会话 Cookie 取代 |
| `weiguang.local.voice-settings.v1` | `user_voice_settings` | 保存角色设定、音色 ID 与原始兼容配置 JSON |
| `weiguang.local.chat-history.v1` | `chat_conversations` / `chat_messages` | 按旧消息 ID 幂等导入，保留时间、角色、类型、状态和附件 |
| `weiguang_custom_stories` | `community_stories` | 原样保留遗留寄语 JSON，避免数据丢失 |

同源下的 `fsmt_*` 等其他项目 Key 不属于本次范围，严禁删除。

## 三、数据库与会话设计

- 在 `backend/migrations/005_app_data_persistence.sql` 增加用户、会话、设置、聊天和故事表。
- 当前运行代码自动加载 `backend/migrations/`；虽然旧规范仍提到 `internal/auth/migrations/`，但该目录在当前 checkout 已不存在，因此以实际 FastAPI 迁移机制为准并记录差异。
- 注册/登录使用 PostgreSQL 用户表；密码采用 Python 标准库 `hashlib.scrypt` 加随机盐哈希，不新增依赖。
- 登录成功后使用随机 Session Token，数据库仅保存 SHA-256 摘要，浏览器仅接收 `HttpOnly + SameSite=Lax` Cookie。
- 当前前端不再发送依赖 Local Storage 生成的 `X-Weiguang-User-ID`；后端现有接口优先解析会话 Cookie，保留 Header 仅用于现有工具兼容。

官方依据：FastAPI 支持通过 `Response.set_cookie()` 设置响应 Cookie；Psycopg 连接上下文在正常退出时提交、异常时回滚。本方案使用事务完成“一次性导入 + 会话创建”。

## 四、一次性安全迁移流程

1. 页面启动先请求 `GET /api/auth/me`。
2. 无有效数据库会话且检测到微光旧 Key 时，读取旧值并调用 `POST /api/migrations/local-storage`。
3. 后端在单个事务中幂等写入用户、设置、聊天、故事与新会话，返回导入计数和数据库资料。
4. 前端再次请求数据库历史/设置进行回读。
5. 只有后端迁移成功且关键数据回读成功后，删除上述五个微光 Key。
6. 任一步失败都保留 Local Storage 原数据并显示错误，禁止“先删后迁”。

迁移创建的旧账户没有可恢复的密码哈希，但当前浏览器会获得数据库会话。若以后登出，可在注册界面用原邮箱首次设置正式密码；已有密码账户仍按正常登录校验。

## 五、前端切换

- `fetchMe/login/register/logout/patchMe` 全部改为 `/api/auth/*`。
- 角色/音色设置改为 `/api/voice-settings`。
- 聊天历史改为 `/api/chat-history`，消息写入使用幂等 upsert，清空新对话由后端归档/删除当前会话数据。
- `requestJSON` 与 SSE 统一使用同源 Cookie，不再读取或写入 Local Storage。
- TTS Cache Storage 仍是可删除、可回源的非权威二进制缓存，不属于本次业务数据删除范围。

## 六、验收标准

1. 数据库迁移成功，当前用户资料、设置、聊天和故事导入计数与浏览器旧数据一致。
2. 页面刷新后可通过 HttpOnly Cookie 恢复登录，并从数据库回显历史与设置。
3. Application → Local Storage 中不再存在任何 `weiguang*` Key；`fsmt_*` 保持不变。
4. 全仓 `frontend/src` 不再出现 `localStorage` 读写。
5. 新消息、昵称、角色设置刷新后均从数据库恢复；“新对话”只操作数据库。
6. 前端生产构建、后端编译、数据库表/行数、API smoke 与浏览器回读通过。
7. 旧 PostgreSQL `weiguang-postgres-1` 中历史数据保持只读不变；本次不在未确认身份映射的情况下自动并入当前账户。

## 七、涉及文件

- `backend/migrations/005_app_data_persistence.sql`
- `backend/app_data_store.py`
- `backend/app.py`
- `frontend/src/api/index.ts`
- `frontend/src/views/ChatView.vue`
- `progress/PROGRESS.md`
- `progress/index.html`
- `HANDOFF.md`

## 八、实施与验收记录（2026-08-28）

- 已新增 PostgreSQL 用户、Session、角色设置、聊天会话/消息及故事表，并由当前 FastAPI 迁移加载器执行。
- 已新增数据库注册/登录/登出、HttpOnly Cookie、资料、设置、聊天、故事及本机一次性迁移 API。
- 前端业务读写已切换数据库 API；`localStorage` 只保留在一次性迁移适配器中，用于“读取旧值 → 数据库回读 → 删除五个 Key”。
- 后端 compileall、前端生产构建、`scripts/test_app_data_persistence.py` 和 HTTP API smoke 均通过；未登录读取聊天接口返回 `401`。
- 当前浏览器用户已自动迁入数据库并回读：5 条消息、1 份角色设置、1 条遗留故事、1 个有效数据库 Session。
- 旧 `weiguang-postgres-1` 中的 38 条消息保持只读不变，尚未确认与当前账户的身份映射，因此未自动合并。
- 尚待用户在 Chrome Application 面板确认五个微光 Local Storage Key 已消失；确认后将标题更新为 `[已完成]`。
