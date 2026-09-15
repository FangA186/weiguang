<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { usePersonaStore } from "../stores/personaStore";
import { useVoiceConfigStore } from "../stores/voiceConfig";
import { useAuthStore } from "../stores/auth";
import type { PersonaRecord, PersonaStructured, PersonaMemories } from "../types";
import type { VoiceProfile } from '../types';
import VoiceProfileForm from './VoiceProfileForm.vue';

const personaStore = usePersonaStore();
const voiceConfigStore = useVoiceConfigStore();
const authStore = useAuthStore();

const {
  personas,
  activePersona,
  workshopDialogOpen,
  selectedPersonaForEdit,
  versions,
  corrections,
} = storeToRefs(personaStore);

const { voiceClones } = storeToRefs(voiceConfigStore);

const dialogRef = ref<HTMLDialogElement | null>(null);

// Active Tab in Editor
const activeTab = ref<"profile" | "expression" | "emotions" | "memories" | "corrections" | "versions" | "advanced">("profile");

// ---------------------------------------------------------------------------
// Friendly Visual Form Fields
// ---------------------------------------------------------------------------
const editName = ref("");
const editVoiceId = ref("");
const voicePickerRef = ref<HTMLElement | null>(null);
const voiceMenuOpen = ref(false);

// 1. Profile / 身份与画像
const mbti = ref("");
const attachmentStyle = ref("");
const selectedTags = ref<string[]>([]);
const roleDescription = ref("");
const characterCallsUser = ref("");
const userCallsCharacter = ref("");
const forbiddenTopics = ref("");

// 2. Expression DNA / 说话风格
const catchphrases = ref("");
const frequentEmojis = ref("");
const punctuationHabit = ref("");
const sentenceRhythm = ref("");
const voiceProfile = ref<VoiceProfile>({});

// 3. Emotional Dynamics / 情绪动力学
const joyExpression = ref("");
const angerTriggers = ref("");
const angerManifestation = ref("");
const repairPath = ref("");

// 4. Memories / 专属共同回忆
const insideJokes = ref("");
const dietaryLikes = ref("");
const dietaryDislikes = ref("");
const timelineText = ref("");
const livingHabits = ref("");

// 5. Advanced Raw JSON / Prompt
const editPersonaJSON = ref("");
const editMemoriesJSON = ref("");
const editPrompt = ref("");

// State
const saving = ref(false);
const saveSuccess = ref(false);
const saveError = ref("");
const newFeedback = ref("");
const addingCorr = ref(false);

const PRESET_TAGS = [
  "傲娇 / 嘴硬心软", "焦虑型依恋", "回避型依恋", "安全型依恋",
  "高冷 / 理性脑", "黏人精 / 甜妹", "幽默逗比", "细节控",
  "爱吃醋", "高频波浪号", "连环短句", "极简回复", "早起达人", "夜猫子"
];

const selectedVoiceLabel = computed(() => {
  const clone = voiceClones.value.find((voice) => voice.voice_id === editVoiceId.value);
  return clone ? `🎙️ 克隆音色：${clone.reference_filename}` : "🎙️ 系统默认音色（百炼官方）";
});

const MBTI_OPTIONS = [
  ["ISTJ", "ISTJ (务实可靠 / 秩序感)"], ["ISFJ", "ISFJ (温柔体贴 / 默默守护)"],
  ["INFJ", "INFJ (洞察体贴 / 灵魂伴侣)"], ["INTJ", "INTJ (理性独立 / 规划控)"],
  ["ISTP", "ISTP (冷静独立 / 鉴赏家)"], ["ISFP", "ISFP (随性温和 / 艺术气质)"],
  ["INFP", "INFP (敏感深情 / 理想主义者)"], ["INTP", "INTP (好奇理性 / 思考者)"],
  ["ESTP", "ESTP (直率果断 / 行动派)"], ["ESFP", "ESFP (热情随和 / 氛围感)"],
  ["ENFP", "ENFP (热情开朗 / 小太阳)"], ["ENTP", "ENTP (幽默机智 / 欢喜冤家)"],
  ["ESTJ", "ESTJ (干练可靠 / 执行派)"], ["ESFJ", "ESFJ (热情关怀 / 照顾型)"],
  ["ENFJ", "ENFJ (共情引导 / 温暖陪伴)"], ["ENTJ", "ENTJ (坚定自信 / 目标感)"],
] as const;

function normalizeMbti(value: unknown): string {
  return String(value || "").toUpperCase().match(/[EI][NS][TF][JP]/)?.[0] || "";
}

function normalizeAttachmentStyle(value: unknown): string {
  const text = String(value || "");
  if (text.includes("恐惧")) return "恐惧回避型";
  if (text.includes("焦虑")) return "焦虑型依恋";
  if (text.includes("回避")) return "回避型依恋";
  if (text.includes("安全")) return "安全型依恋";
  return "";
}

