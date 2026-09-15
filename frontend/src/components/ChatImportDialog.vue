<script setup lang="ts">
import { computed, nextTick, ref, watch, onMounted, onBeforeUnmount } from "vue";
import type { ChatConversationRecord, ChatImportAttachment, ChatImportBatch, ChatImportMessage } from "../types";
import {
  uploadScreenshotForImport,
  createChatImport,
  quotaExceededMessage,
  updateChatImport,
  confirmChatImport,
  presignImportMessageMedia,
  confirmImportMessageMedia,
  updateImportMessageTranscript,
} from "../api";
import { useAuthStore } from "../stores/auth";
import { usePersonaStore } from "../stores/personaStore";
import type { VoiceProfile } from '../types';
import VoiceProfileForm from './VoiceProfileForm.vue';

const props = defineProps<{
  open: boolean;
  conversations: ChatConversationRecord[];
  activeConversationId: string;
  preferNew?: boolean;
}>();

const auth = useAuthStore();
const personaStore = usePersonaStore();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "confirmed", payload: { batch: ChatImportBatch; target: string; conversationName?: string }): void;
}>();

const dialogRef = ref<HTMLDialogElement | null>(null);
const step = ref<"upload" | "processing" | "review" | "success">("upload");
const selectedFiles = ref<File[]>([]);
const attachments = ref<ChatImportAttachment[]>([]);
const currentBatch = ref<ChatImportBatch | null>(null);
const messages = ref<ChatImportMessage[]>([]);
const voiceProfile = ref<VoiceProfile>({});
const applyVoiceToCurrentPersona = ref(false);
const appliedVoiceNotice = ref("");
const warnings = ref<string[]>([]);
const activeAttachmentIndex = ref(0);
const uploading = ref(false);
const processingText = ref("正在上传截图并由 Qwen3.5-Flash 进行视觉提取…");
const errorMessage = ref("");
const saving = ref(false);
const messageListEl = ref<HTMLElement | null>(null);
const leftAvatarInputEl = ref<HTMLInputElement | null>(null);
const avatarUploading = ref<"left" | null>(null);
const importTarget = ref("new");
const newConversationName = ref("");
const targetConversation = computed(() => (props.conversations || []).find(c => c.id === importTarget.value));
const isAutoDistilling = ref(false);
const autoDistillError = ref("");
const closeLocked = computed(() => uploading.value || step.value === "processing" || saving.value || isAutoDistilling.value || avatarUploading.value !== null);

const isPreviewOpen = ref(false);
const zoomLevel = ref(1);

const activeAttachment = computed(() => attachments.value[activeAttachmentIndex.value] || null);
const visibleMessages = computed(() => {
  const attachmentId = activeAttachment.value?.id;
  if (attachmentId == null) return messages.value;
  return messages.value.filter((message) => message.source_attachment_id === attachmentId);
});

function openImagePreview(index?: number) {
  if (typeof index === "number" && index >= 0 && index < attachments.value.length) {
    activeAttachmentIndex.value = index;
  }
  zoomLevel.value = 1;
  isPreviewOpen.value = true;
}

function closeImagePreview() {
  isPreviewOpen.value = false;
  zoomLevel.value = 1;
}

function zoomIn() {
  if (zoomLevel.value < 3.0) {
    zoomLevel.value = Math.min(3.0, +(zoomLevel.value + 0.25).toFixed(2));
  }
}

function zoomOut() {
  if (zoomLevel.value > 0.5) {
    zoomLevel.value = Math.max(0.5, +(zoomLevel.value - 0.25).toFixed(2));
  }
}

function resetZoom() {
  zoomLevel.value = 1;
}

function prevAttachment() {
  if (activeAttachmentIndex.value > 0) {
    activeAttachmentIndex.value--;
    zoomLevel.value = 1;
  }
}

function nextAttachment() {
  if (activeAttachmentIndex.value < attachments.value.length - 1) {
    activeAttachmentIndex.value++;
    zoomLevel.value = 1;
  }
}

function selectAttachment(index: number) {
  if (index < 0 || index >= attachments.value.length) return;
  activeAttachmentIndex.value = index;
  zoomLevel.value = 1;
  nextTick(() => messageListEl.value?.scrollTo({ top: 0, behavior: "smooth" }));
}

function visibleMessageIndex(message: ChatImportMessage): number {
  return visibleMessages.value.indexOf(message);
}

