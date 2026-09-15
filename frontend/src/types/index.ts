// Shared frontend type definitions.

/** Public user profile returned by /api/me and auth endpoints. */
export interface Profile {
  id: string;
  email: string;
  nickname: string;
  provider: Provider;
  quota_remaining: number;
  text_requests: number;
  voice_requests: number;
  free_quota_total: number;
  created_at: string;
  is_admin?: boolean;
  status?: "active" | "disabled";
  admin_note?: string;
  avatar_download_url?: string | null;
  avatar_object_key?: string | null;
  chat_background_object_key?: string | null;
  chat_background_download_url?: string | null;
  chat_panel_background_object_key?: string | null;
  chat_panel_background_download_url?: string | null;
}

/** Result of the irreversible account deletion endpoint.
 * The server may add counts or describe asynchronous external cleanup later.
 */
export interface DeleteAccountResponse {
  status: string;
  deleted_counts?: Record<string, number>;
  remote_cleanup?: unknown;
  [key: string]: unknown;
}

export type Provider = "bailian";

/** Persisted per-user voice settings returned by the backend. */
export interface VoiceSettingsRecord {
  speaker: string;
  character_manifest: string;
  updated_at: string;
  voice_clone?: VoiceCloneRecord | null;
}

export interface VoiceCloneRecord {
  voice_id: string;
  object_key: string;
  reference_filename: string;
  reference_size?: number | null;
  reference_duration?: number | null;
  target_model: string;
  created_at: string;
  reference_audio_url?: string | null;
  request_id?: string;
}

export interface VoiceCloneListResponse {
  voice_clones: VoiceCloneRecord[];
  voice_clone: VoiceCloneRecord | null;
}

export interface DeleteVoiceCloneResponse extends VoiceCloneListResponse {
  deleted_voice_id: string;
  speaker: string;
}

/** Persisted conversation record. */
export interface ChatConversationRecord {
  id: string;
  user_id: string;
  title: string;
  provider: Provider;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  avatar_object_key?: string | null;
  avatar_download_url?: string | null;
  last_message?: string | null;
  last_message_at?: string | null;
}

export interface ChatConversationListResponse {
  conversations: ChatConversationRecord[];
}

/** Persisted or pending chat attachment (image / video). */
export interface ChatAttachment {
  id: string;
  kind: "image" | "video";
  object_key: string;
  filename: string;
  content_type: string;
  file_size?: number;
  url?: string;
  download_url?: string;
  uploading?: boolean;
  progress?: number;
  error?: string;
}

/** OpenAI-compatible structured content part for multimodal input. */
export type ContentPart =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string }; min_pixels?: number; max_pixels?: number }
  | { type: "video_url"; video_url: { url: string; fps?: number }; max_pixels?: number };

/** Persisted chat message record. */
export interface ChatMessageRecord {
  speech_turn_id?: string | null;
  id: number;
  conversation_id: string;
  user_id: string;
  role: "user" | "ai" | "system";
  content: string;
  kind: "text" | "voice";
  status: "completed" | "interrupted" | "error";
  audio_duration_ms: number;
  created_at: string;
  attachments?: ChatAttachment[];
  import_meta?: {
    source?: "chat_import";
    speaker_label?: string;
    avatar_object_key?: string;
    avatar_download_url?: string;
  };
}

export interface ChatHistoryResponse {
  conversation: ChatConversationRecord;
  messages: ChatMessageRecord[];
  message?: string;
}

export interface BailianChatResult {
  model?: string;
  content?: string;
}

export interface BailianChatAndTTSResult {
  answer: string;
  audio: {
    model?: string;
    audio_url?: string | null;
    request_id?: string;
  } | null;
  request_id?: string;
  audio_quota_exhausted?: {
    code: "quota_exceeded";
    metric: BillingMetricCode;
    used: number;
    limit: number;
    remaining: number;
    reset_at?: string;
  };
}

export interface BailianStreamEvent {
  type: "text.delta" | "text.done" | "audio.delta" | "audio.url" | "audio.asset" | "audio.error" | "audio.quota_exhausted" | "stream.done" | "error";
  speech_turn_id?: string;
  text?: string;
  audio?: string;
  url?: string;
  message?: string;
  sentence_index?: number;
  sample_rate?: number;
  metric?: BillingMetricCode;
  used?: number;
  reserved?: number;
  limit?: number;
  remaining?: number;
  reset_at?: string;
}

