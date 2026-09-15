<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import OrbCanvas from "../components/OrbCanvas.vue";
import AppNav from "../components/AppNav.vue";
import ChatImportDialog from "../components/ChatImportDialog.vue";
import PersonaWorkshopDialog from "../components/PersonaWorkshopDialog.vue";
import DistillWizardDialog from "../components/DistillWizardDialog.vue";
import CorrectionDialog from "../components/CorrectionDialog.vue";
import {
  streamChat,
  streamChatAndTTS,
  createChatConversation,
  updateChatConversation,
  uploadConversationAvatar,
  fetchChatConversations,
  fetchChatMessages,
  upsertChatMessage,
  uploadMediaAttachment,
  synthesizeMessageTTS,
  isQuotaExceededError,
  quotaExceededMessage,
} from "../api";
import { useAuthStore } from "../stores/auth";
import { useVoiceConfigStore } from "../stores/voiceConfig";
import { usePersonaStore } from "../stores/personaStore";
import type { OrbState } from "../composables/useOrb";
import type { BailianStreamEvent, ChatAttachment, ChatConversationRecord, ContentPart, ChatImportBatch } from "../types";
import { PCMStreamPlayer } from "../lib/pcmStreamPlayer";
import { loadWavWithFallback } from "../lib/audioResponse";
import { messageTtsCachePayload } from "../lib/ttsSettings";
import { loadSpeechReplay } from '../lib/speechReplay';
import "../assets/styles/chat.css";

const auth = useAuthStore();
const voice = useVoiceConfigStore();
const personaStore = usePersonaStore();
const avatarInput = ref<HTMLInputElement | null>(null);
const conversationSaving = ref(false);
const conversationEditError = ref('');
const editingConversationId = ref('');
const conversationTitleDraft = ref('');
let avatarConversationId = '';

function chooseConversationAvatar(id: string) {
  if (!id || conversationSaving.value) return;
  avatarConversationId = id;
  avatarInput.value?.click();
}

async function changeConversationAvatar(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file || !avatarConversationId || conversationSaving.value) return;
  const id = avatarConversationId;
  conversationSaving.value = true;
  conversationEditError.value = '';
  try {
    await uploadConversationAvatar(id, file);
    failedConversationAvatar.value = '';
    await loadConversations();
  } catch (error) { conversationEditError.value = (error as Error).message; }
  finally { conversationSaving.value = false; }
}

async function editConversation(conversation: ChatConversationRecord) {
  editingConversationId.value = conversation.id;
  conversationTitleDraft.value = conversation.title;
  conversationEditError.value = '';
  await nextTick();
  document.querySelector<HTMLInputElement>('.conversation-list__title-input')?.focus();
}

async function renameConversation(conversation: ChatConversationRecord) {
  const title = conversationTitleDraft.value.trim();
  if (conversationSaving.value) return;
  if (!title) { conversationEditError.value = '请输入对话标题'; return; }
  if (title === conversation.title) { editingConversationId.value = ''; return; }
  if (title.length > 64) { conversationEditError.value = '标题最多64字'; return; }
  conversationSaving.value = true;
  conversationEditError.value = '';
  try { await updateChatConversation(conversation.id, {title}); await loadConversations(); editingConversationId.value = ''; }
  catch (error) { conversationEditError.value = (error as Error).message; }
  finally { conversationSaving.value = false; }
}

interface Message {
  speechTurnId?: string;
  id: number;
  text: string;
  who: "ai" | "user";
  welcome?: boolean;
  audioUrl?: string;
  audioCached?: boolean;
  audioLoading?: boolean;
  audioPlaying?: boolean;
  audioError?: string;
  attachments?: ChatAttachment[];
  imported?: boolean;
  speakerLabel?: string;
  avatarUrl?: string;
}

const orbState = ref<OrbState>("idle");
const messages = ref<Message[]>([]);
const typing = ref(false);
const voiceReplying = ref(false);
const input = ref("");
const sendDisabled = ref(true);
const statusText = ref("轻触光球，开始说话");
const tapHint = ref("轻触说话");
const placeholder = ref("想说点什么…");
const threadEl = ref<HTMLElement | null>(null);
const inputEl = ref<HTMLTextAreaElement | null>(null);
const fileInputEl = ref<HTMLInputElement | null>(null);
const pendingAttachments = ref<ChatAttachment[]>([]);
const previewImage = ref<string | null>(null);
const importDialogOpen = ref(false);
type MobileView = "conversations" | "chat" | "voice";
const mobileView = ref<MobileView>("chat");
const conversations = ref<ChatConversationRecord[]>([]);
const activeConversationId = ref("");
const chatHeaderTitle = computed(() => conversations.value.find((item) => item.id === activeConversationId.value)?.title || personaStore.activePersonaName);
const failedConversationAvatar = ref('');
const failedAccountAvatar = ref('');
const conversationAvatarUrl = computed(() => {
  const url = conversations.value.find(c => c.id === activeConversationId.value)?.avatar_download_url || '';
  return url === failedConversationAvatar.value ? '' : url;
});
const accountAvatarUrl = computed(() => {
  const url = auth.profile?.avatar_download_url || '';
  return url === failedAccountAvatar.value ? '' : url;
});
const accountAvatarFallback = computed(() => (auth.profile?.nickname || auth.profile?.email || '我').trim().slice(0,1).toUpperCase());

function openNewConversationImport() {
  importDialogOpen.value = true;
}

function openVoiceSettings() {
  if (auth.profile) void voice.open(auth.profile.id, "settings");
}

async function selectChatVoice(event: Event) {
  const speaker = (event.target as HTMLSelectElement).value;
  await voice.save({ speaker, characterManifest: voice.characterManifest });
  statusText.value = "音色已自动切换";
}
function voiceDisplayName(filename:string,index:number) {
  return /^\d{4}(?:年|-)|_trim_/i.test(filename || '') ? `克隆音色 ${index + 1}` : filename || `克隆音色 ${index + 1}`;
}
const orbPanelWidth = ref<string | null>(null);
let stopConversationResize: (() => void) | null = null;

function importConversationTitle(batch: ChatImportBatch) {
  const label = batch.messages?.find((message) => message.role_guess !== "user" && !["对方", "我", "系统消息"].includes(message.speaker_label))?.speaker_label;
  return label || "导入聊天";
}