function onLightboxKeydown(e: KeyboardEvent) {
  if (!isPreviewOpen.value) return;
  e.preventDefault();
  e.stopPropagation();
  if (e.key === "Escape") {
    closeImagePreview();
  } else if (e.key === "ArrowLeft") {
    prevAttachment();
  } else if (e.key === "ArrowRight") {
    nextAttachment();
  } else if (e.key === "+" || e.key === "=") {
    zoomIn();
  } else if (e.key === "-") {
    zoomOut();
  }
}

function syncOpen() {
  const el = dialogRef.value;
  if (!el) return;
  if (props.open && !el.open) {
    resetState();
    el.showModal();
  } else if (!props.open && el.open) {
    el.close();
  }
}

watch(() => props.open, syncOpen);
watch(dialogRef, syncOpen);

function resetState() {
  step.value = "upload";
  selectedFiles.value = [];
  attachments.value = [];
  currentBatch.value = null;
  voiceProfile.value = {};
  applyVoiceToCurrentPersona.value = Boolean(personaStore.activePersona);
  appliedVoiceNotice.value = "";
  messages.value = [];
  warnings.value = [];
  activeAttachmentIndex.value = 0;
  uploading.value = false;
  errorMessage.value = "";
  saving.value = false;
  avatarUploading.value = null;
  importTarget.value = props.preferNew ? "new" : props.activeConversationId || props.conversations?.[0]?.id || "new";
  newConversationName.value = "";
  isAutoDistilling.value = false;
  autoDistillError.value = "";
}

function handleClose() {
  if (closeLocked.value) return;
  emit("close");
}

function handleCancel(event: Event) {
  if (isPreviewOpen.value) {
    event.preventDefault();
    closeImagePreview();
  } else if (closeLocked.value) {
    event.preventDefault();
  }
}

function onFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) return;
  addFiles(Array.from(input.files));
  input.value = "";
}

function onDrop(event: DragEvent) {
  event.preventDefault();
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files));
  }
}

function addFiles(files: File[]) {
  const imageFiles = files.filter((f) => f.type.startsWith("image/"));
  if (imageFiles.length === 0) {
    errorMessage.value = "请选择图片格式的聊天截图（JPG/PNG/WEBP）。";
    return;
  }
  errorMessage.value = "";
  const total = [...selectedFiles.value, ...imageFiles];
  if (total.length > 10) {
    errorMessage.value = "一次最多支持上传 10 张截图，已截取前 10 张。";
    selectedFiles.value = total.slice(0, 10);
  } else {
    selectedFiles.value = total;
  }
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1);
}

