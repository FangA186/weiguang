<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from "vue";
import { storeToRefs } from "pinia";
import { usePersonaStore } from "../stores/personaStore";
import * as api from "../api";
import type { ChatImportBatch } from "../types";

const personaStore = usePersonaStore();
const { distillWizardOpen, selectedPersonaForEdit } = storeToRefs(personaStore);

const dialogRef = ref<HTMLDialogElement | null>(null);

const step = ref(1); // 1: 基本信息, 2: 素材选择, 3: 蒸馏中, 4: 完成预览

// Step 1
const name = ref("");
const slug = ref("");
const mbti = ref("INFP");
const attachmentStyle = ref("焦虑型依恋");
const selectedTags = ref<string[]>(["嘴硬心软", "高频波浪号"]);
const customNotes = ref("");

// Step 2
const importBatches = ref<ChatImportBatch[]>([]);
const selectedBatchIds = ref<number[]>([]);
const rawChatText = ref("");
const loadingBatches = ref(false);

// Presets
const PRESET_TAGS = [
  "焦虑型依恋", "回避型依恋", "安全型依恋", "傲娇 / 嘴硬心软",
  "高冷 / 理性脑", "黏人精 / 甜妹", "幽默逗比", "细节控",
  "爱吃醋", "高频波浪号", "连环短句", "极简回复"
];

const errorMsg = ref("");
const resultPersona = ref<any>(null);

function syncOpen() {
  const el = dialogRef.value;
  if (!el) return;
  if (distillWizardOpen.value && !el.open) {
    el.showModal();
    void loadChatImportBatches();
  } else if (!distillWizardOpen.value && el.open) {
    el.close();
  }
}

watch(distillWizardOpen, syncOpen);
watch(dialogRef, syncOpen);

onMounted(async () => {
  await loadChatImportBatches();
});

async function loadChatImportBatches() {
  loadingBatches.value = true;
  try {
    const res = await api.fetchChatImports({ limit: 20, offset: 0 });
    importBatches.value = res.batches || [];
  } catch {
    importBatches.value = [];
  } finally {
    loadingBatches.value = false;
  }
}

function toggleTag(tag: string) {
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter((t) => t !== tag);
  } else {
    selectedTags.value.push(tag);
  }
}

function toggleBatch(id: number) {
  if (selectedBatchIds.value.includes(id)) {
    selectedBatchIds.value = selectedBatchIds.value.filter((b) => b !== id);
  } else {
    selectedBatchIds.value.push(id);
  }
}

function close() {
  personaStore.closeDistillWizard();
  step.value = 1;
  errorMsg.value = "";
  resultPersona.value = null;
}

function closeOnBackdrop(event: MouseEvent) {
  if (event.target === dialogRef.value) {
    close();
  }
}

async function startDistillation() {
  const finalName = name.value.trim() || "伴侣";
  errorMsg.value = "";
  step.value = 3;

  try {
    // 1. Create or ensure persona
    let targetId = selectedPersonaForEdit.value?.id;
    if (!targetId) {
      const created = await personaStore.createNewPersona({
        name: finalName,
        slug: slug.value.trim() || undefined,
        source_type: selectedBatchIds.value.length > 0 ? "chat_import" : "text_input",
        source_import_ids: selectedBatchIds.value,
        is_active: false,
      });
      targetId = created.id;
    }

    // 2. Trigger Distillation
    const tags = Array.from(new Set([...selectedTags.value, mbti.value, attachmentStyle.value]));
    const descriptions = `【MBTI】: ${mbti.value}\n【依恋类型】: ${attachmentStyle.value}\n【特征备忘】: ${customNotes.value}`;

    const distilled = await personaStore.triggerDistill(targetId, {
      import_ids: selectedBatchIds.value,
      raw_chat_text: rawChatText.value.trim() || undefined,
      personality_tags: tags,
      user_descriptions: descriptions,
    });

    resultPersona.value = distilled;
    step.value = 4;
  } catch (err: any) {
    step.value = 2;
    errorMsg.value = err.message || "蒸馏失败，请重试";
  }
}

async function applyAndUse() {
  if (resultPersona.value?.id) {
    await personaStore.switchPersona(resultPersona.value.id);
  }
  close();
  personaStore.openWorkshop();
}

onBeforeUnmount(() => dialogRef.value?.close());
</script>

