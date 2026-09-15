<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from "vue";
import { storeToRefs } from "pinia";
import { usePersonaStore } from "../stores/personaStore";

const personaStore = usePersonaStore();
const { correctionDialogOpen, activePersona } = storeToRefs(personaStore);

const dialogRef = ref<HTMLDialogElement | null>(null);

const feedbackText = ref("");
const correctionType = ref<"linguistic" | "emotional" | "fact">("linguistic");
const targetLayer = ref("L2");
const submitting = ref(false);
const successMsg = ref("");
const errorMsg = ref("");

function syncOpen() {
  const el = dialogRef.value;
  if (!el) return;
  if (correctionDialogOpen.value && !el.open) {
    el.showModal();
  } else if (!correctionDialogOpen.value && el.open) {
    el.close();
  }
}

watch(correctionDialogOpen, syncOpen);
watch(dialogRef, syncOpen);

function close() {
  personaStore.closeCorrectionDialog();
  feedbackText.value = "";
  successMsg.value = "";
  errorMsg.value = "";
}

function closeOnBackdrop(event: MouseEvent) {
  if (event.target === dialogRef.value) {
    close();
  }
}

async function handleSubmit() {
  if (!feedbackText.value.trim() || !activePersona.value) return;
  submitting.value = true;
  errorMsg.value = "";
  successMsg.value = "";
  try {
    const record = await personaStore.submitCorrection(activePersona.value.id, {
      user_feedback: feedbackText.value.trim(),
      correction_type: correctionType.value,
      target_layer: targetLayer.value,
    });
    successMsg.value = `已成功提炼并注入规则：「${record.rule_text}」，下一轮对话立即生效！`;
    feedbackText.value = "";
    setTimeout(() => {
      if (successMsg.value) close();
    }, 2000);
  } catch (err: any) {
    errorMsg.value = err.message || "纠偏提炼失败，请重试";
  } finally {
    submitting.value = false;
  }
}

onBeforeUnmount(() => dialogRef.value?.close());
</script>

<template>
  <dialog ref="dialogRef" class="correction-dialog" @close="close" @click="closeOnBackdrop">
    <!-- Header -->
    <header class="correction-head">
      <div class="correction-head__title">
        <h2>🎯 人设动态调教 / 纠偏</h2>
        <span class="persona-badge">{{ activePersona?.name || '微光' }}</span>
      </div>
      <button type="button" class="correction-close" aria-label="关闭" @click="close">×</button>
    </header>

    <!-- Body -->
    <div class="correction-body">
      <div v-if="successMsg" style="padding: 12px 16px; border-radius: 6px; background: rgba(16,185,129,0.15); color: #34d399; font-size: 0.85rem; line-height: 1.5;">
        ✓ {{ successMsg }}
      </div>
      <div v-if="errorMsg" style="padding: 12px 16px; border-radius: 6px; background: rgba(239,68,68,0.15); color: #f87171; font-size: 0.85rem;">
        {{ errorMsg }}
      </div>

      <div class="p-form-group">
        <label class="p-label">纠偏类型</label>
        <div class="p-tags">
          <button
            type="button"
            class="p-tag-btn"
            :class="{ 'is-active': correctionType === 'linguistic' }"
            @click="correctionType = 'linguistic'; targetLayer = 'L2'"
          >
            🗣️ 语言/语气 (标点/口癖/句式)
          </button>
          <button
            type="button"
            class="p-tag-btn"
            :class="{ 'is-active': correctionType === 'emotional' }"
            @click="correctionType = 'emotional'; targetLayer = 'L3'"
          >
            💔 情绪动力学 (反应强度/脾气)
          </button>
          <button
            type="button"
            class="p-tag-btn"
            :class="{ 'is-active': correctionType === 'fact' }"
            @click="correctionType = 'fact'; targetLayer = 'L0'"
          >
            📌 事实/记忆纠正 (名字/硬规则)
          </button>
        </div>
      </div>

      <div class="p-form-group">
        <label class="p-label">你的自然语言反馈（直接说出对方哪里不像，或期望怎么表现）：</label>
        <textarea
          v-model="feedbackText"
          class="p-textarea"
          rows="4"
          placeholder="例如：
- 说话太官方了，不要每句话都带句号，多发~
- 生气的时候不要直接道歉，要傲娇一点单发'哦'
- 叫我笨蛋，别叫我的全名"
        ></textarea>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button type="button" class="p-btn p-btn-outline" @click="close">
          取消
        </button>
        <button
          type="button"
          class="p-btn p-btn-primary"
          :disabled="submitting || !feedbackText.trim()"
          @click="handleSubmit"
        >
          {{ submitting ? "提炼并注入中…" : "立即提炼并注入规则" }}
        </button>
      </div>
    </div>
  </dialog>
</template>
