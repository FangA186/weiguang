<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from "vue";
import { storeToRefs } from "pinia";
import { useVoiceConfigStore } from "../stores/voiceConfig";
import { useAuthStore } from "../stores/auth";
import { usePersonaStore } from "../stores/personaStore";
import type { VoiceCloneRecord, VoiceProfile } from "../types";
import {
  createBailianVoiceClone,
  denoiseBailianVoiceReference,
  presignBailianVoiceUpload,
  quotaExceededMessage,
  uploadBailianVoiceReference,
} from "../api";
import { formatQuotaValue } from "../config/plans";

import AudioTrimmer from "./AudioTrimmer.vue";
import VoiceProfileForm from "./VoiceProfileForm.vue";
import { normalizeVoiceReference } from "../utils/audioEncoder";

const voice = useVoiceConfigStore();
const auth = useAuthStore();
const personaStore = usePersonaStore();
const { dialogOpen, dialogMode, speaker, characterManifest, voiceClone, voiceClones } = storeToRefs(voice);

const dialogRef = ref<HTMLDialogElement | null>(null);
const speakerDraft = ref("");
const manifestDraft = ref("");
const normalManifestDraft = ref("");
const normalManifestOriginal = ref("");
const advancedMode = ref(false);
const cloneResult = ref("");
const voiceName = ref("我的音色");
const savingConfig = ref(false);
const bailianVoiceAuthorized = ref(false);
const bailianVoiceSaving = ref(false);
const audioFile = ref<File | null>(null);
const rawOriginalAudioFile = ref<File | null>(null);
const isTrimPanelOpen = ref(false);
const isTrimmed = ref(false);
const audioName = ref("");
const audioMeta = ref("");
const audioPreviewSrc = ref("");
const persistedAudioUrl = ref("");
const sourceDuration = ref(0);
const uploadedSourceObjectKey = ref("");
const uploadedSourceSize = ref(0);
const denoisedObjectKey = ref("");
const denoisedPreviewUrl = ref("");
const denoisedSize = ref(0);
const denoisedDuration = ref(0);
const denoiseSaving = ref(false);
const cloneSource = ref<"original" | "denoised">("original");
const deletingVoiceId = ref("");
const voiceProfileDraft = ref<VoiceProfile>({});
const savingVoiceProfile = ref(false);
const voiceProfileValid = ref(true);
const renamingVoiceId = ref("");
const voiceRenameDraft = ref("");

const voiceSlotMetric = computed(() => auth.billingSummary?.metrics?.voice_slot);
const voiceSlotsFull = computed(() => {
  const metric = voiceSlotMetric.value;
  return Boolean(metric && metric.limit >= 0 && metric.remaining <= 0);
});
const voiceSlotText = computed(() => {
  const metric = voiceSlotMetric.value;
  if (!metric) return "正在读取音色槽位…";
  return `音色槽位：已用 ${formatQuotaValue("voice_slot", metric.used)} · 预留 ${formatQuotaValue("voice_slot", metric.reserved)} · 剩余 ${formatQuotaValue("voice_slot", metric.remaining)} / 上限 ${formatQuotaValue("voice_slot", metric.limit)}`;
});

const DEFAULT_MANIFEST =
  "你是微光，一个明确标注为 AI 的温和陪伴角色。你认真倾听，简短自然地回应，不冒充或替代任何真实的人。";

function isCompiledPrompt(value: string): boolean {
  return /#\s*SYSTEM INSTRUCTION|\[PERSONA\]|\[MEMORIES\]|优先级\s*0|五层人格模型|共同记忆库|对话守则/i.test(value)
    || value.trim().length > 240;
}

function normalManifestText(value: string): string {
  const text = value.trim();
  return text && !isCompiledPrompt(text)
    ? text
    : "温和、自然地倾听并回应，保持明确的 AI 身份，不冒充或替代真实人物。";
}

function formatBytes(size: number): string {
  if (size < 1024) return size + " B";
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
  return (size / (1024 * 1024)).toFixed(1) + " MB";
}

function syncOpen() {
  const el = dialogRef.value;
  if (!el) return;
  if (dialogOpen.value && !el.open) {
    speakerDraft.value = speaker.value;
    manifestDraft.value = characterManifest.value;
    normalManifestDraft.value = normalManifestText(characterManifest.value);
    normalManifestOriginal.value = normalManifestDraft.value;
    advancedMode.value = false;
    voiceProfileDraft.value = JSON.parse(JSON.stringify(personaStore.activePersona?.persona?.layer2_expression_dna?.voice_style || {}));
    syncPersistedClone();
    void auth.fetchBilling();
    el.showModal();
  } else if (!dialogOpen.value && el.open) {
    el.close();
  }
}