const INVALID_PERSONA_LABELS = new Set([
  "我", "用户", "对方", "未知", "自己", "ta", "ai", "助手", "系统消息", "时间", "日期",
  "system message", "system", "message", "伴侣", "未命名", "新角色",
]);

function cleanPersonaLabel(value: unknown): string {
  let text = String(value || "").trim();
  if (!text) return "";
  const quoted = text.match(/["'“”‘’「」『』【】]([^"'“”‘’「」『』【】\r\n]{1,24})["'“”‘’「」『』【】]/);
  text = (quoted?.[1] || text).trim().replace(/^["'“”‘’「」『』【】\s]+|["'“”‘’「」『』【】\s]+$/g, "");
  if (!text || INVALID_PERSONA_LABELS.has(text.toLowerCase()) || text.length > 24 || /[\r\n。！？!?；;]/.test(text)) return "";
  if (/(必须|应该|请|不要|不能|严禁|称呼|叫对方|称为|规则|系统提示|system\s+prompt|instruction)/i.test(text)) return "";
  return text;
}

function sanitizePersonaFields(persona: PersonaStructured, memories: PersonaMemories) {
  const layer0 = (persona.layer0_hard_rules ||= {});
  const layer1 = (persona.layer1_identity ||= {}) as PersonaStructured["layer1_identity"] & { character_name?: unknown };
  const petNames = (memories.pet_names ||= {});
  const characterCall = cleanPersonaLabel(petNames.character_calls_user || layer0.naming_rules);
  const userCall = cleanPersonaLabel(petNames.user_calls_character);
  if (characterCall) {
    layer0.naming_rules = `必须叫对方'${characterCall}'`;
    petNames.character_calls_user = characterCall;
  } else {
    delete layer0.naming_rules;
    delete petNames.character_calls_user;
  }
  if (userCall) petNames.user_calls_character = userCall;
  else delete petNames.user_calls_character;
  const characterName = cleanPersonaLabel(layer1.character_name);
  if (characterName) layer1.character_name = characterName;
  else delete layer1.character_name;
}

function syncOpen() {
  const el = dialogRef.value;
  if (!el) return;
  if (workshopDialogOpen.value && !el.open) {
    el.showModal();
  } else if (!workshopDialogOpen.value && el.open) {
    el.close();
  }
}

watch(workshopDialogOpen, syncOpen);
watch(dialogRef, syncOpen);

watch(
  () => selectedPersonaForEdit.value,
  (p) => {
    if (p) {
      loadPersonaToForm(p);
      personaStore.loadVersions(p.id);
      personaStore.loadCorrections(p.id);
    }
  },
  { immediate: true }
);

function loadPersonaToForm(p: PersonaRecord) {
  editName.value = p.name || "";
  editVoiceId.value = p.voice_id || "";

  const l0 = p.persona?.layer0_hard_rules || {};
  const l1 = p.persona?.layer1_identity || {};
  const l2 = p.persona?.layer2_expression_dna || {};
  const l3 = p.persona?.layer3_emotional_dynamics || {};
  const mem = p.memories || {};

  // Profile
  mbti.value = normalizeMbti(l1.mbti);
  attachmentStyle.value = normalizeAttachmentStyle(l1.attachment_style);
  selectedTags.value = Array.isArray(l1.tags) ? [...l1.tags] : (typeof l1.tags === "string" ? l1.tags.split(/[,，\s]+/).filter(Boolean) : []);
  roleDescription.value = l1.role_description || "";
  characterCallsUser.value = cleanPersonaLabel(mem.pet_names?.character_calls_user || l0.naming_rules);
  userCallsCharacter.value = cleanPersonaLabel(mem.pet_names?.user_calls_character || p.name);
  forbiddenTopics.value = Array.isArray(l0.forbidden_topics) ? l0.forbidden_topics.join("、") : (l0.forbidden_topics || "");

  // Expression
  catchphrases.value = Array.isArray(l2.catchphrases) ? l2.catchphrases.join("，") : (l2.catchphrases || "");
  frequentEmojis.value = Array.isArray(l2.frequent_emojis) ? l2.frequent_emojis.join(" ") : (l2.frequent_emojis || "");
  punctuationHabit.value = typeof l2.punctuation_habits === "object" ? JSON.stringify(l2.punctuation_habits) : (l2.punctuation_habits || "");
  sentenceRhythm.value = l2.sentence_rhythm || "";
  voiceProfile.value = JSON.parse(JSON.stringify(l2.voice_style || {}));

  // Emotions
  joyExpression.value = l3.joy_expression || "";
  angerTriggers.value = Array.isArray(l3.anger_triggers) ? l3.anger_triggers.join("、") : (l3.anger_triggers || "");
  angerManifestation.value = l3.anger_manifestation || "";
  repairPath.value = l3.repair_path || "";

  // Memories
  if (Array.isArray(mem.inside_jokes)) {
    insideJokes.value = mem.inside_jokes.map((j: any) => `${j.phrase || ''}: ${j.meaning || ''}`).join("\n");
  } else {
    insideJokes.value = "";
  }

  const prefs = mem.preferences || {};
  dietaryLikes.value = Array.isArray(prefs.dietary_likes) ? prefs.dietary_likes.join("、") : (prefs.dietary_likes || "");
  dietaryDislikes.value = Array.isArray(prefs.dietary_dislikes) ? prefs.dietary_dislikes.join("、") : (prefs.dietary_dislikes || "");
  livingHabits.value = Array.isArray(prefs.living_habits) ? prefs.living_habits.join("、") : (prefs.living_habits || "");

  if (Array.isArray(mem.timeline)) {
    timelineText.value = mem.timeline.map((t: any) => `${t.date || ''}: ${t.event || ''} ${t.details ? `(${t.details})` : ''}`.trim()).join("\n");
  } else {
    timelineText.value = "";
  }

  // Advanced Raw JSON
  editPersonaJSON.value = JSON.stringify(p.persona || {}, null, 2);
  editMemoriesJSON.value = JSON.stringify(p.memories || {}, null, 2);
  editPrompt.value = p.compiled_prompt || "";
}

function toggleTag(tag: string) {
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter((t) => t !== tag);
  } else {
    selectedTags.value.push(tag);
  }
}

function close() {
  personaStore.closeWorkshop();
}

function closeOnBackdrop(event: MouseEvent) {
  if (event.target === dialogRef.value) {
    close();
  }
}

function selectPersona(p: PersonaRecord) {
  selectedPersonaForEdit.value = p;
  saveSuccess.value = false;
  saveError.value = "";
}

async function handleActivate(p: PersonaRecord) {
  await personaStore.switchPersona(p.id);
}

async function handleDelete(p: PersonaRecord) {
  if (confirm(`确定要删除角色「${p.name}」吗？`)) {
    await personaStore.removePersona(p.id);
    if (selectedPersonaForEdit.value?.id === p.id) {
      selectedPersonaForEdit.value = activePersona.value || personas.value[0] || null;
    }
  }
}

async function handleSave() {
  if (!selectedPersonaForEdit.value) return;
  saving.value = true;
  saveSuccess.value = false;
  saveError.value = "";

  try {
    let personaObj: PersonaStructured;
    let memoriesObj: PersonaMemories;

    if (activeTab.value === "advanced") {
      try {
        personaObj = JSON.parse(editPersonaJSON.value);
        memoriesObj = JSON.parse(editMemoriesJSON.value);
      } catch (e: any) {
        throw new Error("高级模式中的 JSON 格式有误: " + e.message);
      }
    } else {
      // Assemble from visual form fields
      personaObj = {
        layer0_hard_rules: {
          naming_rules: cleanPersonaLabel(characterCallsUser.value) ? `必须叫对方'${cleanPersonaLabel(characterCallsUser.value)}'` : "保持温和称呼",
          forbidden_topics: forbiddenTopics.value.split(/[、,，\n]+/).map(s => s.trim()).filter(Boolean),
          defensive_mechanism: selectedPersonaForEdit.value.persona?.layer0_hard_rules?.defensive_mechanism || "被质疑时保持角色性格特质",
        },
        layer1_identity: {
          role_description: roleDescription.value.trim(),
          mbti: mbti.value,
          attachment_style: attachmentStyle.value,
          core_motivation: selectedPersonaForEdit.value.persona?.layer1_identity?.core_motivation || "陪伴与情感共鸣",
          tags: selectedTags.value,
        },
        layer2_expression_dna: {
          catchphrases: catchphrases.value.split(/[、,，\n]+/).map(s => s.trim()).filter(Boolean),
          frequent_emojis: frequentEmojis.value.split(/[\s,，]+/).map(s => s.trim()).filter(Boolean),
          punctuation_habits: punctuationHabit.value.trim(),
          sentence_rhythm: sentenceRhythm.value.trim(),
          voice_style: voiceProfile.value,
        },
        layer3_emotional_dynamics: {
          joy_expression: joyExpression.value.trim(),
          anger_triggers: angerTriggers.value.split(/[、,，\n]+/).map(s => s.trim()).filter(Boolean),
          anger_manifestation: angerManifestation.value.trim(),
          repair_path: repairPath.value.trim(),
        },
        layer4_conflict_patterns: selectedPersonaForEdit.value.persona?.layer4_conflict_patterns || {
          disagreement_handling: "依恋类型驱动的处理模式",
          stress_response: "退缩或寻求安抚",
        },
      };

      // Assemble memories
      const parsedJokes = insideJokes.value.split("\n").filter(Boolean).map(line => {
        const parts = line.split(/[:：]/);
        return { phrase: parts[0]?.trim() || line, meaning: parts[1]?.trim() || "" };
      });

      const parsedTimeline = timelineText.value.split("\n").filter(Boolean).map(line => {
        const match = line.match(/^([^\s:：]+)[:：\s]+([^(（]+)(?:[(（]([^)）]+)[)）])?/);
        if (match) {
          return { date: match[1]?.trim(), event: match[2]?.trim(), details: match[3]?.trim() || "" };
        }
        return { date: "重要节点", event: line.trim() };
      });

      memoriesObj = {
        pet_names: {
          ...(cleanPersonaLabel(characterCallsUser.value) ? { character_calls_user: cleanPersonaLabel(characterCallsUser.value) } : {}),
          ...(cleanPersonaLabel(userCallsCharacter.value) ? { user_calls_character: cleanPersonaLabel(userCallsCharacter.value) } : {}),
        },
        inside_jokes: parsedJokes,
        timeline: parsedTimeline,
        preferences: {
          dietary_likes: dietaryLikes.value.split(/[、,，\n]+/).map(s => s.trim()).filter(Boolean),
          dietary_dislikes: dietaryDislikes.value.split(/[、,，\n]+/).map(s => s.trim()).filter(Boolean),
          living_habits: livingHabits.value.split(/[、,，\n]+/).map(s => s.trim()).filter(Boolean),
        },
      };
    }

    sanitizePersonaFields(personaObj, memoriesObj);

    const updated = await personaStore.savePersona(selectedPersonaForEdit.value.id, {
      name: editName.value.trim(),
      slug: selectedPersonaForEdit.value.slug,
      voice_id: editVoiceId.value || undefined,
      persona: personaObj,
      memories: memoriesObj,
      compiled_prompt: activeTab.value === "advanced" ? editPrompt.value : undefined,
    });

    selectedPersonaForEdit.value = updated;
    loadPersonaToForm(updated);
    saveSuccess.value = true;
    setTimeout(() => {
      saveSuccess.value = false;
    }, 3000);
  } catch (err: any) {
    saveError.value = err.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

async function handleQuickCorrection() {
  if (!selectedPersonaForEdit.value || !newFeedback.value.trim()) return;
  addingCorr.value = true;
  try {
    await personaStore.submitCorrection(selectedPersonaForEdit.value.id, {
      user_feedback: newFeedback.value.trim(),
      correction_type: "linguistic",
    });
    newFeedback.value = "";
  } catch (err: any) {
    alert("纠偏提炼失败: " + err.message);
  } finally {
    addingCorr.value = false;
  }
}

async function handleToggleCorrection(c: any) {
  if (!selectedPersonaForEdit.value) return;
  await personaStore.toggleCorrectionStatus(selectedPersonaForEdit.value.id, c.id, !c.is_active);
}

async function handleDeleteCorrection(cid: number) {
  if (!selectedPersonaForEdit.value) return;
  await personaStore.removeCorrection(selectedPersonaForEdit.value.id, cid);
}

async function handleRollback(v: any) {
  if (!selectedPersonaForEdit.value) return;
  if (confirm(`确定要回滚到快照「${v.version_tag}」吗？`)) {
    const rolled = await personaStore.rollback(selectedPersonaForEdit.value.id, v.id);
    selectedPersonaForEdit.value = rolled;
  }
}

function handleCreateNew() {
  personaStore.openDistillWizard();
}

function openVoiceCloneSettings() {
  if (authStore.profile) {
    void voiceConfigStore.open(authStore.profile.id);
  }
}

function selectVoice(voiceId: string) {
  editVoiceId.value = voiceId;
  voiceMenuOpen.value = false;
}

function closeVoiceMenuOnOutsidePointer(event: PointerEvent) {
  if (!voicePickerRef.value?.contains(event.target as Node)) voiceMenuOpen.value = false;
}

onMounted(() => document.addEventListener("pointerdown", closeVoiceMenuOnOutsidePointer));
onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", closeVoiceMenuOnOutsidePointer);
  dialogRef.value?.close();
});
</script>

<template>
  <dialog ref="dialogRef" class="persona-dialog" @close="close" @click="closeOnBackdrop">
    <!-- Header -->
    <header class="persona-head">
      <div class="persona-head__title">
        <h2>🎭 角色与人设工坊</h2>
        <span class="persona-badge">专属 AI 伴侣定制</span>
      </div>
      <button type="button" class="persona-close" aria-label="关闭" @click="close">×</button>
    </header>

    <!-- Body: Two-Column Layout -->
    <div class="persona-body">
      <!-- Left Sidebar: Persona Cards -->
      <aside class="persona-sidebar">
        <div class="persona-sidebar__actions">
          <button type="button" class="p-btn p-btn-primary" style="width: 100%;" @click="handleCreateNew">
            ✨ 智能蒸馏 / 新建角色
          </button>
        </div>

        <div class="persona-list">
          <div
            v-for="p in personas"
            :key="p.id"
            class="persona-card"
            :class="{ 'is-selected': selectedPersonaForEdit?.id === p.id }"
            @click="selectPersona(p)"
          >
            <div class="persona-card__avatar">
              {{ (p.name || "微").slice(0, 1) }}
            </div>
            <div class="persona-card__main">
              <div class="persona-card__top">
                <span class="persona-card__name">{{ p.name }}</span>
                <span v-if="p.is_active" class="persona-card__badge">当前使用</span>
              </div>
              <div class="persona-card__meta">
                <span v-if="p.persona?.layer1_identity?.mbti">{{ p.persona.layer1_identity.mbti }} · </span>
                <span>{{ p.persona?.layer1_identity?.attachment_style || '专属角色' }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Right Main: Visual Persona Editor -->
      <main class="persona-main" v-if="selectedPersonaForEdit">
        <!-- Main Top Bar -->
        <div class="persona-main__header">
          <div class="persona-main__info">
            <div class="persona-header-field">
              <label class="persona-header-label" for="persona-name">角色名称</label>
              <input id="persona-name" v-model="editName" class="p-input persona-name-input" placeholder="例如：晚晚、阿泽" title="这是角色名称，不是系统指令；保存后可作为 AI 的称呼使用。" />
            </div>
            <div class="persona-header-field">
              <label class="persona-header-label" for="persona-voice">朗读与通话音色</label>
              <div class="persona-voice-controls">
                <div ref="voicePickerRef" class="persona-voice-picker" @keydown.esc.prevent.stop="voiceMenuOpen = false">
                  <button
                    id="persona-voice"
                    type="button"
                    class="persona-voice-trigger"
                    :aria-expanded="voiceMenuOpen"
                    aria-haspopup="listbox"
                    aria-controls="persona-voice-options"
                    title="为此角色绑定朗读与语音通话的音色"
                    @click="voiceMenuOpen = !voiceMenuOpen"
                  >
                    <span class="persona-voice-trigger__label">{{ selectedVoiceLabel }}</span>
                    <span class="persona-voice-trigger__arrow" aria-hidden="true">⌄</span>
                  </button>
                  <div v-if="voiceMenuOpen" id="persona-voice-options" class="persona-voice-menu" role="listbox" aria-label="朗读与通话音色">
                    <button type="button" class="persona-voice-option" :class="{ 'is-selected': !editVoiceId }" role="option" :aria-selected="!editVoiceId" @click="selectVoice('')">
                      🎙️ 系统默认音色（百炼官方）
                    </button>
                    <button v-for="vc in voiceClones" :key="vc.voice_id" type="button" class="persona-voice-option" :class="{ 'is-selected': editVoiceId === vc.voice_id }" role="option" :aria-selected="editVoiceId === vc.voice_id" @click="selectVoice(vc.voice_id)">
                      🎙️ 克隆音色：{{ vc.reference_filename }}
                    </button>
                  </div>
                </div>
                <button
                  type="button"
                  class="p-btn p-btn-outline persona-clone-button"
                  title="上传参考音频克隆该角色的声音"
                  @click="openVoiceCloneSettings"
                >
                  + 克隆新音色
                </button>
              </div>
            </div>
          </div>

          <div class="persona-main__actions">
            <button
              v-if="!selectedPersonaForEdit.is_active"
              type="button"
              class="p-btn p-btn-success"
              @click="handleActivate(selectedPersonaForEdit)"
            >
              ✓ 设为当前伴聊
            </button>
            <button
              type="button"
              class="p-btn p-btn-primary"
              :disabled="saving"
              @click="handleSave"
            >
              {{ saving ? "保存中…" : "保存修改" }}
            </button>
            <button
              v-if="!selectedPersonaForEdit.is_builtin"
              type="button"
              class="p-btn p-btn-danger"
              @click="handleDelete(selectedPersonaForEdit)"
            >
              删除
            </button>
          </div>
        </div>

        <!-- Auto Generated Success Banner -->
        <div
          v-if="personaStore.justAutoGenerated"
          style="padding: 14px 20px; background: rgba(236,215,175,0.14); border: 1px solid rgba(236,215,175,0.35); margin: 16px 24px 0; border-radius: 8px; font-size: 0.86rem; color: #ecd7af; display: flex; align-items: center; justify-content: space-between; gap: 14px;"
        >
          <div>
            🎉 <strong>已根据您的聊天截图自动提炼专属角色【{{ selectedPersonaForEdit.name }}】！</strong><br>
            AI 已自动推导出五层人设、表达习惯与专属回忆。如果对某些细节不满意，可随时在下方各个标签页中手动微调并保存。
          </div>
          <button
            type="button"
            class="p-btn p-btn-outline"
            style="font-size: 0.78rem; padding: 4px 12px; flex-shrink: 0; white-space: nowrap;"
            @click="personaStore.justAutoGenerated = false"
          >
            我知道了
          </button>
        </div>

        <!-- Friendly Distill Tip Banner when role is clean/empty -->
        <div
          v-if="!personaStore.justAutoGenerated && !selectedPersonaForEdit.persona?.layer1_identity?.role_description && !selectedPersonaForEdit.memories?.timeline?.length"
          style="padding: 12px 20px; background: rgba(236,215,175,0.08); border-left: 3px solid #ecd7af; margin: 16px 24px 0; border-radius: 6px; font-size: 0.82rem; color: #ecd7af; display: flex; align-items: center; justify-content: space-between; gap: 12px;"
        >
          <span>💡 <strong>全自动提炼提示</strong>：这些性格、口癖与记忆无需手动逐项填写！点击「✨ 智能蒸馏 / 新建角色」或在主页「导入图片」，AI 会自动分析微信聊天记录并一键填满人设。此处仅供查看和微调。</span>
          <button type="button" class="p-btn p-btn-primary" style="font-size: 0.76rem; padding: 4px 12px; flex-shrink: 0;" @click="handleCreateNew">
            去智能蒸馏
          </button>
        </div>

        <div v-if="saveSuccess" style="padding: 10px 24px; background: rgba(16,185,129,0.16); color: #34d399; font-size: 0.82rem;">
          ✓ 角色人设与专属记忆已成功保存，已自动重新编译 System Prompt！
        </div>
        <div v-if="saveError" style="padding: 10px 24px; background: rgba(239,68,68,0.16); color: #f87171; font-size: 0.82rem;">
          {{ saveError }}
        </div>

        <!-- Navigation Tabs -->
        <div class="persona-main__tabs">
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'profile' }"
            @click="activeTab = 'profile'"
          >
            👤 基本画像
          </button>
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'expression' }"
            @click="activeTab = 'expression'"
          >
            💬 说话风格
          </button>
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'emotions' }"
            @click="activeTab = 'emotions'"
          >
            💖 情绪与脾气
          </button>
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'memories' }"
            @click="activeTab = 'memories'"
          >
            📖 专属回忆库
          </button>
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'corrections' }"
            @click="activeTab = 'corrections'"
          >
            🎯 调教记录 ({{ corrections.length }})
          </button>
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'versions' }"
            @click="activeTab = 'versions'"
          >
            🕒 历史快照 ({{ versions.length }})
          </button>
          <button
            type="button"
            class="persona-tab"
            :class="{ 'is-active': activeTab === 'advanced' }"
            @click="activeTab = 'advanced'"
          >
            ⚙️ 高级模式
          </button>
        </div>

        <!-- Tab Content -->
        <div class="persona-tab-content">
          <!-- TAB 1: 身份与画像 -->
          <div v-if="activeTab === 'profile'" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="form-card">
              <div class="form-card__title">🏷️ 性格定位与心理特征</div>
              <div class="form-grid-2">
                <div class="p-form-group">
                  <label class="p-label">MBTI 性格类型</label>
                  <select v-model="mbti" class="p-select">
                    <option value="">未识别</option>
                    <option v-for="[value, label] in MBTI_OPTIONS" :key="value" :value="value">{{ label }}</option>
                  </select>
                </div>
                <div class="p-form-group">
                  <label class="p-label">依恋类型</label>
                  <select v-model="attachmentStyle" class="p-select">
                    <option value="">未识别</option>
                    <option value="焦虑型依恋">焦虑型依恋 (渴望确认 / 敏感容易多想)</option>
                    <option value="回避型依恋">回避型依恋 (习惯退缩 / 口是心非)</option>
                    <option value="安全型依恋">安全型依恋 (情绪稳定 / 积极沟通)</option>
                    <option value="恐惧回避型">恐惧回避型 (渴望亲密又害怕受伤)</option>
                  </select>
                </div>
              </div>

              <div class="p-form-group">
                <label class="p-label">性格特征标签</label>
                <div class="p-tags">
                  <button
                    v-for="t in PRESET_TAGS"
                    :key="t"
                    type="button"
                    class="p-tag-btn"
                    :class="{ 'is-active': selectedTags.includes(t) }"
                    @click="toggleTag(t)"
                  >
                    {{ t }}
                  </button>
                </div>
              </div>

              <div class="p-form-group">
                <label class="p-label">性格与角色简述</label>
                <textarea
                  v-model="roleDescription"
                  class="p-textarea"
                  rows="3"
                  placeholder="例如：嘴硬心软的青梅竹马，表面上喜欢怼你，其实内心非常在乎你的每一个小情绪…"
                ></textarea>
              </div>
            </div>

            <div class="form-card">
              <div class="form-card__title">👥 专属称呼与避雷话题</div>
              <div class="form-grid-2">
                <div class="p-form-group">
                  <label class="p-label">TA 对我的称呼</label>
                  <input v-model="characterCallsUser" class="p-input" placeholder="例如：笨蛋、猪头、哥哥、小林" />
                </div>
                <div class="p-form-group">
                  <label class="p-label">我怎么称呼 TA</label>
                  <input v-model="userCallsCharacter" class="p-input" placeholder="例如：晚晚、小笨蛋、阿泽" />
                </div>
              </div>
              <div class="p-form-group">
                <label class="p-label">
                  <span>避雷/禁忌话题</span>
                  <span class="p-label-hint">（AI 会主动规避或表现出抵触）</span>
                </label>
                <input v-model="forbiddenTopics" class="p-input" placeholder="例如：前任、相亲、高考成绩（用顿号或逗号分隔）" />
              </div>
            </div>
          </div>

          <!-- TAB 2: 说话风格 -->
          <div v-if="activeTab === 'expression'" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="form-card">
              <div class="form-card__title">💬 语言习惯与口癖</div>
              <div class="p-form-group">
                <label class="p-label">口头禅 / 高频词</label>
                <input v-model="catchphrases" class="p-input" placeholder="例如：好叭、哼、绝了、知道啦、哎呀（用逗号隔开）" />
              </div>

              <div class="p-form-group">
                <label class="p-label">常用 Emoji / 表情</label>
                <input v-model="frequentEmojis" class="p-input" placeholder="例如：🥺 🙄 🤍 🐾 [旺柴]（空格隔开）" />
              </div>
            </div>

            <div class="form-card">
              <div class="form-card__title">⌨️ 标点与打字节奏</div>
              <div class="form-grid-2">
                <div class="p-form-group">
                  <label class="p-label">标点符号偏好</label>
                  <input v-model="punctuationHabit" class="p-input" placeholder="例如：句尾爱用~，从不打句号" />
                </div>
                <div class="p-form-group">
                  <label class="p-label">回复长短与节奏</label>
                  <input v-model="sentenceRhythm" class="p-input" placeholder="例如：喜欢连发2-3条短句、极简回复" />
                </div>
              </div>
            </div>

            <div class="form-card">
              <div class="form-card__title">🔊 朗读声音表现</div>
              <VoiceProfileForm v-model="voiceProfile" />
            </div>
          </div>

          <!-- TAB 3: 情绪与脾气 -->
          <div v-if="activeTab === 'emotions'" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="form-card">
              <div class="form-card__title">🥰 开心与脆弱时刻</div>
              <div class="p-form-group">
                <label class="p-label">开心/被夸时的表现</label>
                <textarea
                  v-model="joyExpression"
                  class="p-textarea"
                  rows="2"
                  placeholder="例如：连发感叹号和可爱的表情包，傲娇地说'那当然啦~'"
                ></textarea>
              </div>
            </div>

            <div class="form-card">
              <div class="form-card__title">😤 闹脾气与哄好指南</div>
              <div class="p-form-group">
                <label class="p-label">生气 / 吃醋触发点</label>
                <input v-model="angerTriggers" class="p-input" placeholder="例如：回复超过半小时、提到其他异性、敷衍回复" />
              </div>
              <div class="p-form-group">
                <label class="p-label">生气时的具体反应</label>
                <textarea
                  v-model="angerManifestation"
                  class="p-textarea"
                  rows="2"
                  placeholder="例如：单发'哦'或'随便'，字数突然变少，撤回消息"
                ></textarea>
              </div>
              <div class="p-form-group">
                <label class="p-label">正确的哄好方式</label>
                <textarea
                  v-model="repairPath"
                  class="p-textarea"
                  rows="2"
                  placeholder="例如：诚恳认错、主动打电话连麦、买奶茶或发小红包"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- TAB 4: 专属回忆库 -->
          <div v-if="activeTab === 'memories'" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="form-card">
              <div class="form-card__title">🤫 只有你们懂的专属黑话 / 秘密梗</div>
              <div class="p-form-group">
                <label class="p-label">
                  <span>黑话列表（每行一条，格式为：词语: 含义）</span>
                </label>
                <textarea
                  v-model="insideJokes"
                  class="p-textarea"
                  rows="4"
                  placeholder="小肥猪: 吃火锅抢肉的梗