<template>
  <dialog ref="dialogRef" class="distill-dialog" @close="close" @click="closeOnBackdrop">
    <!-- Header -->
    <header class="distill-head">
      <div class="distill-head__title">
        <h2>✨ 智能人设与记忆蒸馏 (Zero-Prompt Distill)</h2>
        <span class="persona-badge">Ex-Skill 两阶段分析器</span>
      </div>
      <button type="button" class="distill-close" aria-label="关闭" @click="close">×</button>
    </header>

    <!-- Body -->
    <div class="distill-body">
      <!-- Steps Indicator -->
      <div class="wizard-steps">
        <div class="wizard-step" :class="{ 'is-active': step === 1, 'is-done': step > 1 }">
          <span class="wizard-step__num">1</span>
          <span>角色画像</span>
        </div>
        <div class="wizard-step" :class="{ 'is-active': step === 2, 'is-done': step > 2 }">
          <span class="wizard-step__num">2</span>
          <span>对话素材</span>
        </div>
        <div class="wizard-step" :class="{ 'is-active': step === 3, 'is-done': step > 3 }">
          <span class="wizard-step__num">3</span>
          <span>AI 蒸馏中</span>
        </div>
        <div class="wizard-step" :class="{ 'is-active': step === 4 }">
          <span class="wizard-step__num">4</span>
          <span>生成与激活</span>
        </div>
      </div>

      <div v-if="errorMsg" style="padding: 10px 16px; border-radius: 6px; background: rgba(239,68,68,0.15); color: #f87171; font-size: 0.82rem;">
        {{ errorMsg }}
      </div>

      <!-- Step 1: Basic Profile -->
      <div v-if="step === 1">
        <div class="p-form-group">
          <label class="p-label">角色姓名 / 昵称（选填，不填由 AI 自动推断）</label>
          <input v-model="name" class="p-input" placeholder="例如：林晚晚、小笨蛋，或留空自动识别" />
        </div>

        <div class="p-form-group">
          <label class="p-label">标识 Slug (英文唯一代号)</label>
          <input v-model="slug" class="p-input" placeholder="例如：wanwan" />
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div class="p-form-group">
            <label class="p-label">MBTI 性格类型</label>
            <select v-model="mbti" class="p-select">
              <option value="INFP">INFP (调停者 / 敏感深情)</option>
              <option value="INFJ">INFJ (提倡者 / 洞察体贴)</option>
              <option value="ENFP">ENFP (竞选者 / 热情小太阳)</option>
              <option value="INTJ">INTJ (建筑师 / 理性高冷)</option>
              <option value="ISFP">ISFP (探险家 / 随性温和)</option>
              <option value="ENTP">ENTP (辩论家 / 幽默逗比)</option>
              <option value="ISFJ">ISFJ (守卫者 / 默默奉献)</option>
              <option value="ESFJ">ESFJ (执政官 / 照顾型人格)</option>
            </select>
          </div>

          <div class="p-form-group">
            <label class="p-label">依恋类型 (Attachment Style)</label>
            <select v-model="attachmentStyle" class="p-select">
              <option value="焦虑型依恋">焦虑型依恋 (渴望确认 / 敏感容易多想)</option>
              <option value="回避型依恋">回避型依恋 (习惯退缩 / 口是心非)</option>
              <option value="安全型依恋">安全型依恋 (情绪稳定 / 积极沟通)</option>
              <option value="恐惧回避型">恐惧回避型 (渴望亲密又害怕受伤)</option>
            </select>
          </div>
        </div>

        <div class="p-form-group">
          <label class="p-label">性格特征标签（可多选）</label>
          <div class="p-tags">
            <button
              v-for="tag in PRESET_TAGS"
              :key="tag"
              type="button"
              class="p-tag-btn"
              :class="{ 'is-active': selectedTags.includes(tag) }"
              @click="toggleTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>

        <div class="p-form-group">
          <label class="p-label">其他特征备忘（可选，如：喜欢喝半糖抹茶、经常熬夜、生气时会发短句）</label>
          <textarea v-model="customNotes" class="p-textarea" rows="3" placeholder="填写能反映对方真实说话方式的细节备忘…"></textarea>
        </div>

        <div style="display: flex; justify-content: flex-end; margin-top: 16px;">
          <button type="button" class="p-btn p-btn-primary" :disabled="!name.trim()" @click="step = 2">
            下一步：选择素材 ›
          </button>
        </div>
      </div>

      <!-- Step 2: Chat Material Selection -->
      <div v-if="step === 2">
        <p class="p-label" style="margin-bottom: 8px;">
          选择用于人格蒸馏的素材来源（可多选已有截图批次，或直接粘贴聊天文本）：
        </p>

        <div class="p-form-group">
          <label class="p-label">① 已导入的微信/IM 聊天截图批次：</label>
          <div v-if="loadingBatches" style="font-size: 0.8rem; color: var(--text-dim); padding: 10px;">
            正在读取历史截图批次…
          </div>
          <div v-else-if="importBatches.length === 0" style="font-size: 0.8rem; color: var(--text-dim); padding: 12px; border: 1px dashed var(--line); border-radius: 6px; text-align: center;">
            暂无历史截图批次。可在主界面点击“导入图片”添加微信截图，或在下方直接粘贴聊天记录。
          </div>
          <div v-else class="batch-select-list">
            <div
              v-for="b in importBatches"
              :key="b.id"
              class="batch-select-item"
              @click="toggleBatch(b.id)"
            >
              <input type="checkbox" :checked="selectedBatchIds.includes(b.id)" />
              <div style="flex: 1;">
                <span style="font-size: 0.85rem; color: var(--text);">批次 #{{ b.id }}</span>
                <span style="font-size: 0.75rem; color: var(--text-dim); margin-left: 8px;">
                  ({{ b.messages?.length || 0 }} 条消息 · {{ new Date(b.created_at).toLocaleDateString('zh-CN') }})
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="p-form-group" style="margin-top: 16px;">
          <label class="p-label">② 直接粘贴聊天记录文本（格式不限）：</label>
          <textarea
            v-model="rawChatText"
            class="p-textarea"
            rows="6"
            placeholder="张三: 你在干嘛呢~