async function saveVoiceProfile() {
  const active = personaStore.activePersona;
  if (!active || savingVoiceProfile.value || !voiceProfileValid.value) return;
  savingVoiceProfile.value = true;
  try {
    await personaStore.savePersona(active.id, { voice_style: voiceProfileDraft.value });
    cloneResult.value = `“${active.name}”的声音配置已保存。`;
  } catch (error) {
    cloneResult.value = quotaExceededMessage(error);
  } finally {
    savingVoiceProfile.value = false;
  }
}

function syncPersistedClone() {
  const clone = voiceClone.value;
  if (audioFile.value) return;
  if (!clone) {
    persistedAudioUrl.value = "";
    audioName.value = "";
    audioMeta.value = "";
    sourceDuration.value = 0;
    return;
  }
  persistedAudioUrl.value = clone.reference_audio_url || "";
  audioName.value = clone.reference_filename || "已绑定参考音频";
  audioMeta.value = clone.reference_size ? formatBytes(clone.reference_size) : "已上传";
  sourceDuration.value = clone.reference_duration || 0;
  cloneResult.value = "";
}

watch(dialogOpen, syncOpen);
watch(dialogRef, syncOpen);

function onClose() {
  if (dialogOpen.value) voice.close();
}

async function saveConfig() {
  savingConfig.value = true;
  try {
    const normalChanged = normalManifestDraft.value.trim() !== normalManifestOriginal.value.trim();
    const nextManifest = advancedMode.value
      ? manifestDraft.value
      : normalChanged
        ? normalManifestDraft.value
        : manifestDraft.value;
    const saved = await voice.save({
      speaker: speakerDraft.value,
      characterManifest: nextManifest || DEFAULT_MANIFEST,
    });
    manifestDraft.value = saved.character_manifest;
    normalManifestDraft.value = normalManifestText(saved.character_manifest);
    normalManifestOriginal.value = normalManifestDraft.value;
    cloneResult.value = "声音与角色设置已保存，将应用到下一次实时会话。";
  } catch (error) {
    cloneResult.value = (error as Error).message;
  } finally {
    savingConfig.value = false;
  }
}

async function selectVoiceClone(clone: VoiceCloneRecord) {
  speakerDraft.value = clone.voice_id;
  try {
    const saved = await voice.save({ speaker: clone.voice_id, characterManifest: characterManifest.value });
    speakerDraft.value = saved.speaker;
    syncPersistedClone();
    cloneResult.value = `已切换音色：${clone.reference_filename}。`;
  } catch (error) {
    speakerDraft.value = speaker.value;
    cloneResult.value = quotaExceededMessage(error);
  }
}

async function deleteVoiceClone(clone: VoiceCloneRecord) {
  if (deletingVoiceId.value || !window.confirm(`确定删除音色“${clone.reference_filename}”吗？此操作不可撤销。`)) return;
  deletingVoiceId.value = clone.voice_id;
  cloneResult.value = "正在删除音色…";
  try {
    const result = await voice.deleteVoiceClone(clone.voice_id);
    speakerDraft.value = result.speaker;
    syncPersistedClone();
    cloneResult.value = result.speaker
      ? "音色已删除，已切换为可用音色。"
      : "音色已删除，已切换为系统默认音色。";
    await auth.fetchBilling();
  } catch (error) {
    cloneResult.value = quotaExceededMessage(error);
  } finally {
    deletingVoiceId.value = "";
  }
}

function startRenameVoice(clone: VoiceCloneRecord) {
  renamingVoiceId.value = clone.voice_id;
  voiceRenameDraft.value = clone.reference_filename;
}

async function saveVoiceRename(clone: VoiceCloneRecord) {
  const name = voiceRenameDraft.value.trim();
  if (!name) return;
  try {
    await voice.renameVoiceClone(clone.voice_id, name);
    cloneResult.value = `音色已重命名为“${name}”。`;
    renamingVoiceId.value = "";
  } catch (error) {
    cloneResult.value = quotaExceededMessage(error);
  }
}

function onAudioChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files && input.files[0] ? input.files[0] : null;
  rawOriginalAudioFile.value = file;
  isTrimmed.value = false;
  isTrimPanelOpen.value = false;
  renderAudioFile(file);
}

function openTrimmer() {
  isTrimPanelOpen.value = true;
}

function onAudioTrimmed(payload: { file: File; duration: number }) {
  isTrimPanelOpen.value = false;
  isTrimmed.value = true;
  renderAudioFile(payload.file);
  sourceDuration.value = payload.duration;
  cloneResult.value = `音频已成功裁剪为 ${payload.duration.toFixed(1)} 秒（标准无损 WAV 格式），确认授权后即可上传。`;
}

function restoreOriginalAudio() {
  if (!rawOriginalAudioFile.value) return;
  isTrimmed.value = false;
  isTrimPanelOpen.value = false;
  renderAudioFile(rawOriginalAudioFile.value);
  cloneResult.value = "已还原为原始录音文件。";
}

function renderAudioFile(file: File | null) {
  if (audioPreviewSrc.value) URL.revokeObjectURL(audioPreviewSrc.value);
  audioPreviewSrc.value = file ? URL.createObjectURL(file) : "";
  audioFile.value = file;
  audioName.value = file?.name || "";
  audioMeta.value = file ? formatBytes(file.size) : "";
  sourceDuration.value = 0;
  uploadedSourceObjectKey.value = "";
  uploadedSourceSize.value = 0;
  denoisedObjectKey.value = "";
  denoisedPreviewUrl.value = "";
  denoisedSize.value = 0;
  denoisedDuration.value = 0;
  cloneSource.value = "original";
  persistedAudioUrl.value = "";
  cloneResult.value = file ? "音频已就绪，确认授权后即可上传。" : "";
  if (!file) syncPersistedClone();
}

async function ensureAudioUploaded(): Promise<string> {
  if (uploadedSourceObjectKey.value) return uploadedSourceObjectKey.value;
  if (!audioFile.value) throw new Error("请选择参考音频。");
  const normalized = await normalizeVoiceReference(audioFile.value);
  if (normalized.size > 10 * 1024 * 1024) throw new Error("转换后的48kHz单声道WAV超过10 MB，请缩短音频。");
  const presign = await presignBailianVoiceUpload(normalized);
  await uploadBailianVoiceReference(presign, normalized);
  uploadedSourceObjectKey.value = presign.object_key;
  uploadedSourceSize.value = normalized.size;
  return presign.object_key;
}

async function generateDenoisedPreview() {
  if (!audioFile.value || !bailianVoiceAuthorized.value || sourceDuration.value < 5 || sourceDuration.value > 60) return;
  denoiseSaving.value = true;
  cloneResult.value = "正在上传并净化背景噪声…";
  try {
    const sourceKey = await ensureAudioUploaded();
    const result = await denoiseBailianVoiceReference(sourceKey);
    denoisedObjectKey.value = result.object_key;
    denoisedPreviewUrl.value = result.download_url;
    denoisedSize.value = result.size;
    denoisedDuration.value = result.duration;
    cloneSource.value = "denoised";
    cloneResult.value = `DeepFilterNet 净化完成（${result.duration.toFixed(1)} 秒），请试听并选择用于克隆的版本。`;
  } catch (error) {
    cloneResult.value = quotaExceededMessage(error);
  } finally {
    denoiseSaving.value = false;
  }
}

function onPreviewMetadata(event: Event) {
  const duration = (event.target as HTMLAudioElement).duration;
  if (Number.isFinite(duration) && !sourceDuration.value) sourceDuration.value = duration;
}

function removeAudio() {
  rawOriginalAudioFile.value = null;
  isTrimmed.value = false;
  isTrimPanelOpen.value = false;
  renderAudioFile(null);
  const input = document.getElementById("bailianVoiceAudio") as HTMLInputElement | null;
  if (input) input.value = "";
  input?.focus();
}