星期四: 疯狂星期四一起吃炸鸡的约定
秘密基地: 学校东门的星巴克二楼"
                ></textarea>
              </div>
            </div>

            <div class="form-card">
              <div class="form-card__title">🍜 生活喜好与饮食习惯</div>
              <div class="form-grid-2">
                <div class="p-form-group">
                  <label class="p-label">喜欢的食物 / 饮品</label>
                  <input v-model="dietaryLikes" class="p-input" placeholder="例如：半糖抹茶、海底捞、草莓蛋糕" />
                </div>
                <div class="p-form-group">
                  <label class="p-label">忌口 / 讨厌的食物</label>
                  <input v-model="dietaryDislikes" class="p-input" placeholder="例如：香菜、生洋葱、太辣的" />
                </div>
              </div>
              <div class="p-form-group">
                <label class="p-label">生活习惯与愿望清单</label>
                <input v-model="livingHabits" class="p-input" placeholder="例如：习惯晚睡熬夜、想一起去大理看苍山洱海" />
              </div>
            </div>

            <div class="form-card">
              <div class="form-card__title">📅 共同经历与纪念日时间线</div>
              <div class="p-form-group">
                <label class="p-label">
                  <span>时间线回忆（每行一条，格式为：时间: 事件 (细节)）</span>
                </label>
                <textarea
                  v-model="timelineText"
                  class="p-textarea"
                  rows="4"
                  placeholder="2023-05: 在星巴克初次相遇 (点了抹茶拿铁)
