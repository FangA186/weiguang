import type {
  Profile,
  VoiceSettingsRecord,
  ChatHistoryResponse,
  ChatConversationListResponse,
  ChatConversationRecord,
  ChatMessageRecord,
  ChatAttachment,
  ContentPart,
  BailianChatResult,
  BailianChatAndTTSResult,
  BailianStreamEvent,
  BailianMediaUploadPresign,
  VoiceCloneRecord,
  VoiceCloneListResponse,
  DeleteVoiceCloneResponse,
  MessageTTSResponse,
  ChatImportBatch,
  ChatImportAttachment,
  ChatImportMessage,
  ChatImportListResponse,
  BillingSummary,
  BillingChannels,
  RedemptionResult,
  PlanDefinition,
  BillingMetricCode,
  PersonaRecord,
  PersonaCreatePayload,
  PersonaUpdatePayload,
  PersonaDistillPayload,
  PersonaCorrectionPayload,
  PersonaVersionRecord,
  PersonaCorrectionRecord,
  DeleteAccountResponse,
} from "../types";

export interface QuotaExceededPayload {
  code: "quota_exceeded";
  metric: BillingMetricCode;
  used: number;
  limit: number;
  remaining: number;
  reset_at?: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  metric?: BillingMetricCode;
  used?: number;
  reserved?: number;
  limit?: number;
  remaining?: number;
  reset_at?: string;

  constructor(message: string, status: number, details: Partial<QuotaExceededPayload> = {}) {
    super(message);
    this.status = status;
    this.code = details.code;
    this.metric = details.metric;
    this.used = details.used;
    this.limit = details.limit;
    this.remaining = details.remaining;
    this.reset_at = details.reset_at;
  }
}

function errorDetails(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== "object") return {};
  const body = payload as Record<string, unknown>;
  return body.detail && typeof body.detail === "object"
    ? body.detail as Record<string, unknown>
    : body;
}

function apiErrorFromPayload(payload: unknown, status: number): ApiError {
  const details = errorDetails(payload);
  const message = typeof details.message === "string"
    ? details.message
    : typeof details.detail === "string"
      ? details.detail
      : typeof (payload as Record<string, unknown> | null)?.message === "string"
        ? (payload as Record<string, unknown>).message as string
        : "请求失败";
  return new ApiError(message, status, details as Partial<QuotaExceededPayload>);
}

export function isQuotaExceededError(error: unknown): error is ApiError & QuotaExceededPayload {
  return error instanceof ApiError && error.status === 402 && error.code === "quota_exceeded" && Boolean(error.metric);
}

export function quotaExceededMessage(error: unknown): string {
  if (!isQuotaExceededError(error)) return error instanceof Error ? error.message : "请求失败";
  const reset = error.reset_at ? "，可在本期重置后继续使用" : "";
  switch (error.metric) {
    case "ai_reply":
      return `本期 AI 回答额度已用完${reset}。`;
    case "ai_voice_seconds":
      return `本期 AI 语音额度已用完，请改用文字回答${reset}。`;
    case "image":
    case "video":
      return "图片或视频额度不足，请移除附件后以纯文本发送。";
    case "voice_slot":
      return `专属克隆音色槽位已满${reset}。`;
    case "chat_import_batch":
      return `本期截图导入批次已用完${reset}。`;
    default:
      return `本期套餐额度已用完${reset}。`;
  }
}