async function handleImportConfirmed({ batch, target, conversationName }: { batch: ChatImportBatch; target: string; conversationName?: string }) {
  importDialogOpen.value = false;
  let reusedConversation = conversations.value.find(c => c.id === target);
  if (target === "new") {
    const created = await createChatConversation({
      title: conversationName?.trim() || importConversationTitle(batch),
    });
    activeConversationId.value = created.id;
    messages.value = [];
    reusedConversation = undefined;
  } else {
    activeConversationId.value = target;
    await loadHistory(target);
  }
  if (batch.messages && batch.messages.length > 0) {
    for (const m of batch.messages) {
      const who = m.role_guess === "user" ? "user" : "ai";
      const avatarObjectKey = who === "ai" ? batch.left_avatar_object_key || reusedConversation?.avatar_object_key : undefined;
      const avatarUrl = who === "ai" ? batch.left_avatar_download_url || reusedConversation?.avatar_download_url : undefined;
      const msg = addMessage(m.text, who, false, { imported: true, speakerLabel: m.speaker_label, avatarUrl: avatarUrl || undefined });
      await upsertChatMessage({
        id: msg.id,
        conversation_id: activeConversationId.value || undefined,
        role: who,
        content: m.text,
        kind: "text",
        import_meta: {
          source: "chat_import",
          speaker_label: m.speaker_label,
          avatar_object_key: avatarObjectKey || undefined,
        },
      });
    }
    nextTick(scrollBottom);
  }
  await loadConversations();
}

let busy = false;
let voiceActive = false;
let recognition: any = null;
let recognitionStarting = false;
let messageId = Date.now() * 1000;
let activeAudio: HTMLAudioElement | null = null;
let manualAudio: HTMLAudioElement | null = null;
let manualAudioMessageId: number | null = null;
let activeStreamPlayer: PCMStreamPlayer | null = null;
let activeVoiceTurnAbort: AbortController | null = null;
let audioRequestId = 0;
let manualAudioRequestId = 0;
let audioPlaying = false;
let audioCooldownUntil = 0;
// Memory-only session fallback after the server reports exhausted AI-voice quota.
let voiceTextOnly = false;
const messageAudioCache = new Map<number, string>();
const messageAudioCacheKeys = new Map<number, string>();
const messageAudioSourceKeys = new Map<number, string>();
const messageAudioLoads = new Map<number, Promise<string>>();
let messageAudioCacheGeneration = 0;
const MESSAGE_AUDIO_CACHE_NAME = "weiguang-message-audio-v1";
const MESSAGE_AUDIO_CACHE_PREFIX = "https://weiguang.local/audio/";
const MESSAGE_AUDIO_CACHE_MAX_ENTRIES = 30;
const MESSAGE_AUDIO_CACHE_TIMESTAMP = "X-Weiguang-Cached-At";

function addMessage(text: string, who: "ai" | "user", welcome = false, extra: Partial<Message> = {}): Message {
  const msg: Message = { id: ++messageId, text, who, welcome, ...extra };
  messages.value.push(msg);
  nextTick(scrollBottom);
  return messages.value[messages.value.length - 1];
}

function scrollBottom() {
  const el = threadEl.value;
  if (el) el.scrollTop = el.scrollHeight;
}

function setState(state: OrbState) {
  orbState.value = state;
  statusText.value = state === "idle"
    ? "轻触光球，开始说话"
    : state === "listening" ? "正在聆听…"
      : state === "thinking" ? "正在想想…" : "回应中";
  tapHint.value = state === "speaking" ? "轻触打断" : voiceActive ? "轻触结束" : "轻触说话";
}

function showTyping() {
  typing.value = true;
  nextTick(scrollBottom);
}

function hideTyping() {
  typing.value = false;
}

function stopAudio() {
  audioRequestId += 1;
  manualAudioRequestId += 1;
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
    activeAudio = null;
  }
  if (manualAudio) {
    manualAudio.pause();
    manualAudio.currentTime = 0;
    manualAudio = null;
  }
  manualAudioMessageId = null;
  activeStreamPlayer?.stop();
  activeStreamPlayer = null;
  audioPlaying = false;
  audioCooldownUntil = Date.now() + 700;
  messages.value.forEach((item) => {
    item.audioPlaying = false;
    item.audioLoading = false;
  });
}

function abortActiveVoiceTurn(reason = "voice-interrupted") {
  activeVoiceTurnAbort?.abort(reason);
}

function releaseMessageAudioCache() {
  messageAudioCacheGeneration += 1;
  for (const url of messageAudioCache.values()) URL.revokeObjectURL(url);
  messageAudioCache.clear();
  messageAudioCacheKeys.clear();
  messageAudioSourceKeys.clear();
  messageAudioLoads.clear();
}

function getAudioUserId() {
  return auth.profile?.id || "anonymous";
}

function getTtsOptions() {
  return {
    voice: voice.speaker.trim() || "__default__",
    instruction: personaStore.activeTtsInstruction,
    sample_rate: personaStore.activeTtsSampleRate,
    rate: personaStore.activeTtsRate,
    volume: personaStore.activePersona?.persona?.layer2_expression_dna?.voice_style?.volume ?? 50,
    pitch: personaStore.activePersona?.persona?.layer2_expression_dna?.voice_style?.pitch ?? 1,
    use_defaults: personaStore.activePersona?.persona?.layer2_expression_dna?.voice_style?.use_defaults ?? false,
  };
}

function getAudioCachePayload(message: Message, settings = getTtsOptions()) {
  const userId = getAudioUserId();
  return {
    userId,
    payload: message.speechTurnId ? JSON.stringify({version:3,userId,asset:message.speechTurnId}) : messageTtsCachePayload(userId, message.id, message.text, settings),
  };
}