李四: 在发呆呀，今天好累哦🥺
张三: 晚上想吃啥？
李四: 随便叭，只要不吃香菜都行！"
          ></textarea>
        </div>

        <div style="display: flex; justify-content: space-between; margin-top: 16px;">
          <button type="button" class="p-btn p-btn-outline" @click="step = 1">
            ‹ 上一步
          </button>
          <button
            type="button"
            class="p-btn p-btn-primary"
            :disabled="selectedBatchIds.length === 0 && !rawChatText.trim() && !customNotes.trim()"
            @click="startDistillation"
          >
            🚀 开始智能蒸馏五层人设
          </button>
        </div>
      </div>

      <!-- Step 3: Distillation In Progress -->
      <div v-if="step === 3" class="p-loader">
        <div class="p-spinner"></div>
        <strong style="font-size: 1rem; color: var(--text);">AI 正在深度蒸馏五层人设与共同记忆…</strong>
        <p style="font-size: 0.8rem; color: var(--text-dim); max-width: 480px; text-align: center; line-height: 1.6;">
          正在分析：说话语气口癖、标点符号频率、Emoji 习惯、情绪反应动态机制、初识时间线与共同黑话事实库…
        </p>
      </div>

      <!-- Step 4: Complete & Preview -->
      <div v-if="step === 4 && resultPersona">
        <div style="padding: 16px; border-radius: 8px; background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.2rem;">🎉</span>
            <strong style="font-size: 0.95rem; color: #34d399;">恭喜！角色「{{ resultPersona.name }}」蒸馏完成</strong>
          </div>
          <p style="font-size: 0.8rem; color: var(--text-mid); margin-top: 6px;">
            已生成五层表达 DNA、情绪动力学矩阵及事实记忆库，并自动完成了 System Prompt 的编译。
          </p>
        </div>

        <div class="p-form-group">
          <label class="p-label">编译后生成的 System Instruction 预览：</label>
          <textarea
            :value="resultPersona.compiled_prompt"
            class="p-textarea p-textarea-code"
            rows="10"
            readonly
          ></textarea>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 16px;">
          <button type="button" class="p-btn p-btn-outline" @click="close">
            稍后在工坊中查看
          </button>
          <button type="button" class="p-btn p-btn-primary" @click="applyAndUse">
            立即启用并设为当前对话角色
          </button>
        </div>
      </div>
    </div>
  </dialog>
</template>