/** A request ID lives only for the in-flight request; it is never persisted in browser storage. */
export function createRequestId(): string {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  if (globalThis.crypto?.getRandomValues) globalThis.crypto.getRandomValues(bytes);
  else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

const LEGACY_STORAGE_KEYS = {
  profile: "weiguang.local.profile.v1",
  profileId: "weiguang.local.profile-id.v1",
  settings: "weiguang.local.voice-settings.v1",
  history: "weiguang.local.chat-history.v1",
  stories: "weiguang_custom_stories",
} as const;

function parseLegacyValue<T>(key: string, fallback: T): T {
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function legacyStoragePayload() {
  const profile = parseLegacyValue<Record<string, any> | null>(LEGACY_STORAGE_KEYS.profile, null);
  if (!profile?.id || !profile?.email) return null;
  return {
    profile,
    profile_id: localStorage.getItem(LEGACY_STORAGE_KEYS.profileId),
    voice_settings: parseLegacyValue<Record<string, any> | null>(LEGACY_STORAGE_KEYS.settings, null),
    chat_history: parseLegacyValue<ChatMessageRecord[]>(LEGACY_STORAGE_KEYS.history, []),
    stories: parseLegacyValue<Record<string, any>[]>(LEGACY_STORAGE_KEYS.stories, []),
  };
}

function clearMigratedLegacyStorage() {
  Object.values(LEGACY_STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
}

async function requestJSON<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = Object.assign(
    { "Content-Type": "application/json" },
    options.headers || {},
  );
  const response = await fetch(url, { ...options, headers, credentials: "same-origin" });
  const text = await response.text();
  let payload: any;
  try {
    payload = JSON.parse(text);
  } catch {
    payload = { message: text || "服务响应异常" };
  }
  if (!response.ok) {
    throw apiErrorFromPayload(payload, response.status);
  }
  return payload as T;
}

export interface AuthInput {
  email: string;
  password: string;
  nickname?: string;
}

export async function fetchMe(): Promise<Profile | null> {
  try {
    const profile = await requestJSON<Profile>("/api/auth/me");
    // The migration endpoint is deliberately disabled in production. Avoid a
    // guaranteed 403 on every production page load while preserving the old
    // browser data for an explicit local-development migration.
    if (import.meta.env.PROD) return profile;
    const legacy = legacyStoragePayload();
    if (!legacy) return profile;
    try {
      return await migrateLegacyStorage(legacy);
    } catch (error) {
      // A valid server session remains usable when this development-only
      // migration endpoint is forbidden. Legacy data is intentionally kept.
      if (error instanceof ApiError && error.status === 403) return profile;
      throw error;
    }
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error;
    if (import.meta.env.PROD) return null;
    const legacy = legacyStoragePayload();
    if (!legacy) return null;
    try {
      return await migrateLegacyStorage(legacy);
    } catch (migrationError) {
      // An anonymous browser must not fail initialization merely because the
      // protected migration endpoint rejects the old browser data.
      if (migrationError instanceof ApiError && migrationError.status === 403) return null;
      throw migrationError;
    }
  }
}

export async function login(input: AuthInput): Promise<Profile> {
  return requestJSON<Profile>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function register(input: AuthInput): Promise<Profile> {
  return requestJSON<Profile>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

async function uploadAvatarFile(file: File, label = '头像'): Promise<string> {
  const type=file.type.toLowerCase();
  if (!['image/jpeg','image/png','image/webp'].includes(type)) throw new Error(`${label}仅支持 JPG、PNG 或 WEBP`);
  if (file.size > 5*1024*1024) throw new Error(`${label}不能超过 5MB`);
  const signed=await requestJSON<BailianMediaUploadPresign>('/api/auth/avatar/presign',{
    method:'POST',body:JSON.stringify({filename:file.name,content_type:type,expires_seconds:900}),
  });
  const uploaded=await fetch(signed.upload_url,{method:'PUT',headers:signed.headers,body:file});
  if (!uploaded.ok) throw new Error(`${label}上传失败（HTTP ${uploaded.status}）`);
  return signed.object_key;
}

export async function uploadAccountAvatar(file: File): Promise<Profile> {
  const object_key = await uploadAvatarFile(file);
  return requestJSON<Profile>('/api/auth/avatar',{method:'PUT',body:JSON.stringify({object_key})});
}

export async function updateChatConversation(id: string, input: {title?: string; avatar_object_key?: string}): Promise<ChatConversationRecord> {
  return requestJSON<ChatConversationRecord>(`/api/chat-history/conversations/${encodeURIComponent(id)}`, {method:'PATCH', body:JSON.stringify(input)});
}

export async function uploadConversationAvatar(id: string, file: File): Promise<ChatConversationRecord> {
  const avatar_object_key = await uploadAvatarFile(file);
  return updateChatConversation(id, {avatar_object_key});
}

export async function logout(): Promise<void> {
  await requestJSON<{ status: string }>("/api/auth/logout", { method: "POST" });
}

export async function deleteAccount(): Promise<DeleteAccountResponse> {
  const result = await requestJSON<DeleteAccountResponse>("/api/auth/me", { method: "DELETE" });
  if (!result || typeof result.status !== "string") throw new Error("账号删除结果无效，请联系支持人员");
  return result;
}

export async function patchMe(patch: { nickname?: string }): Promise<Profile | null> {
  if (!patch.nickname?.trim()) return fetchMe();
  return requestJSON<Profile>("/api/auth/me", {
    method: "PATCH",
    body: JSON.stringify({ nickname: patch.nickname.trim() }),
  });
}

async function migrateLegacyStorage(legacy: NonNullable<ReturnType<typeof legacyStoragePayload>>): Promise<Profile> {
  const result = await requestJSON<{
    profile: Profile;
    counts: { messages: number; stories: number; settings: number };
  }>("/api/migrations/local-storage", {
    method: "POST",
    body: JSON.stringify(legacy),
  });

  const [history, settings, stories] = await Promise.all([
    requestJSON<ChatHistoryResponse>("/api/chat-history?limit=200"),
    requestJSON<VoiceSettingsRecord>("/api/voice-settings"),
    requestJSON<{ stories: Record<string, any>[] }>("/api/stories"),
  ]);
  if (history.messages.length < legacy.chat_history.length) {
    throw new Error("聊天记录数据库回读数量不足，已保留浏览器旧数据");
  }
  if (legacy.voice_settings && !settings.updated_at) {
    throw new Error("角色设置数据库回读失败，已保留浏览器旧数据");
  }
  if (result.counts.stories < legacy.stories.length || stories.stories.length < legacy.stories.length) {
    throw new Error("故事寄语数据库写入数量不足，已保留浏览器旧数据");
  }
  clearMigratedLegacyStorage();
  return result.profile;
}

export type ChatMessagePayload = Array<{ role: string; content: string | ContentPart[] }>;

export async function chat(
  messages: ChatMessagePayload,
  temperature?: number,
  requestId = createRequestId(),
): Promise<BailianChatResult> {
  return requestJSON<BailianChatResult>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ messages, temperature, request_id: requestId }),
  });
}