function fallbackAudioCacheDigest(input: string) {
  let hash = 2166136261;
  for (let index = 0; index < input.length; index += 1) {
    hash = Math.imul(hash ^ input.charCodeAt(index), 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

async function getAudioCacheContext(message: Message, settings = getTtsOptions()) {
  const { userId, payload } = getAudioCachePayload(message, settings);
  let digest = "";
  try {
    if (globalThis.crypto?.subtle) {
      const bytes = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
      digest = Array.from(new Uint8Array(bytes), (byte) => byte.toString(16).padStart(2, "0")).join("");
    }
  } catch {
    digest = "";
  }
  if (!digest) digest = fallbackAudioCacheDigest(payload);
  const userPrefix = `${MESSAGE_AUDIO_CACHE_PREFIX}${encodeURIComponent(userId)}/`;
  return {
    payload,
    request: new Request(`${userPrefix}${digest}`),
    userPrefix,
  };
}

function audioContentType(response: Response) {
  return (response.headers.get("content-type") || "")
    .split(";", 1)[0]
    .trim()
    .toLowerCase();
}

async function readPersistentMessageAudio(context: Awaited<ReturnType<typeof getAudioCacheContext>>) {
  if (typeof caches === "undefined") return null;
  try {
    const cache = await caches.open(MESSAGE_AUDIO_CACHE_NAME);
    const response = await cache.match(context.request);
    if (!response) return null;
    const contentType = audioContentType(response);
    if (!response.ok || !contentType.startsWith("audio/")) {
      await cache.delete(context.request);
      return null;
    }
    const blob = await response.blob();
    if (!blob.size) {
      await cache.delete(context.request);
      return null;
    }
    return new Blob([blob], { type: contentType });
  } catch {
    return null;
  }
}

async function trimPersistentMessageAudio(cache: Cache) {
  const entries: Array<{ request: Request; createdAt: number }> = [];
  for (const request of await cache.keys()) {
    if (!request.url.startsWith(MESSAGE_AUDIO_CACHE_PREFIX)) continue;
    const response = await cache.match(request);
    entries.push({
      request,
      createdAt: Number(response?.headers.get(MESSAGE_AUDIO_CACHE_TIMESTAMP) || 0),
    });
  }
  entries.sort((left, right) => left.createdAt - right.createdAt);
  for (const entry of entries.slice(0, Math.max(0, entries.length - MESSAGE_AUDIO_CACHE_MAX_ENTRIES))) {
    await cache.delete(entry.request);
  }
}

async function persistMessageAudio(
  context: Awaited<ReturnType<typeof getAudioCacheContext>>,
  blob: Blob,
  generation: number,
) {
  if (typeof caches === "undefined" || generation !== messageAudioCacheGeneration) return;
  try {
    const cache = await caches.open(MESSAGE_AUDIO_CACHE_NAME);
    if (generation !== messageAudioCacheGeneration) return;
    const headers = new Headers({
      "Content-Type": blob.type || "audio/wav",
      [MESSAGE_AUDIO_CACHE_TIMESTAMP]: String(Date.now()),
    });
    await cache.put(context.request, new Response(blob, { headers }));
    if (generation !== messageAudioCacheGeneration) {
      await cache.delete(context.request);
      return;
    }
    await trimPersistentMessageAudio(cache);
  } catch {
    // Cache Storage is an optimization; a valid network Blob remains playable.
  }
}

async function clearCurrentUserPersistentAudio() {
  if (typeof caches === "undefined") return;
  try {
    const cache = await caches.open(MESSAGE_AUDIO_CACHE_NAME);
    const userPrefix = `${MESSAGE_AUDIO_CACHE_PREFIX}${encodeURIComponent(getAudioUserId())}/`;
    for (const request of await cache.keys()) {
      if (request.url.startsWith(userPrefix)) await cache.delete(request);
    }
  } catch {
    // A storage failure must not block starting a new conversation.
  }
}

function invalidateMessageAudio(message: Message) {
  const cachedUrl = messageAudioCache.get(message.id);
  if (cachedUrl) {
    URL.revokeObjectURL(cachedUrl);
    messageAudioCache.delete(message.id);
  }
  messageAudioCacheKeys.delete(message.id);
  messageAudioSourceKeys.delete(message.id);
  message.audioUrl = undefined;
  message.audioCached = false;
}

function startRecognition() {
  if (!voiceActive || busy || recognition || recognitionStarting) return;
  if (audioPlaying || Date.now() < audioCooldownUntil) {
    window.setTimeout(startRecognition, Math.max(120, audioCooldownUntil - Date.now()));
    return;
  }
  const Recognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!Recognition) {
    addMessage("当前浏览器不支持语音转写，请改用文字输入。", "ai");
    voiceActive = false;
    setState("idle");
    return;
  }
  recognitionStarting = true;
  const current = new Recognition();
  current.lang = "zh-CN";
  current.continuous = false;
  current.interimResults = true;
  current.maxAlternatives = 1;
  current.onstart = () => {
    recognitionStarting = false;
    if (recognition === current) setState("listening");
  };
  current.onresult = (event: any) => {
    let text = "";
    let final = false;
    for (let index = 0; index < event.results.length; index += 1) {
      text += String(event.results[index]?.[0]?.transcript || "");
      final = final || Boolean(event.results[index]?.isFinal);
    }
    if (text.trim() && !final) statusText.value = text.trim();
    if (final && text.trim()) {
      stopRecognition();
      const currentAttachments = [...pendingAttachments.value];
      pendingAttachments.value = [];
      void submitTurn(text.trim(), "voice", currentAttachments.length ? currentAttachments : undefined);
    }
  };
  current.onerror = (event: any) => {
    recognitionStarting = false;
    if (event?.error === "not-allowed" || event?.error === "service-not-allowed") {
      addMessage("浏览器没有授予麦克风或语音识别权限。", "ai");
      voiceActive = false;
      setState("idle");
    }
  };
  current.onend = () => {
    recognitionStarting = false;
    if (recognition === current) recognition = null;
    if (voiceActive && !busy) window.setTimeout(startRecognition, 180);
  };
  recognition = current;
  try {
    current.start();
  } catch {
    recognitionStarting = false;
    recognition = null;
  }
}

function stopRecognition() {
  const current = recognition;
  recognition = null;
  recognitionStarting = false;
  if (current) {
    try { current.stop(); } catch { /* already stopped */ }
  }
}

function buildMessages(currentTurnAttachments?: ChatAttachment[], currentTurnText?: string) {
  const history = messages.value
    .filter((item) => !item.welcome && item.text.trim())
    .map((item) => ({ role: item.who === "user" ? "user" : "assistant", content: item.text }));
  const effectiveSystemPrompt = personaStore.activeCompiledPrompt || voice.characterManifest;
  const result: Array<{ role: string; content: string | ContentPart[] }> = [
    { role: "system", content: effectiveSystemPrompt },
    ...history,
  ];

  if (currentTurnAttachments && currentTurnAttachments.length > 0) {
    const parts: ContentPart[] = [
      { type: "text", text: currentTurnText || "请查看我发送的附件内容" },
    ];
    for (const att of currentTurnAttachments) {
      const url = att.download_url || att.url || "";
      if (att.kind === "image" && url) {
        parts.push({
          type: "image_url",
          image_url: { url },
        });
      } else if (att.kind === "video" && url) {
        parts.push({
          type: "video_url",
          video_url: { url, fps: 2 },
        });
      }
    }
    if (result.length > 1 && result[result.length - 1].role === "user") {
      result[result.length - 1].content = parts;
    }
  }
  return result;
}

function triggerFileSelect() {
  if (busy) return;
  fileInputEl.value?.click();
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files || []);
  target.value = "";
  if (!files.length) return;
  await processIncomingFiles(files);
}

async function processIncomingFiles(files: File[]) {
  const currentImages = pendingAttachments.value.filter((a) => a.kind === "image").length;
  const currentVideos = pendingAttachments.value.filter((a) => a.kind === "video").length;

  for (const file of files) {
    const isVideo = file.type.startsWith("video/") || /\.(mp4|mov|webm)$/i.test(file.name);
    const isImage = file.type.startsWith("image/") || /\.(jpg|jpeg|png|webp)$/i.test(file.name);

    if (!isImage && !isVideo) {
      addMessage(`暂不支持该文件类型: ${file.name}，仅支持图片与常见视频格式。`, "ai");
      continue;
    }

    if (isImage) {
      if (currentImages >= 4) {
        addMessage("每轮对话最多上传 4 张图片。", "ai");
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        addMessage(`图片 ${file.name} 超过 10MB 限制。`, "ai");
        continue;
      }
    } else if (isVideo) {
      if (currentVideos >= 1) {
        addMessage("每轮对话最多上传 1 个视频文件。", "ai");
        continue;
      }
      if (file.size > 50 * 1024 * 1024) {
        addMessage(`视频 ${file.name} 超过 50MB 限制。`, "ai");
        continue;
      }
    }

    const localUrl = URL.createObjectURL(file);
    const attachment: ChatAttachment = {
      id: `pending-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      kind: isImage ? "image" : "video",
      object_key: "",
      filename: file.name,
      content_type: file.type || (isImage ? "image/jpeg" : "video/mp4"),
      file_size: file.size,
      url: localUrl,
      uploading: true,
      progress: 0,
    };
    pendingAttachments.value.push(attachment);
    updateSend();

    uploadMediaAttachment(file, (percent) => {
      attachment.progress = percent;
    })
      .then((uploaded) => {
        attachment.object_key = uploaded.object_key;
        attachment.download_url = uploaded.download_url;
        attachment.uploading = false;
        attachment.progress = 100;
        updateSend();
      })
      .catch((error) => {
        attachment.uploading = false;
        attachment.error = error.message || "上传失败";
        updateSend();
      });
  }
}

function removeAttachment(index: number) {
  const [removed] = pendingAttachments.value.splice(index, 1);
  if (removed?.url && removed.url.startsWith("blob:")) {
    URL.revokeObjectURL(removed.url);
  }
  updateSend();
}

function onInputPaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items;
  if (!items) return;
  const files: File[] = [];
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.kind === "file") {
      const file = item.getAsFile();
      if (file) files.push(file);
    }
  }
  if (files.length) {
    event.preventDefault();
    void processIncomingFiles(files);
  }
}

async function submitTurn(text: string, kind: "text" | "voice", attachments?: ChatAttachment[]) {
  const normalized = text.trim();
  if (!normalized && (!attachments || !attachments.length)) return;
  if (busy) return;
  await auth.ensureReady();
  if (!auth.canRequest()) {
    addMessage("免费请求额度已用完，请在个人中心查看使用记录。", "ai");
    return;
  }
  await voice.ensureReady(auth.profile!.id);
  const ttsOptions = getTtsOptions();
  const userMessage = addMessage(normalized || (attachments?.length ? "（已发送附件）" : ""), "user");
  if (attachments && attachments.length) {
    userMessage.attachments = attachments;
  }
  await upsertChatMessage({
    id: userMessage.id,
    conversation_id: activeConversationId.value || undefined,
    role: "user",
    content: normalized || (attachments?.length ? "（已发送附件）" : ""),
    kind,
    attachments: attachments && attachments.length ? attachments : undefined,
  });
  void loadConversations().catch(() => undefined);
  busy = true;
  updateSend();
  if (kind === "voice") setState("thinking");
  else setState("idle");
  showTyping();
  stopAudio();
  let assistant: Message | null = null;
  let answerText = "";
  let streamedAudio: Blob | null = null;
  let streamError = "";
  let voiceQuotaExhausted = false;
  let enqueueChain = Promise.resolve();
  const wantsVoiceAudio = kind === "voice" && !voiceTextOnly;
  voiceReplying.value = wantsVoiceAudio;
  const turnAbort = wantsVoiceAudio ? new AbortController() : null;
  if (turnAbort) activeVoiceTurnAbort = turnAbort;
  const streamPlayer = wantsVoiceAudio
    ? new PCMStreamPlayer({
        onStart: () => {
          audioPlaying = true;
          setState("speaking");
        },
        onIdle: () => {
          audioPlaying = false;
          audioCooldownUntil = Date.now() + 700;
        },
      })
    : null;
  activeStreamPlayer = streamPlayer;
  try {
    const onStreamEvent = (event: BailianStreamEvent) => {
      if (event.type === "text.delta" && event.text) {
        answerText += event.text;
        if (!assistant) assistant = addMessage(answerText, "ai");
        else assistant.text = answerText;
        hideTyping();
        nextTick(scrollBottom);
      } else if (event.type === "audio.delta" && event.audio && streamPlayer) {
        enqueueChain = enqueueChain
          .then(() => streamPlayer.enqueue(event.audio!, event.sample_rate || 24000))
          .catch((error) => { streamError = (error as Error).message; });
      } else if (event.type === 'audio.asset' && event.speech_turn_id) {
        if (assistant) assistant.speechTurnId = event.speech_turn_id;
      } else if (event.type === "audio.quota_exhausted") {
        voiceQuotaExhausted = true;
        voiceTextOnly = true;
      } else if (event.type === "audio.error" || event.type === "error") {
        streamError = event.message || "百炼流式语音生成失败";
      }
    };
    const messagesPayload = buildMessages(attachments, normalized);
    if (wantsVoiceAudio) {
      await streamChatAndTTS(messagesPayload, {
        adaptiveVoice: true,
        personaId: personaStore.activePersona?.id,
        conversationId: activeConversationId.value,
        ...ttsOptions,
        sampleRate: ttsOptions.sample_rate,
      }, onStreamEvent, turnAbort?.signal);
    } else {
      await streamChat(messagesPayload, onStreamEvent);
    }
    if (streamPlayer) {
      await enqueueChain;
      streamPlayer.finish();
      streamedAudio = !streamError && !voiceQuotaExhausted ? streamPlayer.toWavBlob() : null;
      await streamPlayer.waitForIdle();
    }
    if (!answerText.trim()) throw new Error(streamError || "本次未收到回复，请重试。");
    const answer = answerText.trim();
    if (!assistant) assistant = addMessage(answer, "ai");
    assistant.text = answer;
    await upsertChatMessage({ id: assistant.id, conversation_id: activeConversationId.value || undefined, role: "ai", content: answer, kind, speech_turn_id: assistant.speechTurnId });
    if (streamedAudio) {
      const generation = messageAudioCacheGeneration;
      const context = await getAudioCacheContext(assistant, ttsOptions);
      await persistMessageAudio(context, streamedAudio, generation);
      if (generation === messageAudioCacheGeneration) {
        const url = URL.createObjectURL(streamedAudio);
        messageAudioCache.set(assistant.id, url);
        messageAudioCacheKeys.set(assistant.id, context.payload);
        assistant.audioCached = true;
      }
    }
    if (voiceQuotaExhausted) {
      assistant.audioError = "AI 语音额度已用完，已自动切换为仅文字回答。";
    }
    if (streamError && !answerText) throw new Error(streamError);
    hideTyping();
  } catch (error) {
    streamPlayer?.stop();
    hideTyping();
    if (turnAbort?.signal.aborted) {
      if (turnAbort.signal.reason !== "page-unload" && assistant && answerText.trim()) {
        assistant.text = answerText.trim();
        await upsertChatMessage({ id: assistant.id, conversation_id: activeConversationId.value || undefined, role: "ai", content: assistant.text, kind });
      }
      return;
    }
    if (isQuotaExceededError(error) && error.metric === "ai_voice_seconds") {
      voiceTextOnly = true;
    }
    if (isQuotaExceededError(error) && (error.metric === "image" || error.metric === "video") && attachments?.length) {
      pendingAttachments.value = attachments;
      if (kind === "text") input.value = normalized;
    }
    addMessage(quotaExceededMessage(error) || "百炼 API 暂时不可用。", "ai");
    void auth.fetchBilling();
  } finally {
    void loadConversations().catch(() => undefined);
    voiceReplying.value = false;
    if (activeVoiceTurnAbort === turnAbort) activeVoiceTurnAbort = null;
    if (activeStreamPlayer === streamPlayer) activeStreamPlayer = null;
    busy = false;
    if (voiceActive && kind === "voice") {
      setState(audioPlaying ? "speaking" : "listening");
      startRecognition();
    } else {
      setState("idle");
    }
    updateSend();
  }
}

async function startVoice() {
  if (voiceActive) {
    voiceActive = false;
    abortActiveVoiceTurn();
    stopRecognition();
    stopAudio();
    setState("idle");
    return;
  }
  await auth.ensureReady();
  stopAudio();
  voiceActive = true;
  setState("listening");
  startRecognition();
}

function autoGrow() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

function updateSend() {
  const hasText = input.value.trim().length > 0;
  const hasAttachments = pendingAttachments.value.length > 0;
  const isUploading = pendingAttachments.value.some((a) => a.uploading);
  sendDisabled.value = (!hasText && !hasAttachments) || busy || isUploading;
}

async function sendNow() {
  const text = input.value.trim();
  const currentAttachments = [...pendingAttachments.value];
  if ((!text && !currentAttachments.length) || busy) return;
  if (currentAttachments.some((a) => a.uploading)) {
    addMessage("附件仍在上传中，请稍候…", "ai");
    return;
  }
  input.value = "";
  pendingAttachments.value = [];
  autoGrow();
  updateSend();
  if (voiceActive) {
    voiceActive = false;
    stopRecognition();
  }
  await submitTurn(text || "请查看我发送的附件", "text", currentAttachments.length ? currentAttachments : undefined);
  inputEl.value?.focus();
}

async function loadMessageAudio(message: Message): Promise<string> {
  const pending = messageAudioLoads.get(message.id);
  if (pending) return pending;

  const generation = messageAudioCacheGeneration;
  const load = (async () => {
    await auth.ensureReady();
    if (auth.profile?.id) {
      await voice.ensureReady(auth.profile.id);
    }
    const ttsOptions = getTtsOptions();
    const context = await getAudioCacheContext(message, ttsOptions);
    const cachedUrl = messageAudioCache.get(message.id);
    if (cachedUrl && messageAudioCacheKeys.get(message.id) === context.payload) {
      message.audioCached = true;
      return cachedUrl;
    }
    if (cachedUrl) {
      URL.revokeObjectURL(cachedUrl);
      messageAudioCache.delete(message.id);
      messageAudioCacheKeys.delete(message.id);
    }
    message.audioCached = false;

    const persistentBlob = await readPersistentMessageAudio(context);
    if (persistentBlob) {
      if (generation !== messageAudioCacheGeneration) throw new Error("音频缓存已失效");
      const url = URL.createObjectURL(persistentBlob);
      messageAudioCache.set(message.id, url);
      messageAudioCacheKeys.set(message.id, context.payload);
      message.audioCached = true;
      return url;
    }
    if (generation !== messageAudioCacheGeneration) throw new Error("音频缓存已失效");

    if (message.speechTurnId) {
      const blob = await loadSpeechReplay(message.speechTurnId);
      if (generation !== messageAudioCacheGeneration) throw new Error('音频缓存已失效');
      await persistMessageAudio(context, blob, generation);
      const url = URL.createObjectURL(blob);
      messageAudioCache.set(message.id,url);
      messageAudioCacheKeys.set(message.id,context.payload);
      message.audioCached = true;
      return url;
    }
    let sourceUrl = message.audioUrl;
    if (sourceUrl && messageAudioSourceKeys.get(message.id) && messageAudioSourceKeys.get(message.id) !== context.payload) {
      message.audioUrl = undefined;
      messageAudioSourceKeys.delete(message.id);
      sourceUrl = undefined;
    }
    try {
      const loaded = await loadWavWithFallback(sourceUrl, async () => {
        if (!message.text.trim()) throw new Error("消息没有可朗读内容");
        const res = await synthesizeMessageTTS(message.text, ttsOptions);
        if (!res.audio_url) throw new Error("百炼未返回语音链接");
        return res.audio_url;
      });
      sourceUrl = loaded.url;
      message.audioUrl = sourceUrl;
      messageAudioSourceKeys.set(message.id, context.payload);

      if (generation !== messageAudioCacheGeneration) {
        throw new Error("音频缓存已失效");
      }
      await persistMessageAudio(context, loaded.blob, generation);
      if (generation !== messageAudioCacheGeneration) throw new Error("音频缓存已失效");
      const url = URL.createObjectURL(loaded.blob);
      messageAudioCache.set(message.id, url);
      messageAudioCacheKeys.set(message.id, context.payload);
      message.audioCached = true;
      return url;
    } catch (error) {
      if (sourceUrl && message.audioUrl === sourceUrl) {
        message.audioUrl = undefined;
      }
      message.audioCached = false;
      throw error;
    }
  })();
  messageAudioLoads.set(message.id, load);
  try {
    return await load;
  } finally {
    if (messageAudioLoads.get(message.id) === load) {
      messageAudioLoads.delete(message.id);
    }
  }
}

function isCurrentManualAudio(message: Message, audio: HTMLAudioElement, requestId: number) {
  return requestId === manualAudioRequestId
    && manualAudio === audio
    && manualAudioMessageId === message.id;
}

async function playOrSynthesizeMessage(message: Message) {
  if (voiceActive || orbState.value !== "idle") return;
  if (message.audioLoading || messageAudioLoads.has(message.id)) return;

  if (manualAudio && manualAudioMessageId === message.id) {
    const audio = manualAudio;
    const currentReqId = manualAudioRequestId;
    if (audio.paused) {
      try {
        if (audio.ended) audio.currentTime = 0;
        await audio.play();
        if (isCurrentManualAudio(message, audio, currentReqId)) {
          message.audioLoading = false;
          message.audioPlaying = true;
        }
      } catch (error) {
        if (isCurrentManualAudio(message, audio, currentReqId)) {
          message.audioLoading = false;
          message.audioPlaying = false;
          message.audioError = (error as Error).message || "语音播放失败";
        }
      }
    } else {
      audio.pause();
      message.audioPlaying = false;
    }
    return;
  }

  if (!message.audioUrl && !messageAudioCache.has(message.id) && !message.text.trim()) return;

  stopAudio();
  const currentReqId = manualAudioRequestId;
  message.audioLoading = true;
  message.audioError = undefined;

  try {
    const url = await loadMessageAudio(message);
    if (currentReqId !== manualAudioRequestId) return;

    const audio = new Audio(url);
    manualAudio = audio;
    manualAudioMessageId = message.id;
    audio.onplay = () => {
      if (isCurrentManualAudio(message, audio, currentReqId)) {
        message.audioLoading = false;
        message.audioPlaying = true;
      }
    };
    audio.onpause = () => {
      if (isCurrentManualAudio(message, audio, currentReqId)) {
        message.audioLoading = false;
        message.audioPlaying = false;
      }
    };
    audio.onended = () => {
      if (isCurrentManualAudio(message, audio, currentReqId)) {
        audio.currentTime = 0;
        message.audioLoading = false;
        message.audioPlaying = false;
      }
    };
    audio.onerror = () => {
      if (isCurrentManualAudio(message, audio, currentReqId)) {
        invalidateMessageAudio(message);
        message.audioLoading = false;
        message.audioPlaying = false;
        message.audioError = "语音播放失败";
        manualAudio = null;
        manualAudioMessageId = null;
      }
    };
    await audio.play();
  } catch (error) {
    if (currentReqId === manualAudioRequestId) {
      const name = (error as DOMException).name;
      if (name === "NotSupportedError") invalidateMessageAudio(message);
      message.audioLoading = false;
      message.audioPlaying = false;
      if (isQuotaExceededError(error) && error.metric === "ai_voice_seconds") {
        voiceTextOnly = true;
        void auth.fetchBilling();
      }
      message.audioError = quotaExceededMessage(error) || "语音播放失败";
      manualAudio = null;
      manualAudioMessageId = null;
    }
  }
}

async function downloadMessageAudio(message: Message) {
  if (!message.audioUrl && !message.audioCached && !messageAudioCache.has(message.id) && !messageAudioLoads.has(message.id)) return;
  try {
    const url = await loadMessageAudio(message);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `weiguang-${message.id}.wav`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } catch (error) {
    message.audioError = (error as Error).message || "语音下载失败";
  }
}

function onOrbTap() {
  if (voiceActive && audioPlaying) {
    abortActiveVoiceTurn();
    stopAudio();
    setState("thinking");
    statusText.value = "准备聆听…";
    startRecognition();
    return;
  }
  void startVoice();
}

function onInputKeydown(event: KeyboardEvent) {
  if (event.isComposing || event.keyCode === 229) return;
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    void sendNow();
  }
}

function onSpaceKeydown(event: KeyboardEvent) {
  if (event.code === "Space" && document.activeElement !== inputEl.value && !busy) {
    event.preventDefault();
    void startVoice();
  }
}

function setMobileView(view: MobileView) {
  if (view !== "voice" && (voiceActive || orbState.value !== "idle")) {
    voiceActive = false;
    abortActiveVoiceTurn();
    stopRecognition();
    stopAudio();
    setState("idle");
  }
  mobileView.value = view;
  if (view === "chat") nextTick(scrollBottom);
}

async function handleNewChat() {
  if (busy) return;
  mobileView.value = "chat";
  stopAudio();
  releaseMessageAudioCache();
  await clearCurrentUserPersistentAudio();
  const conversation = await createChatConversation();
  activeConversationId.value = conversation.id;
  messages.value = [];
  await loadConversations();
  addMessage("我在。今天想聊点什么？", "ai", true);
  window.setTimeout(() => addMessage("可以打字，也可以轻触左侧的光球说话。", "ai", true), 700);
}

async function loadConversations() {
  const result = await fetchChatConversations();
  conversations.value = result.conversations;
  if (!activeConversationId.value && conversations.value[0]) activeConversationId.value = conversations.value[0].id;
}

function conversationPreview(conversation: ChatConversationRecord) {
  return (conversation.last_message || "还没有消息").replace(/\s+/g, " ").slice(0, 28);
}

function conversationTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function startOrbPanelResize(event: PointerEvent) {
  const startX = event.clientX;
  const target = event.currentTarget as HTMLElement;
  const startWidth = (target.previousElementSibling as HTMLElement | null)?.getBoundingClientRect().width || 0;
  const move = (moveEvent: PointerEvent) => {
    orbPanelWidth.value = `${Math.min(960, Math.max(280, startWidth + moveEvent.clientX - startX))}px`;
  };
  const stop = () => {
    document.removeEventListener("pointermove", move);
    document.removeEventListener("pointerup", stop);
    stopConversationResize = null;
  };
  stopConversationResize?.();
  stopConversationResize = stop;
  document.addEventListener("pointermove", move);
  document.addEventListener("pointerup", stop);
  event.preventDefault();
}

async function selectConversation(conversationId: string) {
  if (busy) return;
  mobileView.value = "chat";
  if (conversationId === activeConversationId.value) return;
  stopAudio();
  activeConversationId.value = conversationId;
  await loadHistory(conversationId);
}

async function loadHistory(conversationId = activeConversationId.value) {
  try {
    const res = await fetchChatMessages({ limit: 50, conversation_id: conversationId || undefined });
    activeConversationId.value = res.conversation.id;
    if (res.messages.length) {
      messages.value = res.messages.map((m) => {
        if (m.id > messageId) messageId = m.id;
        const legacyImported = m.role === "ai" && m.content.startsWith("【对方】");
        const importMeta = m.import_meta;
        return {
          id: m.id,
          text: legacyImported ? m.content.slice("【对方】".length) : m.content,
          who: m.role === "user" ? "user" : "ai",
          attachments: m.attachments && m.attachments.length ? m.attachments : undefined,
          imported: importMeta?.source === "chat_import" || legacyImported,
          speakerLabel: importMeta?.speaker_label,
          avatarUrl: importMeta?.avatar_download_url,
          speechTurnId: m.speech_turn_id || undefined,
        };
      });
      nextTick(scrollBottom);
      return;
    }
  } catch (error) {
    console.warn("拉取聊天记录失败，使用默认欢迎语:", error);
  }
  addMessage("我在。今天想聊点什么？", "ai", true);
  window.setTimeout(() => addMessage("可以打字，也可以轻触左侧的光球说话。", "ai", true), 700);
}

function onBeforeUnload() {
  abortActiveVoiceTurn("page-unload");
  stopRecognition();
  stopAudio();
  releaseMessageAudioCache();
  stopConversationResize?.();
}

onMounted(async () => {
  const me = await auth.ensureReady();
  if (me?.id) {
    void voice.ensureReady(me.id);
    void auth.fetchBilling();
    void personaStore.loadPersonas();
  }
  setState("idle");
  await loadConversations();
  void loadHistory();
  inputEl.value?.focus();
  window.addEventListener("beforeunload", onBeforeUnload);
  document.addEventListener("keydown", onSpaceKeydown);
});

onBeforeUnmount(() => {
  abortActiveVoiceTurn("page-unload");
  stopRecognition();
  stopAudio();
  releaseMessageAudioCache();
  window.removeEventListener("beforeunload", onBeforeUnload);
  document.removeEventListener("keydown", onSpaceKeydown);
});
</script>

<template>
  <div class="chat-shell" :data-state="orbState" data-provider="bailian">
    <AppNav variant="chat" @new-chat="handleNewChat" @open-import="importDialogOpen = true" />
    <main class="stage" :data-mobile-view="mobileView" :style="orbPanelWidth ? { '--orb-panel-width': orbPanelWidth } : undefined">
      <nav class="mobile-chat-tabs" aria-label="聊天视图" role="tablist">
        <button
          type="button"
          role="tab"
          :aria-selected="mobileView === 'conversations'"
          aria-controls="mobile-conversations-panel"
          class="mobile-chat-tabs__button"
          :class="{ 'is-active': mobileView === 'conversations' }"
          @click="setMobileView('conversations')"
        >会话</button>
        <button
          type="button"
          role="tab"
          :aria-selected="mobileView === 'chat'"
          aria-controls="mobile-chat-panel"
          class="mobile-chat-tabs__button"
          :class="{ 'is-active': mobileView === 'chat' }"
          @click="setMobileView('chat')"
        >聊天</button>
        <button
          type="button"
          role="tab"
          :aria-selected="mobileView === 'voice'"
          aria-controls="mobile-voice-panel"
          class="mobile-chat-tabs__button"
          :class="{ 'is-active': mobileView === 'voice' }"
          @click="setMobileView('voice')"
        >语音</button>
      </nav>
      <aside id="mobile-voice-panel" class="orb-panel" aria-label="语音对话">
        <div class="orb-stage" id="orbStage">
          <OrbCanvas :state="orbState" :particle-count="140" />
          <div class="orb-halo" aria-hidden="true"></div>
          <button class="orb-tap" id="orbTap" aria-label="轻触开始语音对话" @click="onOrbTap"><span class="orb-tap__hint">{{ tapHint }}</span></button>
        </div>
        <p class="status" aria-live="polite">{{ statusText }}</p>

        <!-- Elegant Persona Capsule Badge -->
        <button
          type="button"
          class="orb-persona-badge"
          @click="personaStore.openWorkshop()"
          title="切换或定制角色人设"
        >
          <span class="orb-persona-badge__dot" aria-hidden="true"></span>
          <span class="orb-persona-badge__label">当前陪伴：</span>
          <span class="orb-persona-badge__name">{{ personaStore.activePersonaName }}</span>
          <span class="orb-persona-badge__arrow" aria-hidden="true">›</span>
        </button>

        <!-- Secondary Action Row -->
        <div class="orb-actions-row">
          <button
            type="button"
            class="orb-pill-btn"
            @click="personaStore.openCorrectionDialog()"
            title="调教或纠偏当前回复"
          >
            <span>🎯 调教语气</span>
          </button>
          <label class="orb-voice-select"><span aria-hidden="true">🎙</span><select :value="voice.speaker" aria-label="选择克隆音色" @change="selectChatVoice"><option value="">默认音色</option><option v-for="(clone,index) in voice.voiceClones" :key="clone.voice_id" :value="clone.voice_id">{{ voiceDisplayName(clone.reference_filename,index) }}</option></select></label>
          <button type="button" class="orb-voice-settings" aria-label="音色设置" title="音色设置" @click="openVoiceSettings">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M8 14v6" /></svg>
          </button>
        </div>
      </aside>
      <div class="orb-panel__resizer" role="separator" aria-orientation="vertical" aria-label="调整光球区域宽度" title="拖动调整光球区域宽度" @pointerdown="startOrbPanelResize"><span aria-hidden="true">⋮</span></div>
      <section class="chat-panel">
        <aside id="mobile-conversations-panel" class="conversation-list" aria-label="聊天列表">
          <div class="conversation-list__header"><span class="conversation-list__title">聊天</span><button type="button" title="新建会话并导入聊天截图" @click="openNewConversationImport">＋ 导入</button></div>
          <div v-for="conversation in conversations" :key="conversation.id" class="conversation-list__row">
          <form v-if="editingConversationId === conversation.id" class="conversation-list__editor" @submit.prevent="renameConversation(conversation)" @keydown.esc="editingConversationId = ''">
            <button type="button" class="conversation-list__avatar-action" :disabled="conversationSaving" aria-label="更换会话头像" @click="chooseConversationAvatar(conversation.id)">
              <img v-if="conversation.avatar_download_url" :src="conversation.avatar_download_url" class="conversation-list__avatar" alt="会话头像" />
              <span v-else class="conversation-list__avatar conversation-list__avatar--fallback">{{ conversation.title.slice(0, 1) }}</span>
              <span>更换头像</span>
            </button>
            <input v-model="conversationTitleDraft" class="conversation-list__title-input" aria-label="对话标题" maxlength="64" :disabled="conversationSaving" />
            <div class="conversation-list__edit-actions"><button type="submit" :disabled="conversationSaving">保存标题</button><button type="button" :disabled="conversationSaving" @click="editingConversationId = ''">收起</button></div>
            <small>头像选择后立即保存</small>
            <p v-if="conversationEditError" role="alert">{{ conversationEditError }}</p>
          </form>
          <template v-else>
          <button
            type="button"
            class="conversation-list__item"
            :class="{ 'is-active': conversation.id === activeConversationId }"
            :aria-current="conversation.id === activeConversationId ? 'page' : undefined"
            @click="selectConversation(conversation.id)"
          >
            <img v-if="conversation.avatar_download_url" :src="conversation.avatar_download_url" class="conversation-list__avatar" alt="会话头像" />
            <span v-else class="conversation-list__avatar conversation-list__avatar--fallback" aria-hidden="true">{{ conversation.title.slice(0, 1) }}</span>
            <span class="conversation-list__copy">
              <span class="conversation-list__name">{{ conversation.title }}</span>
              <span class="conversation-list__preview">{{ conversationPreview(conversation) }}</span>
            </span>
            <time class="conversation-list__time">{{ conversationTime(conversation.last_message_at || conversation.updated_at) }}</time>
          </button>
          <button type="button" class="conversation-list__rename" :aria-label="`编辑对话：${conversation.title}`" title="编辑标题和头像" :disabled="conversationSaving" @click="editConversation(conversation)">✎</button>
          </template>
          </div>
        </aside>
        <div id="mobile-chat-panel" class="chat-panel__main">
        <h1 class="chat-page-title">{{ chatHeaderTitle }}</h1>
        <input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/webp" hidden @change="changeConversationAvatar" />
        <div class="thread" ref="threadEl" aria-live="polite">
          <div class="thread__inner">
            <div v-for="msg in messages" :key="msg.id" class="msg" :class="['msg--' + msg.who, { 'msg--welcome': msg.welcome, 'msg--imported': msg.imported }]">
              <template v-if="msg.who === 'user'">
                <img v-if="accountAvatarUrl" :src="accountAvatarUrl" class="msg__avatar" alt="我的账号头像" @error="failedAccountAvatar = accountAvatarUrl" />
                <span v-else class="msg__avatar msg__avatar--fallback msg__avatar--user" aria-hidden="true">{{ accountAvatarFallback }}</span>
              </template>
              <template v-else>
                <img v-if="conversationAvatarUrl || msg.avatarUrl" :src="conversationAvatarUrl || msg.avatarUrl" class="msg__avatar" alt="本会话的 AI 头像" @error="failedConversationAvatar = conversationAvatarUrl" />
                <span v-else class="msg__avatar msg__avatar--fallback" aria-hidden="true">{{ personaStore.activePersonaName.slice(0, 1) }}</span>
              </template>
              <div class="msg__body">
              <span v-if="false" class="msg__who">{{ personaStore.activePersonaName }} · AI</span>
              <span v-else-if="msg.imported && msg.speakerLabel && msg.speakerLabel !== '对方' && msg.speakerLabel !== '我'" class="msg__who">{{ msg.speakerLabel }}</span>
              <!-- Attachments display -->
              <div v-if="msg.attachments && msg.attachments.length" class="msg__attachments">
                <div v-for="(att, idx) in msg.attachments" :key="att.id || idx" class="msg__attachment-item">
                  <img
                    v-if="att.kind === 'image'"
                    :src="att.download_url || att.url"
                    :alt="att.filename"
                    class="msg__image-thumb"
                    loading="lazy"
                    @click="previewImage = att.download_url || att.url || null"
                  />
                  <div v-else-if="att.kind === 'video'" class="msg__video-wrap">
                    <video :src="att.download_url || att.url" controls class="msg__video-player" preload="metadata"></video>
                  </div>
                </div>
              </div>
              <span v-if="msg.text" class="msg__text">{{ msg.text }}</span>
              <button
                v-if="msg.who === 'ai' && !voiceReplying && orbState === 'idle'"
                type="button"
                class="msg__audio"
                :class="{ 'is-active': msg.audioPlaying, 'is-loading': msg.audioLoading }"
                :aria-label="msg.audioPlaying ? '暂停播放这条消息' : '朗读这条消息'"
                :title="msg.audioPlaying ? '暂停播放' : '朗读语音'"
                @click="playOrSynthesizeMessage(msg)"
              >
                <span v-if="msg.audioLoading" class="msg__audio-loader">
                  <i></i><i></i><i></i><i></i>
                </span>
                <span v-else aria-hidden="true">{{ msg.audioPlaying ? '■' : '▶' }}</span>
              </button>
              <button
                v-if="msg.who === 'ai' && !msg.imported"
                type="button"
                class="msg__audio"
                title="调教此回复 / 动态纠偏"
                aria-label="调教此回复"
                @click="personaStore.openCorrectionDialog()"
              >
                <span aria-hidden="true">🎯</span>
              </button>
              <button v-if="msg.audioUrl || msg.audioCached" type="button" class="msg__audio msg__audio-save" aria-label="保存这条语音" title="保存语音" @click.stop="downloadMessageAudio(msg)"><span aria-hidden="true">↓</span></button>
              <span v-if="msg.audioError" class="msg__audio-error">{{ msg.audioError }}</span>
              </div>
            </div>
            <div v-if="typing" class="typing" key="typing"><span class="typing__dot"></span><span class="typing__dot"></span><span class="typing__dot"></span></div>
          </div>
        </div>
        <div class="composer">
          <div class="composer__inner">
            <!-- Pending Attachments Bar -->
            <div v-if="pendingAttachments.length" class="composer__attachments">
              <div
                v-for="(att, idx) in pendingAttachments"
                :key="att.id"
                class="attachment-pill"
                :class="{ 'is-uploading': att.uploading, 'is-error': Boolean(att.error) }"
              >
                <img v-if="att.kind === 'image' && att.url" :src="att.url" class="attachment-pill__thumb" alt="预览" />
                <span v-else class="attachment-pill__icon" aria-hidden="true">🎬</span>
                <span class="attachment-pill__name">{{ att.filename }}</span>
                <span v-if="att.uploading" class="attachment-pill__status">{{ att.progress }}%</span>
                <span v-else-if="att.error" class="attachment-pill__status is-error" :title="att.error">失败</span>
                <button type="button" class="attachment-pill__remove" title="移除此附件" aria-label="移除此附件" @click="removeAttachment(idx)">×</button>
              </div>
            </div>
            <span class="composer__line" aria-hidden="true"></span>
            <div class="composer__row">
              <button type="button" class="composer__attach-btn" title="添加图片或视频" aria-label="添加图片或视频" @click="triggerFileSelect">
                <span class="composer__attach-icon" aria-hidden="true">📎</span>
              </button>
              <input
                ref="fileInputEl"
                type="file"
                accept="image/png,image/jpeg,image/webp,video/mp4,video/quicktime,video/webm"
                multiple
                style="display: none"
                @change="handleFileChange"
              />
              <textarea
                ref="inputEl"
                v-model="input"
                class="composer__input"
                rows="1"
                maxlength="2000"
                :placeholder="placeholder"
                aria-label="输入你想说的话，支持粘贴图片"
                @input="autoGrow(); updateSend()"
                @keydown="onInputKeydown"
                @paste="onInputPaste"
              ></textarea>
              <button class="composer__send" aria-label="发送" :disabled="sendDisabled" @click="sendNow"><span class="composer__send-icon" aria-hidden="true">↑</span></button>
            </div>
            <span v-if="input.length >= 1600" class="composer__count" :class="{ 'is-limit': input.length >= 2000 }" aria-live="polite">{{ input.length }} / 2000</span>
          </div>
        </div>
        </div>
      </section>
    </main>

    <!-- Fullscreen Image Preview Lightbox -->
    <div v-if="previewImage" class="image-modal" @click="previewImage = null">
      <div class="image-modal__backdrop"></div>
      <div class="image-modal__content">
        <img :src="previewImage" class="image-modal__img" alt="查看大图" />
        <button type="button" class="image-modal__close" aria-label="关闭预览" @click="previewImage = null">×</button>
      </div>
    </div>

    <!-- Chat Screenshot Import Dialog -->
    <ChatImportDialog
      :open="importDialogOpen"
      :conversations="conversations"
      :active-conversation-id="activeConversationId"
      prefer-new
      @close="importDialogOpen = false"
      @confirmed="handleImportConfirmed"
    />

    <!-- Ex-Skill Persona Workshop & Distillation Dialogs -->
    <PersonaWorkshopDialog />
    <DistillWizardDialog />
    <CorrectionDialog />
  </div>
</template>