export interface BailianMediaUploadPresign {
  bucket: string;
  region: string;
  object_key: string;
  kind: "image" | "video";
  upload_url: string;
  download_url: string;
  expires_in: number;
  headers: Record<string, string>;
}

export interface MessageTTSResponse {
  audio_url: string;
  request_id?: string;
  voice_id?: string;
  model?: string;
}

export interface ChatImportAttachment {
  id?: number;
  import_id?: number;
  object_key: string;
  filename: string;
  content_type: string;
  file_size?: number;
  image_width?: number;
  image_height?: number;
  sort_order?: number;
  created_at?: string;
  download_url?: string;
  local_preview?: string;
  uploading?: boolean;
  progress?: number;
}

export interface ChatImportMessage {
  id?: number;
  import_id?: number;
  user_id?: string;
  speaker_label: string;
  role_guess: "user" | "other" | "unknown";
  text: string;
  timestamp_text?: string | null;
  sort_order: number;
  confidence: number;
  needs_review: boolean;
  source_attachment_id?: number | null;
  transcript?: string | null;
  media_object_key?: string | null;
  media_kind?: "image" | "video" | "audio" | null;
  media_status?: "missing" | "uploading" | "uploaded" | "ignored" | null;
  media_download_url?: string | null;
  created_at?: string;
}

export interface ChatImportBatch {
  voice_style?: VoiceProfile;
  id: number;
  user_id: string;
  source_type: string;
  status: "processing" | "needs_review" | "confirmed" | "failed";
  timezone: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  confirmed_at?: string | null;
  left_avatar_object_key?: string | null;
  right_avatar_object_key?: string | null;
  left_avatar_download_url?: string | null;
  right_avatar_download_url?: string | null;
  attachments?: ChatImportAttachment[];
  messages?: ChatImportMessage[];
  warnings?: string[];
  attachment_count?: number;
  message_count?: number;
}

export interface ChatImportListResponse {
  batches: ChatImportBatch[];
}

export type PlanCode = "free" | "plus" | "pro";

export interface PlanDefinition {
  code: PlanCode;
  name: string;
  price_cny: number;
  billing_period_days: number;
  limits: PlanLimits;
}

export interface PlanLimits {
  ai_reply: number;
  ai_voice_seconds: number;
  image: number;
  video: number;
  chat_import_batch: number;
  voice_slots: number;
}

export type BillingMetricCode =
  | "ai_reply"
  | "ai_voice_seconds"
  | "image"
  | "video"
  | "chat_import_batch"
  | "voice_slot";

export interface BillingMetric {
  used: number;
  reserved: number;
  limit: number;
  remaining: number;
}

export interface BillingUsage {
  ai_replies: number;
  ai_voice_seconds: number;
  images: number;
  videos: number;
  import_batches: number;
  active_voice_slots: number;
}

export interface BillingSummary {
  plan_code: PlanCode;
  status: "active" | "expired";
  period_start: string;
  period_end: string;
  reset_at?: string;
  access_ends_at?: string;
  renewed_until?: string;
  free_trial_started_at?: string;
  enforcement_mode: "shadow" | "hard";
  metrics: Partial<Record<BillingMetricCode, BillingMetric>>;
  usage?: BillingUsage;
}

export interface BillingChannels {
  ldxp: {
    plus: string | null;
    pro: string | null;
  };
}

export interface SubscriptionGrant {
  id: number;
  user_id: string;
  plan_code: Exclude<PlanCode, "free">;
  period_start: string;
  period_end: string;
  source_channel: string;
  created_at: string;
}

export interface RedemptionResult {
  grant: SubscriptionGrant;
  billing: BillingSummary;
}

// ---------------- Admin & Monitoring Types ----------------

export interface MonitoringSeriesPoint {
  bucket_start: string;
  completed: number;
  failed_or_cancelled: number;
  estimated_cost_cny: number;
}

export interface MonitoringModelCost {
  provider: string;
  model: string;
  requests: number;
  estimated_cost_cny: number;
  telemetry_missing: number;
}

export interface MonitoringAlert {
  code: string;
  severity: "critical" | "warning";
  message: string;
  value: number;
  threshold: number;
}