export async function chatAndTTS(
  messages: ChatMessagePayload,
  options: { voice?: string; instruction?: string; sampleRate?: number; rate?: number; temperature?: number; requestId?: string } = {},
): Promise<BailianChatAndTTSResult> {
  const query = new URLSearchParams();
  if (options.voice) query.set("voice", options.voice);
  if (options.instruction) query.set("instruction", options.instruction);
  if (options.sampleRate) query.set("sample_rate", String(options.sampleRate));
  if (options.rate !== undefined) query.set("rate", String(options.rate));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return requestJSON<BailianChatAndTTSResult>(`/api/chat-and-tts${suffix}`, {
    method: "POST",
    body: JSON.stringify({
      messages,
      temperature: options.temperature,
      request_id: options.requestId || createRequestId(),
    }),
  });
}

export async function streamChatAndTTS(
  messages: ChatMessagePayload,
  options: { voice?: string; instruction?: string; sampleRate?: number; rate?: number; temperature?: number; requestId?: string; adaptiveVoice?: boolean; personaId?: string; conversationId?: string; replayTurnId?: string } = {},
  onEvent: (event: BailianStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const query = new URLSearchParams();
  if (!options.replayTurnId && options.voice) query.set("voice", options.voice);
  if (!options.adaptiveVoice && !options.replayTurnId) {
    if (options.instruction) query.set("instruction", options.instruction);
    if (options.sampleRate) query.set("sample_rate", String(options.sampleRate));
    if (options.rate !== undefined) query.set("rate", String(options.rate));
  }
  return streamSSE(
    `/api/chat-and-tts/stream?${query.toString()}`,
    options.adaptiveVoice ? messages.filter(message => message.role !== 'system') : messages,
    options.temperature,
    onEvent,
    signal,
    options.requestId,
    { adaptive_voice: options.adaptiveVoice, persona_id: options.personaId, conversation_id: options.conversationId, replay_turn_id: options.replayTurnId },
  );
}

export async function streamChat(
  messages: ChatMessagePayload,
  onEvent: (event: BailianStreamEvent) => void,
  signal?: AbortSignal,
  requestId?: string,
): Promise<void> {
  return streamSSE("/api/chat/stream", messages, undefined, onEvent, signal, requestId);
}

export async function synthesizeMessageTTS(
  text: string,
  options?: { voice?: string; instruction?: string; format?: string; sample_rate?: number; rate?: number; volume?: number; pitch?: number; use_defaults?: boolean; requestId?: string }
): Promise<MessageTTSResponse> {
  return requestJSON<MessageTTSResponse>("/api/messages/tts", {
    method: "POST",
    body: JSON.stringify({
      text,
      voice: options?.voice,
      instruction: options?.instruction,
      format: options?.format || "wav",
      sample_rate: options?.sample_rate || 24000,
      rate: options?.rate ?? 1,
      volume: options?.volume ?? 50,
      pitch: options?.pitch ?? 1,
      use_defaults: options?.use_defaults ?? false,
      request_id: options?.requestId || createRequestId(),
    }),
  });
}

async function streamSSE(
  url: string,
  messages: ChatMessagePayload,
  temperature: number | undefined,
  onEvent: (event: BailianStreamEvent) => void,
  signal?: AbortSignal,
  requestId = createRequestId(),
  speechScope?: { adaptive_voice?: boolean; persona_id?: string; conversation_id?: string; replay_turn_id?: string },
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ messages, temperature, request_id: requestId, ...speechScope }),
    credentials: "same-origin",
    signal,
  });
  if (!response.ok || !response.body) {
    const text = await response.text();
    let payload: unknown = { message: text || `流式请求失败（HTTP ${response.status}）` };
    try { payload = JSON.parse(text); } catch { /* retain response text */ }
    throw apiErrorFromPayload(payload, response.status);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const consume = (chunk: string) => {
    buffer += chunk;
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() || "";
    for (const frame of frames) {
      const data = frame.split(/\r?\n/).find((line) => line.startsWith("data:"));
      if (!data) continue;
      try { onEvent(JSON.parse(data.slice(5).trim()) as BailianStreamEvent); } catch { /* ignore malformed SSE frames */ }
    }
  };
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      consume(decoder.decode(value, { stream: true }));
    }
    consume(decoder.decode());
  } finally {
    reader.releaseLock();
  }
}