function formatBytes(bytes?: number): string {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function startExtraction() {
  if (uploading.value) return;
  if (selectedFiles.value.length === 0) {
    errorMessage.value = "请先选择聊天截图。";
    return;
  }
  step.value = "processing";
  uploading.value = true;
  errorMessage.value = "";
  processingText.value = "正在检查可用额度…";

  try {
    const billing = await auth.fetchBilling();
    if (!billing) {
      step.value = "upload";
      errorMessage.value = "暂时无法读取可用额度，请确认服务连接和登录状态后重试。";
      return;
    }
    const importMetric = billing.metrics?.chat_import_batch;
    if (importMetric && importMetric.remaining <= 0) {
      step.value = "upload";
      errorMessage.value = "本期截图导入批次已用完，请在额度重置后再试。";
      return;
    }
    const uploadedAttachments: ChatImportAttachment[] = [];
    for (let i = 0; i < selectedFiles.value.length; i++) {
      const file = selectedFiles.value[i];
      processingText.value = `正在上传截图 (${i + 1}/${selectedFiles.value.length})：${file.name}…`;
      const att = await uploadScreenshotForImport(file);
      att.sort_order = i;
      uploadedAttachments.push(att);
    }
    attachments.value = uploadedAttachments;

    processingText.value = "截图上传完成，Qwen3.5-Flash 正在进行视觉结构化理解与气泡识别…";
    const batch = await createChatImport({
      attachments: uploadedAttachments.map((a, idx) => ({
        object_key: a.object_key,
        filename: a.filename,
        content_type: a.content_type,
        file_size: a.file_size,
        sort_order: idx,
      })),
      source_type: "wechat_screenshot",
      timezone: "Asia/Shanghai",
    });

    const localByObjectKey = new Map(uploadedAttachments.map((attachment) => [attachment.object_key, attachment]));
    attachments.value = (batch.attachments?.length ? batch.attachments : uploadedAttachments).map((attachment) => ({
      ...attachment,
      local_preview: localByObjectKey.get(attachment.object_key)?.local_preview || attachment.local_preview,
      download_url: attachment.download_url || localByObjectKey.get(attachment.object_key)?.download_url,
    }));
    activeAttachmentIndex.value = 0;
    currentBatch.value = batch;
    voiceProfile.value = batch.voice_style || {};
    messages.value = batch.messages || [];
    newConversationName.value = messages.value.find((message) => message.role_guess !== "user" && !["对方", "我", "系统消息"].includes(message.speaker_label))?.speaker_label || "";
    warnings.value = batch.warnings || [];
    step.value = "review";
  } catch (error) {
    step.value = "upload";
    errorMessage.value = quotaExceededMessage(error) || "截图提取失败，请重试。";
  } finally {
    uploading.value = false;
  }
}

function toggleRole(msg: ChatImportMessage) {
  if (msg.role_guess === "user") {
    msg.role_guess = "other";
    if (msg.speaker_label === "我") msg.speaker_label = "对方";
  } else {
    msg.role_guess = "user";
    if (msg.speaker_label === "对方") msg.speaker_label = "我";
  }
}

function deleteMessage(message: ChatImportMessage) {
  const index = messages.value.indexOf(message);
  if (index >= 0) messages.value.splice(index, 1);
}

function moveMessage(message: ChatImportMessage, direction: "up" | "down") {
  const index = messages.value.indexOf(message);
  if (index < 0) return;
  const visibleIndex = visibleMessageIndex(message);
  const neighbor = direction === "up"
    ? visibleMessages.value[visibleIndex - 1]
    : visibleMessages.value[visibleIndex + 1];
  if (!neighbor) return;
  const neighborIndex = messages.value.indexOf(neighbor);
  if (neighborIndex < 0) return;
  const temp = messages.value[index];
  messages.value[index] = messages.value[neighborIndex];
  messages.value[neighborIndex] = temp;
  if (index !== neighborIndex) {
    messages.value[index].sort_order = index + 1;
    messages.value[neighborIndex].sort_order = neighborIndex + 1;
  }
  messages.value.forEach((m, idx) => (m.sort_order = idx + 1));
}

async function handleSupplementMedia(msg: ChatImportMessage, mediaKind: "image" | "video") {
  if (!currentBatch.value || !msg.id) return;
  const input = document.createElement("input");
  input.type = "file";
  input.accept = mediaKind === "image" ? "image/*" : "video/*";
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;
    try {
      msg.media_status = "uploading";
      const presign = await presignImportMessageMedia(currentBatch.value!.id, msg.id!, file, mediaKind);
      await fetch(presign.upload_url, {
        method: "PUT",
        headers: presign.headers,
        body: file,
      });
      const updated = await confirmImportMessageMedia(
        currentBatch.value!.id,
        msg.id!,
        presign.object_key,
        mediaKind,
      );
      msg.media_object_key = updated.media_object_key;
      msg.media_status = updated.media_status;
      msg.media_download_url = updated.media_download_url || URL.createObjectURL(file);
      msg.needs_review = false;
    } catch (err) {
      msg.media_status = "missing";
      alert(`媒体补充上传失败: ${(err as Error).message}`);
    }
  };
  input.click();
}

function ignoreMedia(msg: ChatImportMessage) {
  msg.media_status = "ignored";
  msg.needs_review = false;
}

async function saveTranscript(msg: ChatImportMessage) {
  if (!currentBatch.value || !msg.id || !msg.transcript?.trim()) return;
  try {
    const updated = await updateImportMessageTranscript(
      currentBatch.value.id,
      msg.id,
      msg.transcript.trim(),
    );
    msg.text = updated.text;
    msg.transcript = updated.transcript;
    msg.needs_review = false;
  } catch (err) {
    alert(`语音转写保存失败: ${(err as Error).message}`);
  }
}

async function handleSaveReview() {
  if (!currentBatch.value) return false;
  saving.value = true;
  errorMessage.value = "";
  try {
    messages.value.forEach((m, idx) => (m.sort_order = idx + 1));
    const batch = await updateChatImport(currentBatch.value.id, messages.value, { voice_style: voiceProfile.value });
    currentBatch.value = batch;
    messages.value = batch.messages || [];
    return true;
  } catch (err) {
    errorMessage.value = (err as Error).message || "保存修改失败";
    return false;
  } finally {
    isAutoDistilling.value = false;
    saving.value = false;
  }
}

function avatarUrl(side: "left" | "right") {
  return currentBatch.value?.[`${side}_avatar_download_url`] || undefined;
}

function chooseAvatar() {
  leftAvatarInputEl.value?.click();
}