export interface MonitoringSummary {
  generated_at: string;
  window: {
    hours: number;
    start: string;
    end: string;
  };
  requests: {
    total: number;
    completed: number;
    failed_or_cancelled: number;
    active_reserved: number;
    stale_reserved: number;
    failure_rate_percent: number;
  };
  usage: Record<string, number>;
  provider_usage: {
    llm_prompt_tokens: number;
    llm_completion_tokens: number;
    tts_characters: number;
    missing_llm_requests: number;
    missing_tts_requests: number;
  };
  cost: {
    estimated_cny: number;
    window_budget_cny: number;
    partial: boolean;
    breakdown_cny: {
      llm_input: number;
      llm_output: number;
      tts: number;
    };
    rates: {
      llm_input_per_million_tokens: number;
      llm_output_per_million_tokens: number;
      tts_per_10k_characters: number;
    };
  };
  subscriptions: Array<{
    plan_code: PlanCode;
    status: "active" | "expired";
    count: number;
  }>;
  alerts: MonitoringAlert[];
  series: MonitoringSeriesPoint[];
  models: MonitoringModelCost[];
}

export interface AdminUserCostItem {
  user_id: string;
  email: string;
  nickname: string;
  ai_replies: number;
  input_tokens: number;
  output_tokens: number;
  tts_characters: number;
  tts_seconds: number;
  estimated_cost_cny: number;
  missing_requests: number;
  completeness: "complete" | "partial" | "missing";
}

export interface AdminCostsResponse {
  generated_at: string;
  window: {
    hours: number;
    start: string;
    end: string;
  };
  totals: {
    llm_prompt_tokens: number;
    llm_completion_tokens: number;
    tts_characters: number;
    tts_seconds: number;
    estimated_cost_cny: number;
    partial: boolean;
    missing_requests: number;
  };
  rates: {
    llm_input_per_million_tokens: number;
    llm_output_per_million_tokens: number;
    tts_per_10k_characters: number;
  };
  users: AdminUserCostItem[];
}

export interface AdminTransactionItem {
  id: number;
  user_id: string;
  user_email: string;
  user_nickname: string;
  plan_code: "plus" | "pro";
  source_channel: string;
  redeemed_at: string;
  period_start: string;
  period_end: string;
  status: "active" | "expired" | "revoked";
  status_text: string;
  list_price_cny: number;
  paid_amount_text: string;
}

export interface AdminTransactionsResponse {
  total: number;
  page: number;
  limit: number;
  items: AdminTransactionItem[];
}

export interface AdminUserListItem {
  id: string;
  email: string;
  nickname: string;
  status: "active" | "disabled";
  disabled_at: string | null;
  admin_note: string;
  plan_code: PlanCode;
  plan_status: "active" | "expired";
  period_start: string | null;
  period_end: string | null;
  access_end: string | null;
  cost_7d_cny: number;
  last_active_at: string;
  created_at: string;
}

export interface AdminUsersResponse {
  total: number;
  page: number;
  limit: number;
  users: AdminUserListItem[];
}

export interface AdminUserDetail {
  id: string;
  email: string;
  nickname: string;
  status: "active" | "disabled";
  disabled_at: string | null;
  admin_note: string;
  created_at: string;
  updated_at: string | null;
  last_active_at: string;
  subscription: {
    plan_code: PlanCode;
    status: "active" | "expired";
    period_start: string | null;
    period_end: string | null;
    access_end: string | null;
    free_trial_started_at: string | null;
  };
  voice_settings: {
    speaker: string;
    character_manifest: string;
    settings_json: Record<string, any>;
    updated_at: string | null;
  };
  stats_7d: {
    cost_cny: number;
    ai_replies: number;
    voice_seconds: number;
    images: number;
    videos: number;
    prompt_tokens: number;
    completion_tokens: number;
    tts_characters: number;
    total_messages: number;
  };
}