export async function fetchVoiceSettings(): Promise<VoiceSettingsRecord> {
  return requestJSON<VoiceSettingsRecord>("/api/voice-settings");
}

export async function saveVoiceSettings(input: {
  speaker: string;
  character_manifest: string;
  voice_clone?: VoiceCloneRecord | null;
}): Promise<VoiceSettingsRecord> {
  return requestJSON<VoiceSettingsRecord>("/api/voice-settings", {
    method: "PUT",
    body: JSON.stringify({
      speaker: input.speaker,
      character_manifest: input.character_manifest,
    }),
  });
}

export interface BailianUploadPresign {
  bucket: string;
  region: string;
  object_key: string;
  upload_url: string;
  expires_in: number;
  headers: Record<string, string>;
}

export interface BailianVoiceClonePayload {
  object_key: string;
  request_id?: string;
  prefix?: string;
  language_hints?: string[];
  enable_preprocess?: boolean;
  enable_volume_normalization?: boolean;
  max_prompt_audio_length?: number;
  reference_filename?: string;
  reference_size?: number;
  reference_duration?: number;
}

export interface BailianVoiceCloneResult extends VoiceCloneRecord {
  usage?: unknown;
}

export interface VoiceDenoiseResult {
  object_key: string;
  download_url: string;
  size: number;
  duration: number;
  engine: "DeepFilterNet";
  engine_version: string;
}

function audioContentType(file: File): string {
  if (file.type) return file.type;
  const extension = file.name.toLowerCase().split(".").pop();
  return extension === "mp3" ? "audio/mpeg" : extension === "m4a" ? "audio/mp4" : "audio/wav";
}

export async function presignBailianVoiceUpload(file: File): Promise<BailianUploadPresign> {
  return requestJSON<BailianUploadPresign>("/api/uploads/presign", {
    method: "POST",
    body: JSON.stringify({ filename: file.name, content_type: audioContentType(file) }),
  });
}

export async function uploadBailianVoiceReference(
  presign: BailianUploadPresign,
  file: File,
): Promise<void> {
  const response = await fetch(presign.upload_url, {
    method: "PUT",
    headers: presign.headers,
    body: file,
  });
  if (!response.ok) throw new Error(`参考音频上传失败（HTTP ${response.status}）。`);
}