2023-10: 威海看日落 (吹着海风喝奶茶)
2024-02: 第一次一起跨年"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- TAB 5: 调教记录 -->
          <div v-if="activeTab === 'corrections'" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="form-card">
              <div class="form-card__title">🎯 快捷调教新规则</div>
              <p style="font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-bottom: 8px;">
                当你在聊天时发现对方说话不像或习惯不符，输入你的真实期望，AI 会自动提炼为高优先级规则注入：
              </p>
              <div style="display: flex; gap: 10px;">
                <input
                  v-model="newFeedback"
                  class="p-input"
                  placeholder="例如：说话不要太客气，多用~波浪号，叫我笨蛋"
                  @keydown.enter="handleQuickCorrection"
                />
                <button
                  type="button"
                  class="p-btn p-btn-primary"
                  :disabled="addingCorr || !newFeedback.trim()"
                  @click="handleQuickCorrection"
                >
                  {{ addingCorr ? "提炼中…" : "添加规则" }}
                </button>
              </div>
            </div>

            <div v-if="corrections.length === 0" style="padding: 30px; text-align: center; color: rgba(255,255,255,0.4); font-size: 0.88rem;">
              暂无调教记录。在聊天气泡旁点击 🎯 或在上方输入即可实时纠偏。
            </div>

            <div
              v-for="c in corrections"
              :key="c.id"
              class="correction-item"
            >
              <div class="correction-item__content">
                <span class="correction-type-badge" :class="c.correction_type">{{ c.correction_type }}</span>
                <strong style="font-size: 0.88rem; color: #ffffff;">{{ c.rule_text }}</strong>
                <p style="font-size: 0.76rem; color: rgba(255,255,255,0.5); margin-top: 4px;">反馈依据：{{ c.user_feedback }}</p>
              </div>
              <div style="display: flex; gap: 8px;">
                <button
                  type="button"
                  class="p-btn p-btn-outline"
                  style="font-size: 0.74rem; padding: 4px 10px;"
                  @click="handleToggleCorrection(c)"
                >
                  {{ c.is_active ? "已生效" : "已暂停" }}
                </button>
                <button
                  type="button"
                  class="p-btn p-btn-danger"
                  style="font-size: 0.74rem; padding: 4px 10px;"
                  @click="handleDeleteCorrection(c.id)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>

          <!-- TAB 6: 历史快照 -->
          <div v-if="activeTab === 'versions'" style="display: flex; flex-direction: column; gap: 16px;">
            <div v-if="versions.length === 0" style="padding: 30px; text-align: center; color: rgba(255,255,255,0.4); font-size: 0.88rem;">
              暂无历史快照。每次智能蒸馏或保存重要修改时会自动生成版本快照。
            </div>

            <div
              v-for="v in versions"
              :key="v.id"
              class="version-item"
            >
              <div>
                <strong style="font-size: 0.9rem; color: #ffffff;">快照 {{ v.version_tag }}</strong>
                <span style="font-size: 0.76rem; color: rgba(255,255,255,0.45); margin-left: 10px;">{{ new Date(v.created_at).toLocaleString('zh-CN') }}</span>
                <p style="font-size: 0.8rem; color: rgba(255,255,255,0.7); margin-top: 4px;">{{ v.message || '常规修改快照' }}</p>
              </div>
              <button
                type="button"
                class="p-btn p-btn-outline"
                style="font-size: 0.78rem;"
                @click="handleRollback(v)"
              >
                ↩ 回滚到此版本
              </button>
            </div>
          </div>

          <!-- TAB 7: 高级开发者模式 -->
          <div v-if="activeTab === 'advanced'" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="form-card">
              <div class="form-card__title">📜 完整编译指令 (System Prompt)</div>
              <p class="p-label" style="margin-bottom: 8px;">
                这是系统组装后直接注入大模型的完整 System Instruction：
              </p>
              <textarea
                v-model="editPrompt"
                class="p-textarea p-textarea-code"
                rows="10"
                spellcheck="false"
              ></textarea>
            </div>

            <div class="form-card">
              <div class="form-card__title">🧬 底层五层人设 JSON</div>
              <textarea
                v-model="editPersonaJSON"
                class="p-textarea p-textarea-code"
                rows="10"
                spellcheck="false"
              ></textarea>
            </div>

            <div class="form-card">
              <div class="form-card__title">📖 底层共同记忆库 JSON</div>
              <textarea
                v-model="editMemoriesJSON"
                class="p-textarea p-textarea-code"
                rows="8"
                spellcheck="false"
              ></textarea>
            </div>
          </div>
        </div>
      </main>
    </div>
  </dialog>
</template>