async function submitBailianVoiceClone(event: Event) {
  event.preventDefault();
  if (voiceSlotsFull.value) {
    cloneResult.value = "专属克隆音色槽位已满，请等待套餐额度重置或查看可用套餐。";
    return;
  }
  if (!audioFile.value) {
    cloneResult.value = "请选择参考音频。";
    return;
  }
  if (!bailianVoiceAuthorized.value) {
    cloneResult.value = "请先确认已取得声音本人的明确授权。";
    return;
  }
  if (audioFile.value.size > 10 * 1024 * 1024) {
    cloneResult.value = "参考音频不能超过 10 MB。";
    return;
  }
  if (!sourceDuration.value) {
    cloneResult.value = "正在读取音频时长，请稍后再提交。";
    return;
  }
  if (sourceDuration.value < 5) {
    cloneResult.value = "参考音频需要至少 5 秒连续清晰人声；建议使用 10–20 秒录音。";
    return;
  }
  if (sourceDuration.value > 60) {
    cloneResult.value = "参考音频不能超过 60 秒，请先裁剪后再上传。";
    return;
  }

  bailianVoiceSaving.value = true;
  cloneResult.value = "正在上传参考音频…";
  try {
    const originalObjectKey = await ensureAudioUploaded();
    const useDenoised = cloneSource.value === "denoised" && denoisedObjectKey.value;
    const selectedObjectKey = useDenoised ? denoisedObjectKey.value : originalObjectKey;
    cloneResult.value = "参考音频已上传，正在克隆声音…";
    const result = await createBailianVoiceClone({
      object_key: selectedObjectKey,
      prefix: "weiguang",
      language_hints: ["zh"],
      enable_preprocess: true,
      enable_volume_normalization: true,
      max_prompt_audio_length: Math.min(30, Math.max(5, sourceDuration.value)),
      reference_filename: voiceName.value.trim() || "我的音色",
      reference_size: useDenoised ? denoisedSize.value : uploadedSourceSize.value,
      reference_duration: useDenoised ? denoisedDuration.value : sourceDuration.value,
    });
    speakerDraft.value = result.voice_id;
    await voice.save({ speaker: result.voice_id, characterManifest: characterManifest.value });
    voice.addVoiceClone(result);
    voice.selectVoiceClone(result.voice_id);
    persistedAudioUrl.value = result.reference_audio_url || "";
    cloneResult.value = "声音克隆完成，已自动应用到后续对话。";
    voiceName.value = "我的音色";
    bailianVoiceAuthorized.value = false;
    await auth.fetchBilling();
  } catch (error) {
    cloneResult.value = quotaExceededMessage(error);
  } finally {
    bailianVoiceSaving.value = false;
  }
}

function closeOnBackdrop(event: MouseEvent) {
  if (event.target === dialogRef.value) voice.close();
}

onBeforeUnmount(() => {
  dialogRef.value?.close();
  if (audioPreviewSrc.value) URL.revokeObjectURL(audioPreviewSrc.value);
});
</script>