export async function denoiseBailianVoiceReference(objectKey: string): Promise<VoiceDenoiseResult> {
  return requestJSON<VoiceDenoiseResult>("/api/uploads/denoise", {
    method: "POST",
    body: JSON.stringify({ object_key: objectKey }),
  });
}

export function mediaContentType(file: File): string {
  if (file.type) return file.type;
  const ext = file.name.toLowerCase().split(".").pop();
  if (ext === "png") return "image/png";
  if (ext === "jpg" || ext === "jpeg") return "image/jpeg";
  if (ext === "webp") return "image/webp";
  if (ext === "mp4") return "video/mp4";
  if (ext === "mov") return "video/quicktime";
  if (ext === "webm") return "video/webm";
  return "image/jpeg";
}

export async function presignMediaUpload(file: File): Promise<BailianMediaUploadPresign> {
  return requestJSON<BailianMediaUploadPresign>("/api/uploads/presign-media", {
    method: "POST",
    body: JSON.stringify({ filename: file.name, content_type: mediaContentType(file) }),
  });
}

export async function uploadMediaAttachment(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<ChatAttachment> {
  const presign = await presignMediaUpload(file);
  const localPreviewUrl = URL.createObjectURL(file);

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", presign.upload_url, true);
    for (const [key, value] of Object.entries(presign.headers)) {
      xhr.setRequestHeader(key, value);
    }
    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`媒体上传失败（HTTP ${xhr.status}）`));
    };
    xhr.onerror = () => reject(new Error("网络异常，媒体上传失败"));
    xhr.send(file);
  });

  return {
    id: `att-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    kind: presign.kind,
    object_key: presign.object_key,
    filename: file.name,
    content_type: mediaContentType(file),
    file_size: file.size,
    url: localPreviewUrl,
    download_url: presign.download_url,
    uploading: false,
    progress: 100,
  };
}

export async function createBailianVoiceClone(
  input: BailianVoiceClonePayload,
): Promise<BailianVoiceCloneResult> {
  return requestJSON<BailianVoiceCloneResult>("/api/voice-clones", {
    method: "POST",
    body: JSON.stringify({ ...input, request_id: input.request_id || createRequestId() }),
  });
}

export async function fetchVoiceClones(): Promise<VoiceCloneListResponse> {
  return requestJSON<VoiceCloneListResponse>("/api/voice-clones");
}

export async function deleteVoiceClone(voiceId: string): Promise<DeleteVoiceCloneResponse> {
  return requestJSON<DeleteVoiceCloneResponse>(`/api/voice-clones/${encodeURIComponent(voiceId)}`, {
    method: "DELETE",
  });
}

export async function renameVoiceClone(voiceId: string, name: string): Promise<VoiceCloneRecord> {
  return requestJSON<VoiceCloneRecord>(`/api/voice-clones/${encodeURIComponent(voiceId)}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export async function fetchChatMessages(params?: { limit?: number; before_id?: number; conversation_id?: string }): Promise<ChatHistoryResponse> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.conversation_id) query.set("conversation_id", params.conversation_id);
  return requestJSON<ChatHistoryResponse>(`/api/chat-history${query.size ? `?${query}` : ""}`);
}

export async function fetchChatConversations(): Promise<ChatConversationListResponse> {
  return requestJSON<ChatConversationListResponse>("/api/chat-history/conversations");
}