async function uploadAvatar(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file || !currentBatch.value) return;
  avatarUploading.value = "left";
  errorMessage.value = "";
  try {
    const uploaded = await uploadScreenshotForImport(file);
    const batch = await updateChatImport(currentBatch.value.id, messages.value, { left_avatar_object_key: uploaded.object_key });
    currentBatch.value = batch;
    messages.value = batch.messages || messages.value;
  } catch (error) {
    errorMessage.value = (error as Error).message || "头像上传失败，请重试。";
  } finally {
    avatarUploading.value = null;
  }
}

async function handleConfirmImport() {
  if (!currentBatch.value) return;
  if (importTarget.value === "new" && !newConversationName.value.trim()) {
    errorMessage.value = "请填写当前对话人的网名。";
    return;
  }
  const targetPersona = applyVoiceToCurrentPersona.value ? personaStore.activePersona : null;
  if (applyVoiceToCurrentPersona.value && !targetPersona) {
    errorMessage.value = "当前没有可应用的角色，请先选择角色。";
    return;
  }
  const voiceStyleSnapshot = JSON.parse(JSON.stringify(voiceProfile.value));
  saving.value = true;
  errorMessage.value = "";
  try {
    if (!await handleSaveReview()) return;
    saving.value = true;
    if (targetPersona) {
      await personaStore.savePersona(targetPersona.id, {
        ...(applyVoiceToCurrentPersona.value ? { voice_style: voiceStyleSnapshot } : {}),
      });
      appliedVoiceNotice.value = `所选设置已应用到「${targetPersona.name}」。`;
    }
    const confirmed = await confirmChatImport(currentBatch.value.id, {
      save_conversation: true,
      extract_memories: false,
    });
    isAutoDistilling.value = true;
    await personaStore.autoApplyImport(currentBatch.value.id);
    isAutoDistilling.value = false;
    currentBatch.value = confirmed;
    step.value = "success";
    emit("confirmed", { batch: confirmed, target: importTarget.value, conversationName: newConversationName.value.trim() || undefined });
  } catch (err) {
    errorMessage.value = (err as Error).message || "确认导入失败";
  } finally {
    saving.value = false;
  }
}

async function handleAutoDistill() {
  if (!currentBatch.value?.id) return;
  isAutoDistilling.value = true;
  autoDistillError.value = "";
  try {
    if (step.value === "review") {
      if (!await handleSaveReview()) return;
    }
    await personaStore.autoDistillFromImport(currentBatch.value.id);
    emit("close"); // Successful completion may close while the busy flag is still set.
  } catch (err: any) {
    autoDistillError.value = err.message || "自动提炼角色人设失败，请稍后重试";
  } finally {
    isAutoDistilling.value = false;
  }
}

function handleDistillFromBatch() {
  handleAutoDistill();
}

onMounted(() => {
  window.addEventListener("keydown", onLightboxKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onLightboxKeydown);
  dialogRef.value?.close();
});
</script>