export interface AdminConversationItem {
  id: string;
  user_id: string;
  title: string;
  provider: string;
  is_pinned: boolean;
  is_archived: boolean;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminMessageItem {
  id: number;
  conversation_id: string;
  user_id: string;
  role: "user" | "ai" | "system";
  content: string;
  kind: "text" | "voice";
  status: "completed" | "interrupted" | "error";
  audio_duration_ms: number;
  attachments: ChatAttachment[];
  created_at: string;
}

// ---------------------------------------------------------------------------
// Persona & Ex-Skill Distillation Types
// ---------------------------------------------------------------------------

export interface PersonaLayer0 {
  naming_rules?: string;
  forbidden_topics?: string[] | string;
  defensive_mechanism?: string;
}

export interface PersonaLayer1 {
  role_description?: string;
  mbti?: string;
  attachment_style?: string;
  core_motivation?: string;
  tags?: string[] | string;
}

export interface VoiceProfile {
  pitch?: number;
  use_defaults?: boolean;
  volume?: number;
  pace?: "slow" | "normal" | "fast";
  pace_mode?: "auto" | "manual";
  emotion_mode?: "auto" | "manual";
  rate?: number;
  emotion?: "calm" | "gentle" | "cheerful" | "playful" | "sad" | "angry";
  instruction?: string;
  sample_rate?: 24000 | 48000;
  presentation?: string;
  age_feel?: string;
  pitch_hint?: string;
  traits?: string[];
  scenario?: string;
  effects?: "off" | "auto" | "manual";
  control_tag?: string;
  effect_tag?: string;
  evidence?: string;
}

export interface PersonaLayer2 {
  catchphrases?: string[] | string;
  punctuation_habits?: Record<string, string> | string;
  frequent_emojis?: string[] | string;
  sentence_rhythm?: string;
  voice_style?: VoiceProfile;
}

export interface PersonaLayer3 {
  joy_expression?: string;
  vulnerability_expression?: string;
  anger_triggers?: string[] | string;
  anger_manifestation?: string;
  repair_path?: string;
}

export interface PersonaLayer4 {
  disagreement_handling?: string;
  stress_response?: string;
}

export interface PersonaStructured {
  layer0_hard_rules?: PersonaLayer0;
  layer1_identity?: PersonaLayer1;
  layer2_expression_dna?: PersonaLayer2;
  layer3_emotional_dynamics?: PersonaLayer3;
  layer4_conflict_patterns?: PersonaLayer4;
  [key: string]: any;
}

export interface PersonaMemories {
  timeline?: Array<{ date?: string; event?: string; details?: string }>;
  inside_jokes?: Array<{ phrase?: string; meaning?: string }>;
  pet_names?: Record<string, string>;
  routines?: Record<string, any>;
  preferences?: {
    dietary_likes?: string[] | string;
    dietary_dislikes?: string[] | string;
    living_habits?: string[] | string;
    wishes?: string[] | string;
    [key: string]: any;
  };
  conflicts?: Array<{ cause?: string; resolution?: string }>;
  [key: string]: any;
}

export interface PersonaRecord {
  id: string;
  user_id: string;
  slug: string;
  name: string;
  avatar_url?: string | null;
  avatar_download_url?: string | null;
  avatar_object_key?: string | null;
  persona: PersonaStructured;
  memories: PersonaMemories;
  voice_id: string;
  compiled_prompt: string;
  status: "draft" | "distilling" | "ready" | "failed";
  source_type: "manual" | "chat_import" | "text_input";
  source_import_ids: number[];
  is_active: boolean;
  is_builtin: boolean;
  active_corrections_count?: number;
  version_count?: number;
  created_at: string;
  updated_at: string;
}

export interface PersonaVersionRecord {
  id: number;
  persona_id: string;
  version_tag: string;
  persona: PersonaStructured;
  memories: PersonaMemories;
  compiled_prompt: string;
  message: string;
  created_at: string;
}

export interface PersonaCorrectionRecord {
  id: number;
  persona_id: string;
  user_id: string;
  correction_type: "linguistic" | "emotional" | "fact" | string;
  user_feedback: string;
  rule_text: string;
  target_layer: string;
  is_active: boolean;
  created_at: string;
}

export interface PersonaCreatePayload {
  name: string;
  slug?: string;
  avatar_url?: string;
  voice_id?: string;
  persona?: PersonaStructured;
  memories?: PersonaMemories;
  source_type?: "manual" | "chat_import" | "text_input";
  source_import_ids?: number[];
  is_active?: boolean;
}

export interface PersonaUpdatePayload {
  avatar_import_id?: number;
  voice_style?: VoiceProfile;
  name?: string;
  slug?: string;
  avatar_url?: string;
  voice_id?: string;
  persona?: PersonaStructured;
  memories?: PersonaMemories;
  compiled_prompt?: string;
  source_import_ids?: number[];
}

export interface PersonaDistillPayload {
  user_descriptions?: string;
  personality_tags?: string[];
  import_ids?: number[];
  raw_chat_text?: string;
}

export interface PersonaCorrectionPayload {
  user_feedback: string;
  correction_type?: "linguistic" | "emotional" | "fact";
  target_layer?: string;
}