export async function createChatConversation(input: { title?: string; avatar_object_key?: string } = {}): Promise<ChatConversationRecord> {
  return requestJSON<ChatConversationRecord>("/api/chat-history/conversations", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function clearChatMessages(conversationId?: string): Promise<ChatHistoryResponse> {
  const query = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : "";
  return requestJSON<ChatHistoryResponse>(`/api/chat-history${query}`, { method: "DELETE" });
}

export async function upsertChatMessage(input: {
  id: number;
  conversation_id?: string;
  role: ChatMessageRecord["role"];
  content: string;
  kind?: ChatMessageRecord["kind"];
  attachments?: ChatAttachment[];
  import_meta?: ChatMessageRecord["import_meta"];
  speech_turn_id?: string;
}): Promise<ChatMessageRecord> {
  return requestJSON<ChatMessageRecord>("/api/chat-history/messages", {
    method: "PUT",
    body: JSON.stringify({
      ...input,
      kind: input.kind || "text",
      status: "completed",
      audio_duration_ms: 0,
      created_at: new Date().toISOString(),
      attachments: input.attachments || [],
    }),
  });
}

export async function uploadScreenshotForImport(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<ChatImportAttachment> {
  const presign = await requestJSON<BailianMediaUploadPresign>("/api/uploads/presign-media", {
    method: "POST",
    body: JSON.stringify({ filename: file.name, content_type: mediaContentType(file) }),
  });
  const localPreviewUrl = URL.createObjectURL(file);

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", presign.upload_url, true);
    for (const [key, value] of Object.entries(presign.headers)) {
      xhr.setRequestHeader(key, value);
    }
    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`截图上传失败（HTTP ${xhr.status}）`));
    };
    xhr.onerror = () => reject(new Error("网络异常，截图上传失败"));
    xhr.send(file);
  });

  return {
    object_key: presign.object_key,
    filename: file.name,
    content_type: mediaContentType(file),
    file_size: file.size,
    local_preview: localPreviewUrl,
    download_url: presign.download_url,
  };
}

export async function createChatImport(payload: {
  request_id?: string;
  attachments: Array<{
    object_key: string;
    filename?: string;
    content_type?: string;
    file_size?: number;
    image_width?: number;
    image_height?: number;
    sort_order?: number;
  }>;
  source_type?: string;
  timezone?: string;
}): Promise<ChatImportBatch> {
  return requestJSON<ChatImportBatch>("/api/chat-imports", {
    method: "POST",
    body: JSON.stringify({ ...payload, request_id: payload.request_id || createRequestId() }),
  });
}

export async function fetchChatImport(importId: number): Promise<ChatImportBatch> {
  return requestJSON<ChatImportBatch>(`/api/chat-imports/${importId}`);
}

export async function fetchChatImports(params?: { limit?: number; offset?: number }): Promise<ChatImportListResponse> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const qs = query.toString();
  return requestJSON<ChatImportListResponse>(`/api/chat-imports${qs ? `?${qs}` : ""}`);
}

export async function updateChatImport(
  importId: number,
  messages: ChatImportMessage[],
  avatars?: { left_avatar_object_key?: string; right_avatar_object_key?: string; voice_style?: ChatImportBatch['voice_style'] },
): Promise<ChatImportBatch> {
  return requestJSON<ChatImportBatch>(`/api/chat-imports/${importId}`, {
    method: "PATCH",
    body: JSON.stringify({ messages, ...avatars }),
  });
}

export async function confirmChatImport(
  importId: number,
  options?: { save_conversation?: boolean; extract_memories?: boolean },
): Promise<ChatImportBatch> {
  return requestJSON<ChatImportBatch>(`/api/chat-imports/${importId}/confirm`, {
    method: "POST",
    body: JSON.stringify(options || { save_conversation: true, extract_memories: false }),
  });
}

export async function deleteChatImport(importId: number): Promise<{ status: string; deleted_id: number }> {
  return requestJSON<{ status: string; deleted_id: number }>(`/api/chat-imports/${importId}`, {
    method: "DELETE",
  });
}

export async function presignImportMessageMedia(
  importId: number,
  messageId: number,
  file: File,
  mediaKind: "image" | "video",
): Promise<BailianMediaUploadPresign> {
  return requestJSON<BailianMediaUploadPresign>(
    `/api/chat-imports/${importId}/messages/${messageId}/media/presign`,
    {
      method: "POST",
      body: JSON.stringify({
        filename: file.name,
        content_type: mediaContentType(file),
        media_kind: mediaKind,
      }),
    },
  );
}

export async function confirmImportMessageMedia(
  importId: number,
  messageId: number,
  objectKey: string,
  mediaKind: "image" | "video",
): Promise<ChatImportMessage> {
  return requestJSON<ChatImportMessage>(
    `/api/chat-imports/${importId}/messages/${messageId}/media/confirm`,
    {
      method: "POST",
      body: JSON.stringify({
        object_key: objectKey,
        media_kind: mediaKind,
      }),
    },
  );
}

export async function updateImportMessageTranscript(
  importId: number,
  messageId: number,
  transcript: string,
): Promise<ChatImportMessage> {
  return requestJSON<ChatImportMessage>(
    `/api/chat-imports/${importId}/messages/${messageId}/transcript`,
    {
      method: "PATCH",
      body: JSON.stringify({ transcript }),
    },
  );
}