<template>
  <dialog ref="dialogRef" class="chat-import-dialog" @close="handleClose" @cancel="handleCancel">
    <div class="chat-import__panel">
      <header class="chat-import__header">
        <div class="chat-import__header-title">
          <h2>导入聊天截图</h2>
          <span class="chat-import__tag">Qwen3.5-Flash 视觉理解</span>
        </div>
        <button type="button" class="chat-import__close" aria-label="关闭" :disabled="closeLocked" :title="closeLocked ? '正在处理，请等待完成' : '关闭'" @click="handleClose">×</button>
      </header>

      <div class="chat-import__body">
        <!-- STEP 1: Upload Screenshots -->
        <div v-if="step === 'upload'" class="import-step import-step--upload">
          <div
            class="import-dropzone"
            @dragover.prevent
            @drop="onDrop"
          >
            <div class="import-dropzone__icon">📸</div>
            <div class="import-dropzone__title">拖拽聊天截图到此处，或点击选择</div>
            <div class="import-dropzone__hint">支持微信、短信、IM 截图（PNG / JPG / WEBP，最多 10 张，每张 ≤ 10MB）</div>
            <label class="import-file-btn">
              <span>选择截图文件</span>
              <input type="file" multiple accept="image/*" class="is-hidden" @change="onFileSelect" />
            </label>
          </div>

          <div class="import-long-image-warning" role="note">
            <span class="import-long-image-warning__icon">⚠️</span>
            <div><strong>识别提示：</strong>禁止上传长截图。长截图容易因内容过长、缩放后文字过小或请求超时而识别失败，请先裁剪成多张正常比例的聊天截图再上传。</div>
          </div>

          <!-- Preview thumbnails -->
          <div v-if="selectedFiles.length > 0" class="import-preview-list">
            <div class="import-preview-list__title">
              <span>已选截图 ({{ selectedFiles.length }}/10)</span>
            </div>
            <div class="import-preview-grid">
              <div v-for="(file, idx) in selectedFiles" :key="idx" class="import-preview-card">
                <span class="import-preview-card__index">{{ idx + 1 }}</span>
                <div class="import-preview-card__info">
                  <div class="import-preview-card__name">{{ file.name }}</div>
                  <div class="import-preview-card__size">{{ formatBytes(file.size) }}</div>
                </div>
                <button
                  type="button"
                  class="import-preview-card__remove"
                  title="移除此截图"
                  @click="removeFile(idx)"
                >
                  ×
                </button>
              </div>
            </div>
          </div>

          <!-- Privacy Note -->
          <div class="import-privacy-banner">
            <span class="import-privacy-banner__icon">🔒</span>
            <div class="import-privacy-banner__text">
              <strong>隐私与安全声明：</strong>截图可能包含姓名、头像、联系方式等对话信息。截图经由私有 OSS 短期加密存储，只有您审核确认的内容才会进入微光；在确认前您可以删除或修改任何消息。
            </div>
          </div>

          <div v-if="errorMessage" class="import-error-banner">{{ errorMessage }}</div>

          <div class="import-footer-actions">
            <button type="button" class="btn-cancel" @click="handleClose">取消</button>
            <button
              type="button"
              class="btn-primary"
              :disabled="selectedFiles.length === 0 || uploading"
              @click="startExtraction"
            >
              开始提取对话记录
            </button>
          </div>
        </div>

        <!-- STEP 2: Processing -->
        <div v-else-if="step === 'processing'" class="import-step import-step--processing">
          <div class="import-spinner-wrap">
            <div class="import-spinner"></div>
            <div class="import-wave">
              <i></i><i></i><i></i><i></i><i></i>
            </div>
          </div>
          <h3>AI 视觉提取中…</h3>
          <p class="import-processing-desc">{{ processingText }}</p>
        </div>

        <!-- STEP 3: Review & Edit -->
        <div v-else-if="step === 'review'" class="import-step import-step--review">
          <div class="import-review-toolbar">
            <div class="import-review-stats">
              <span>共提取 <strong>{{ messages.length }}</strong> 条消息</span>
              <span v-if="warnings.length > 0" class="import-warning-badge">有 {{ warnings.length }} 项识别提示</span>
            </div>
            <div class="import-review-actions">
              <button type="button" class="btn-sm" :disabled="saving || isAutoDistilling" @click="step = 'upload'">重新上传</button>
              <button v-if="false" type="button" class="btn-sm" :disabled="saving || isAutoDistilling" @click="handleSaveReview">
                {{ saving ? "保存中…" : "保存修正" }}
              </button>
              <button type="button" class="btn-sm" :disabled="saving || isAutoDistilling" @click="handleConfirmImport">
                {{ isAutoDistilling ? 'AI 正在自动学习…' : '确认导入并自动学习' }}
              </button>
              <button v-if="false"
                type="button"
                class="btn-primary btn-sm"
                style="background: linear-gradient(135deg, #e6b980 0%, #eac775 100%); color: #1a1610; font-weight: 600; border: none;"
                :disabled="saving || isAutoDistilling"
                @click="handleAutoDistill"
              >
                {{ isAutoDistilling ? "正在提炼人设…" : "✨ 自动生成角色人设" }}
              </button>
            </div>
          </div>

          <div class="import-target-picker" role="group" aria-label="导入目标会话">
            <span>导入到</span>
            <select v-model="importTarget" aria-label="选择导入会话">
              <option v-for="conversation in conversations" :key="conversation.id" :value="conversation.id">{{ conversation.title }}</option>
              <option value="new">新建聊天</option>
            </select>
            <label v-if="importTarget === 'new'" class="import-conversation-name">
              <span>对方网名</span>
              <input v-model="newConversationName" maxlength="64" placeholder="例如：晚晚" aria-label="当前对话人的网名" />
            </label>
          </div>

          <div v-if="autoDistillError" class="import-error-banner">{{ autoDistillError }}</div>
          <div v-if="errorMessage" class="import-error-banner">{{ errorMessage }}</div>

          <div v-if="isAutoDistilling" style="padding: 16px 20px; margin-bottom: 12px; background: rgba(230, 185, 128, 0.08); border: 1px solid rgba(230, 185, 128, 0.25); border-radius: 8px; text-align: center; color: #ecd7af; font-size: 0.88rem;">
            ✨ <strong>AI 正在深度提炼五层人设与共同回忆…</strong> 自动分析语言风格、口头禅、情绪机制与专属记忆，完成后将直接为您打开角色工坊供您查看与微调。
          </div>

          <section class="import-avatar-setup" aria-label="导入聊天头像">
            <div class="import-avatar-setup__copy">
              <strong>聊天头像（可选）</strong>
              <span>{{ targetConversation?.avatar_object_key && !currentBatch?.left_avatar_object_key ? '将复用所选会话头像；也可以为本次导入单独上传。' : '可为本次导入单独上传对方头像，不会修改会话头像。' }}</span>
            </div>
            <div class="import-avatar-setup__sides">
              <div class="import-avatar-slot">
                <img v-if="avatarUrl('left')" :src="avatarUrl('left')" class="import-avatar-slot__image" alt="左侧对方头像" />
                <span v-else class="import-avatar-slot__fallback" aria-hidden="true">对</span>
                <div>
                  <strong>左侧 · 对方</strong>
                  <button type="button" class="btn-xs" :disabled="avatarUploading !== null" @click="chooseAvatar">
                    {{ avatarUploading === 'left' ? '上传中…' : avatarUrl('left') ? '更换头像' : '上传头像' }}
                  </button>
                </div>
                <input ref="leftAvatarInputEl" type="file" accept="image/jpeg,image/png,image/webp" hidden @change="uploadAvatar" />
              </div>
            </div>
          </section>

          <div class="import-review-split">
            <div v-if="false" class="form-card" style="grid-column:1/-1" role="group" aria-label="声音画像应用目标">
              <label style="display:flex;gap:8px;align-items:center">
                <input v-model="applyVoiceToCurrentPersona" type="checkbox" :disabled="closeLocked || !personaStore.activePersona" />
                确认导入时，将声音画像应用到当前角色「{{ personaStore.activePersona?.name || '未选择角色' }}」
              </label>
              <p style="color:#aaa;font-size:13px;line-height:1.6;margin:8px 0 0">应用后，该角色在各会话中的后续语音对话和新生成朗读都会使用这份设置。仅点“保存修正”会保存到本次导入；“自动生成角色人设”会应用到新角色。</p>
              <p v-if="appliedVoiceNotice" role="status">{{ appliedVoiceNotice }}</p>
            </div>
            <details v-if="false" class="form-card" style="grid-column:1/-1">
              <summary style="cursor:pointer;color:#e5cea4">声音画像（可选，可修改 AI 的文字推断建议）</summary>
              <fieldset :disabled="closeLocked" style="border:0;padding:0;margin:0;min-width:0"><VoiceProfileForm v-model="voiceProfile" /></fieldset>
            </details>
            <!-- Left: Screenshot Preview -->
            <div class="import-review-left">
              <div class="import-preview-header">
                <div class="import-preview-header-title">
                  <span>原图参考</span>
                  <span v-if="attachments.length > 1">({{ activeAttachmentIndex + 1 }}/{{ attachments.length }})</span>
                </div>
                <button
                  type="button"
                  class="btn-zoom-preview"
                  title="全屏放大查看 (快捷键 Esc 关闭)"
                  @click="openImagePreview(activeAttachmentIndex)"
                >
                  🔍 放大查看
                </button>
              </div>
              <div
                class="import-preview-viewport"
                title="点击全屏放大预览"
                @click="openImagePreview(activeAttachmentIndex)"
              >
                <img
                  v-if="attachments[activeAttachmentIndex]"
                  :src="attachments[activeAttachmentIndex].local_preview || attachments[activeAttachmentIndex].download_url"
                  :alt="attachments[activeAttachmentIndex].filename"
                  class="import-preview-img"
                />
                <div class="import-preview-hover-hint">
                  <span>🔍 点击全屏放大预览</span>
                </div>
              </div>
              <div v-if="attachments.length > 1" class="import-preview-thumbnails">
                <button
                  v-for="(att, idx) in attachments"
                  :key="idx"
                  type="button"
                  class="import-preview-thumb-btn"
                  :class="{ 'is-active': activeAttachmentIndex === idx }"
                  @click="selectAttachment(idx)"
                  @dblclick="openImagePreview(idx)"
                >
                  <img :src="att.local_preview || att.download_url" :alt="att.filename" />
                  <span>#{{ idx + 1 }}</span>
                </button>
              </div>
            </div>

            <!-- Right: Editable Message Cards -->
            <div ref="messageListEl" class="import-review-right">
              <div class="import-current-attachment-label">
                当前截图：{{ activeAttachment?.filename || "未选择截图" }}
                <span>（{{ visibleMessages.length }} 条记录）</span>
              </div>
              <div v-if="visibleMessages.length === 0" class="import-empty-messages">
                当前截图未能提取出有效对话消息。您可以返回重试或选择其他截图。
              </div>
              <div v-else class="import-message-list">
                <div
                  v-for="(msg, idx) in visibleMessages"
                  :key="msg.id || idx"
                  class="import-msg-card"
                  :class="[`is-${msg.role_guess}`, { 'needs-review': msg.needs_review }]"
                >
                  <div class="import-msg-card__header">
                    <div class="import-msg-card__speaker-wrap">
                      <button
                        type="button"
                        class="import-role-toggle"
                        :class="`role-${msg.role_guess}`"
                        title="点击切换我方/对方身份"
                        @click="toggleRole(msg)"
                      >
                        {{ msg.role_guess === "user" ? "我方 (右侧)" : "对方 (左侧)" }}
                      </button>
                      <input
                        v-model="msg.speaker_label"
                        type="text"
                        class="import-speaker-input"
                        placeholder="说话人昵称"
                      />
                    </div>

                    <div class="import-msg-card__meta">
                      <input
                        v-model="msg.timestamp_text"
                        type="text"
                        class="import-time-input"
                        placeholder="时间 (如 14:20)"
                      />
                      <span v-if="msg.confidence < 0.9" class="import-confidence-tag">
                        置信度 {{ Math.round(msg.confidence * 100) }}%
                      </span>
                      <div class="import-msg-card__reorder">
                        <button
                          type="button"
                          class="btn-icon"
                          :disabled="idx === 0"
                          title="上移"
                          @click="moveMessage(msg, 'up')"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          class="btn-icon"
                          :disabled="idx === visibleMessages.length - 1"
                          title="下移"
                          @click="moveMessage(msg, 'down')"
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          class="btn-icon btn-icon--danger"
                          title="删除此消息"
                          @click="deleteMessage(msg)"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>

                  <div class="import-msg-card__body">
                    <textarea
                      v-model="msg.text"
                      rows="2"
                      class="import-text-input"
                      placeholder="消息内容"
                    ></textarea>

                    <!-- Media Placeholder Actions -->
                    <div v-if="msg.media_kind === 'image'" class="import-placeholder-box">
                      <div class="import-placeholder-header">
                        <span>🖼️ [图片消息]</span>
                        <span class="import-placeholder-status">
                          {{ msg.media_status === 'uploaded' ? '已补充原始图片' : (msg.media_status === 'ignored' ? '已忽略' : '原始图片未上传') }}
                        </span>
                      </div>
                      <div v-if="msg.media_download_url" class="import-placeholder-preview">
                        <img :src="msg.media_download_url" alt="补充图片" />
                      </div>
                      <div class="import-placeholder-actions">
                        <button
                          type="button"
                          class="btn-xs"
                          :disabled="msg.media_status === 'uploading'"
                          @click="handleSupplementMedia(msg, 'image')"
                        >
                          {{ msg.media_status === 'uploaded' ? '重新替换图片' : '补充高清图片' }}
                        </button>
                        <button
                          v-if="msg.media_status !== 'ignored'"
                          type="button"
                          class="btn-xs btn-text"
                          @click="ignoreMedia(msg)"
                        >
                          忽略此图
                        </button>
                      </div>
                    </div>

                    <div v-else-if="msg.media_kind === 'video'" class="import-placeholder-box">
                      <div class="import-placeholder-header">
                        <span>🎬 [视频消息]</span>
                        <span class="import-placeholder-status">
                          {{ msg.media_status === 'uploaded' ? '已补充原始视频' : (msg.media_status === 'ignored' ? '已忽略' : '原始视频未上传') }}
                        </span>
                      </div>
                      <div v-if="msg.media_download_url" class="import-placeholder-preview">
                        <video :src="msg.media_download_url" controls style="max-height: 120px;"></video>
                      </div>
                      <div class="import-placeholder-actions">
                        <button
                          type="button"
                          class="btn-xs"
                          :disabled="msg.media_status === 'uploading'"
                          @click="handleSupplementMedia(msg, 'video')"
                        >
                          {{ msg.media_status === 'uploaded' ? '重新替换视频' : '补充原始视频' }}
                        </button>
                        <button
                          v-if="msg.media_status !== 'ignored'"
                          type="button"
                          class="btn-xs btn-text"
                          @click="ignoreMedia(msg)"
                        >
                          忽略此视频
                        </button>
                      </div>
                    </div>

                    <div v-else-if="msg.media_kind === 'audio'" class="import-placeholder-box import-placeholder-box--audio">
                      <div class="import-placeholder-header">
                        <span>🎙️ [语音消息]</span>
                        <span class="import-placeholder-status">
                          {{ msg.transcript ? '已填写转写' : '请先转写语音内容' }}
                        </span>
                      </div>
                      <div class="import-audio-transcript-row">
                        <input
                          v-model="msg.transcript"
                          type="text"
                          class="import-transcript-input"
                          placeholder="请将这段语音转成文字填写在此处…"
                        />
                        <button
                          type="button"
                          class="btn-xs btn-primary"
                          :disabled="!msg.transcript?.trim()"
                          @click="saveTranscript(msg)"
                        >
                          保存转写
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- STEP 4: Success -->
        <div v-else-if="step === 'success'" class="import-step import-step--success">
          <div class="import-success-icon">✓</div>
          <h3>截图对话记录已成功导入！</h3>
          <p>共 {{ messages.length }} 条对话消息已保存到您的会话记录中。</p>
          <div v-if="autoDistillError" class="import-error-banner" style="margin: 12px auto; max-width: 480px;">
            {{ autoDistillError }}
          </div>
          <div class="import-footer-actions" style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
            <button v-if="false"
              type="button"
              class="btn-primary"
              style="background: linear-gradient(135deg, #e6b980 0%, #eac775 100%); color: #1a1610; font-weight: 600; border: none; padding: 10px 22px;"
              :disabled="isAutoDistilling"
              @click="handleDistillFromBatch"
            >
              {{ isAutoDistilling ? "正在提炼五层人设与回忆…" : "✨ 一键自动生成角色人设 (无需填写)" }}
            </button>
            <button type="button" class="btn-outline" :disabled="isAutoDistilling" @click="handleClose">返回聊天</button>
          </div>
          <p v-if="isAutoDistilling" style="margin-top: 14px; font-size: 0.84rem; color: #ecd7af;">
            AI 正在基于扫描内容推导语言习惯与共同记忆，生成后将自动打开角色工坊供您微调…
          </p>
        </div>
      </div>
    </div>

  <!-- Fullscreen Image Zoom Lightbox Modal -->
  <div v-if="isPreviewOpen" class="import-lightbox" @click="closeImagePreview">
      <div class="import-lightbox__backdrop"></div>
      <div class="import-lightbox__content" @click.stop>
        <div class="import-lightbox__toolbar">
          <span class="import-lightbox__title">
            {{ attachments[activeAttachmentIndex]?.filename || '原图截图' }}
            <span v-if="attachments.length > 1">({{ activeAttachmentIndex + 1 }} / {{ attachments.length }})</span>
          </span>
          <div class="import-lightbox__controls">
            <button
              type="button"
              class="btn-lightbox-tool"
              title="缩小 (-)"
              :disabled="zoomLevel <= 0.5"
              @click="zoomOut"
            >
              -
            </button>
            <span class="import-lightbox__zoom-text">{{ Math.round(zoomLevel * 100) }}%</span>
            <button
              type="button"
              class="btn-lightbox-tool"
              title="放大 (+)"
              :disabled="zoomLevel >= 3"
              @click="zoomIn"
            >
              +
            </button>
            <button
              type="button"
              class="btn-lightbox-tool"
              title="重置 (1:1)"
              @click="resetZoom"
            >
              1:1
            </button>
            <button
              type="button"
              class="btn-lightbox-close"
              title="关闭预览 (Esc)"
              @click="closeImagePreview"
            >
              ×
            </button>
          </div>
        </div>
        <div class="import-lightbox__viewport">
          <button
            v-if="attachments.length > 1"
            type="button"
            class="import-lightbox__nav-btn import-lightbox__nav-btn--prev"
            :disabled="activeAttachmentIndex === 0"
            title="上一张截图 (←)"
            @click.stop="prevAttachment"
          >
            ‹
          </button>
          <div class="import-lightbox__img-container">
            <img
              :src="attachments[activeAttachmentIndex]?.local_preview || attachments[activeAttachmentIndex]?.download_url"
              :alt="attachments[activeAttachmentIndex]?.filename"
              class="import-lightbox__img"
              :style="{ transform: `scale(${zoomLevel})` }"
            />
          </div>
          <button
            v-if="attachments.length > 1"
            type="button"
            class="import-lightbox__nav-btn import-lightbox__nav-btn--next"
            :disabled="activeAttachmentIndex === attachments.length - 1"
            title="下一张截图 (→)"
            @click.stop="nextAttachment"
          >
            ›
          </button>
        </div>
      </div>
  </div>
  </dialog>
</template>