<template>
  <dialog ref="dialogRef" class="voice-settings" @close="onClose" @click="closeOnBackdrop">
    <div class="voice-settings__panel">
      <header class="voice-settings__header">
        <h2>{{ dialogMode === "settings" ? "音色设置" : "克隆声音" }}</h2>
        <button type="button" class="voice-settings__close" aria-label="关闭" @click="voice.close()">×</button>
      </header>

      <div class="voice-settings__body">
        <section v-if="false" class="voice-settings__section">
          <template v-if="!advancedMode">
            <label class="voice-field">
              <span>角色描述（普通模式）</span>
              <textarea v-model="normalManifestDraft" rows="4" maxlength="240" placeholder="例如：温和、自然地倾听并回应。"></textarea>
            </label>
            <small class="voice-settings__hint">完整 System Prompt 不会在普通模式直接显示；未修改描述时会保留现有高级设置。</small>
          </template>
          <template v-else>
            <div class="voice-advanced-warning" role="alert">
              高级模式会直接展示并编辑完整 System Prompt，可能改变 AI 的身份、边界和回复行为。仅在你明确知道每条指令含义时修改。
            </div>
            <label class="voice-field">
              <span>完整 System Prompt（高级模式）</span>
              <textarea v-model="manifestDraft" rows="10" maxlength="4000" spellcheck="false"></textarea>
            </label>
          </template>
          <button type="button" class="voice-action voice-action--primary" :disabled="savingConfig" @click="saveConfig">
            {{ savingConfig ? "保存中…" : advancedMode ? "保存高级设置" : "保存并应用" }}
          </button>
          <button type="button" class="voice-action voice-action--advanced-toggle" @click="advancedMode = !advancedMode">
            {{ advancedMode ? "返回普通模式" : "进入高级模式" }}
          </button>
        </section>

        <section v-if="dialogMode === 'settings'" class="voice-settings__section">
          <h3>当前角色：{{ personaStore.activePersonaName }}</h3>
          <VoiceProfileForm v-model="voiceProfileDraft" :model="speaker.startsWith('cosyvoice-v3.5-plus-') ? 'cosyvoice-v3.5-plus' : ''" @validity="voiceProfileValid = $event" />
          <button type="button" class="voice-action voice-action--primary voice-action--submit" :disabled="savingVoiceProfile || !personaStore.activePersona || !voiceProfileValid" @click="saveVoiceProfile">
            {{ savingVoiceProfile ? "保存中…" : "保存声音配置" }}
          </button>
        </section>

        <section class="voice-settings__section voice-clone">
          <h3 v-if="dialogMode === 'settings'">已创建音色</h3>
          <label v-if="dialogMode === 'clone'" class="voice-field"><span>音色名称</span><input v-model="voiceName" maxlength="24" placeholder="例如：温柔女声" /></label>
          <div v-if="dialogMode === 'clone'" class="voice-source-heading">
            <div>
              <small class="voice-settings__hint" :class="{ 'voice-settings__hint--warning': voiceSlotsFull }">{{ voiceSlotText }}</small>
            </div>
          </div>
          <div v-if="dialogMode === 'clone'" class="voice-recording-guide">
            <strong>怎样录制，克隆效果更好？</strong>
            <p>建议上传 10–20 秒的单人连续清晰说话录音，使用正常语速；保持环境安静，不要带背景音乐、回声、杂音或其他人的声音。</p>
          </div>

          <div v-if="voiceClones.length" class="voice-clone-list" aria-label="已创建音色">
            <div v-for="clone in voiceClones" :key="clone.voice_id" class="voice-clone-list__item" :class="{ 'is-selected': speakerDraft === clone.voice_id }">
              <div class="voice-clone-list__copy">
                <input v-if="renamingVoiceId === clone.voice_id" v-model="voiceRenameDraft" class="voice-rename-input" maxlength="24" aria-label="新的音色名称" @keydown.enter.prevent="saveVoiceRename(clone)" />
                <strong v-else>{{ clone.reference_filename || "未命名音色" }}</strong>
                <small>{{ clone.reference_duration ? `${clone.reference_duration.toFixed(1)} 秒` : "时长待核对" }}</small>
              </div>
              <div class="voice-clone-list__actions">
                <button v-if="renamingVoiceId === clone.voice_id" type="button" class="voice-action voice-action--compact" @click="saveVoiceRename(clone)">保存</button>
                <button v-if="renamingVoiceId === clone.voice_id" type="button" class="voice-action voice-action--compact" @click="renamingVoiceId = ''">取消</button>
                <button v-if="renamingVoiceId !== clone.voice_id" type="button" class="voice-action voice-action--compact" :aria-pressed="speakerDraft === clone.voice_id" :disabled="Boolean(deletingVoiceId)" @click="selectVoiceClone(clone)">
                  {{ speakerDraft === clone.voice_id ? "当前音色" : "设为当前" }}
                </button>
                <button v-if="renamingVoiceId !== clone.voice_id" type="button" class="voice-action voice-action--compact" :disabled="Boolean(deletingVoiceId)" @click="startRenameVoice(clone)">重命名</button>
                <button v-if="renamingVoiceId !== clone.voice_id" type="button" class="voice-action voice-action--compact voice-action--danger" :disabled="Boolean(deletingVoiceId)" @click="deleteVoiceClone(clone)">
                  {{ deletingVoiceId === clone.voice_id ? "删除中…" : "删除" }}
                </button>
              </div>
            </div>
          </div>
          <p v-else-if="dialogMode === 'settings'" class="voice-settings__hint">暂无已创建音色，请先使用顶部“克隆声音”创建。</p>

          <form v-if="dialogMode === 'clone'" @submit="submitBailianVoiceClone">
            <div class="voice-field voice-field--audio">
              <span>参考音频</span>
              <div class="voice-upload" :class="{ 'has-file': !!audioFile }">
                <input class="voice-upload__input" id="bailianVoiceAudio" type="file" accept=".wav,.mp3,.m4a,audio/wav,audio/mpeg,audio/mp4,audio/x-m4a" required :disabled="voiceSlotsFull" @change="onAudioChange" />
                <label class="voice-upload__picker" for="bailianVoiceAudio">
                  <span class="voice-upload__mark" aria-hidden="true">↑</span>
                  <span class="voice-upload__copy"><strong>选择参考音频</strong><small>WAV · MP3 · M4A · 最大 10 MB；至少 5 秒，建议 10–20 秒</small></span>
                  <span class="voice-upload__browse">浏览</span>
                </label>
                <div class="voice-upload__selected" v-if="audioFile">
                  <span class="voice-upload__file">
                    <strong>{{ audioName }}</strong>
                    <small>
                      {{ audioMeta }}
                      <template v-if="sourceDuration"> · {{ sourceDuration.toFixed(1) }} 秒</template>
                      <span v-if="isTrimmed" class="voice-trimmed-tag">已裁剪</span>
                    </small>
                  </span>
                  <div class="voice-upload__actions">
                    <button
                      v-if="isTrimmed && rawOriginalAudioFile"
                      type="button"
                      class="voice-action-btn"
                      title="还原回原始完整录音"
                      @click="restoreOriginalAudio"
                    >
                      ↺ 还原
                    </button>
                    <button
                      type="button"
                      class="voice-action-btn voice-action-btn--trim"
                      :title="isTrimmed ? '重新调整裁剪选区' : '截取最清晰的人声片段'"
                      @click="openTrimmer"
                    >
                      ✂️ {{ isTrimmed ? "重新裁剪" : "裁剪音频" }}
                    </button>
                    <button type="button" class="voice-upload__remove" aria-label="移除所选音频" title="移除所选音频" @click="removeAudio">×</button>
                  </div>
                </div>
              </div>

              <!-- Interactive Audio Trimmer -->
              <AudioTrimmer
                v-if="isTrimPanelOpen && (rawOriginalAudioFile || audioFile)"
                :file="rawOriginalAudioFile || audioFile!"
                @trimmed="onAudioTrimmed"
                @cancel="isTrimPanelOpen = false"
              />
              <small v-if="isTrimPanelOpen" class="voice-settings__hint">当前选区尚未生效；请先确认裁剪，再生成净化试听。</small>

              <div v-if="voiceClone && !audioFile" class="voice-upload__persisted">
                <strong>已绑定参考音频</strong>
                <small>{{ voiceClone.reference_filename || "我的音色" }}</small>
              </div>
              <audio v-if="!isTrimPanelOpen && (audioPreviewSrc || persistedAudioUrl)" class="voice-preview" controls preload="metadata" :src="audioPreviewSrc || persistedAudioUrl" aria-label="预览参考音频" @loadedmetadata="onPreviewMetadata"></audio>
            </div>

            <label class="voice-consent"><input v-model="bailianVoiceAuthorized" type="checkbox" required :disabled="voiceSlotsFull" /><span>我已取得声音本人的明确授权，并同意用于本次声音复刻。</span></label>
            <button
              v-if="audioFile"
              type="button"
              class="voice-action voice-denoise__button"
              :disabled="isTrimPanelOpen || denoiseSaving || bailianVoiceSaving || !bailianVoiceAuthorized || !sourceDuration || sourceDuration < 5 || sourceDuration > 60"
              @click="generateDenoisedPreview"
            >
              {{ isTrimPanelOpen ? "确认裁剪后去除背景噪声" : denoiseSaving ? "正在净化背景噪声…" : denoisedObjectKey ? "重新生成净化试听" : "去除背景噪声并试听" }}
            </button>
            <div v-if="denoisedPreviewUrl && !isTrimPanelOpen" class="voice-denoise" aria-label="音频净化结果">
              <strong>净化音试听</strong>
              <small>已减少背景噪声，可试听后选择使用。</small>
              <audio class="voice-preview" controls preload="metadata" :src="denoisedPreviewUrl"></audio>
              <div class="voice-denoise__choices" role="radiogroup" aria-label="选择声音克隆来源">
                <label><input v-model="cloneSource" type="radio" value="original" /> 使用原音</label>
                <label><input v-model="cloneSource" type="radio" value="denoised" /> 使用净化音</label>
              </div>
            </div>
            <button type="submit" class="voice-action voice-action--primary voice-action--submit" :disabled="bailianVoiceSaving || voiceSlotsFull || isTrimPanelOpen">
              {{ voiceSlotsFull ? "音色槽位已满" : isTrimPanelOpen ? "请先确认或取消裁剪" : bailianVoiceSaving ? "处理中…" : "创建音色" }}
            </button>
          </form>

          <div class="voice-result" aria-live="polite">{{ cloneResult }}</div>
        </section>
      </div>
    </div>
  </dialog>
</template>