export async function fetchBillingSummary(): Promise<BillingSummary> {
  return requestJSON<BillingSummary>("/api/billing/summary", { signal: AbortSignal.timeout(10000) });
}

export async function fetchPlans(): Promise<PlanDefinition[]> {
  const response = await requestJSON<{ plans: PlanDefinition[] }>("/api/plans");
  return response.plans;
}

export async function fetchBillingChannels(): Promise<BillingChannels> {
  return requestJSON<BillingChannels>("/api/billing/channels");
}

export async function redeemSubscriptionCode(code: string): Promise<RedemptionResult> {
  return requestJSON<RedemptionResult>("/api/billing/redeem", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

// ---------------------------------------------------------------------------
// Persona & Ex-Skill API Client
// ---------------------------------------------------------------------------

export async function fetchPersonas(): Promise<PersonaRecord[]> {
  return requestJSON<PersonaRecord[]>("/api/personas");
}

export async function fetchActivePersona(): Promise<PersonaRecord> {
  return requestJSON<PersonaRecord>("/api/personas/active");
}

export async function createPersona(payload: PersonaCreatePayload): Promise<PersonaRecord> {
  return requestJSON<PersonaRecord>("/api/personas", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPersonaDetail(personaId: string): Promise<PersonaRecord> {
  return requestJSON<PersonaRecord>(`/api/personas/${personaId}`);
}

export async function updatePersona(
  personaId: string,
  payload: PersonaUpdatePayload,
): Promise<PersonaRecord> {
  return requestJSON<PersonaRecord>(`/api/personas/${personaId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deletePersona(personaId: string): Promise<{ status: string; deleted_id: string }> {
  return requestJSON<{ status: string; deleted_id: string }>(`/api/personas/${personaId}`, {
    method: "DELETE",
  });
}

export async function activatePersona(personaId: string): Promise<PersonaRecord> {
  return requestJSON<PersonaRecord>(`/api/personas/${personaId}/activate`, {
    method: "POST",
  });
}

export async function distillPersona(
  personaId: string,
  payload: PersonaDistillPayload,
): Promise<{ status: string; persona: PersonaRecord }> {
  return requestJSON<{ status: string; persona: PersonaRecord }>(`/api/personas/${personaId}/distill`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function distillPersonaFromImport(payload: {
  import_id: number;
  persona_id?: string;
  name?: string;
  slug?: string;
}): Promise<{ status: string; persona: PersonaRecord }> {
  return requestJSON<{ status: string; persona: PersonaRecord }>("/api/personas/distill-from-import", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchPersonaVersions(personaId: string): Promise<PersonaVersionRecord[]> {
  return requestJSON<PersonaVersionRecord[]>(`/api/personas/${personaId}/versions`);
}

export async function rollbackPersonaVersion(
  personaId: string,
  versionId: number,
): Promise<PersonaRecord> {
  return requestJSON<PersonaRecord>(`/api/personas/${personaId}/rollback`, {
    method: "POST",
    body: JSON.stringify({ version_id: versionId }),
  });
}

export async function fetchPersonaCorrections(personaId: string): Promise<PersonaCorrectionRecord[]> {
  return requestJSON<PersonaCorrectionRecord[]>(`/api/personas/${personaId}/corrections`);
}

export async function addPersonaCorrection(
  personaId: string,
  payload: PersonaCorrectionPayload,
): Promise<PersonaCorrectionRecord> {
  return requestJSON<PersonaCorrectionRecord>(`/api/personas/${personaId}/corrections`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deletePersonaCorrection(
  personaId: string,
  correctionId: number,
): Promise<{ status: string; deleted_id: number }> {
  return requestJSON<{ status: string; deleted_id: number }>(
    `/api/personas/${personaId}/corrections/${correctionId}`,
    {
      method: "DELETE",
    },
  );
}

export async function togglePersonaCorrection(
  personaId: string,
  correctionId: number,
  isActive: boolean,
): Promise<PersonaCorrectionRecord> {
  return requestJSON<PersonaCorrectionRecord>(
    `/api/personas/${personaId}/corrections/${correctionId}/toggle?is_active=${isActive}`,
    {
      method: "PATCH",
    },
  );
}
