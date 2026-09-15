<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "../stores/auth";
import { useVoiceConfigStore } from "../stores/voiceConfig";
import { usePersonaStore } from "../stores/personaStore";

const { variant = "chat" } = defineProps<{ variant?: "chat" | "voice" }>();

const auth = useAuthStore();
const voice = useVoiceConfigStore();
const persona = usePersonaStore();

const initial = computed(() => {
  const p = auth.profile;
  const base = (p?.nickname || p?.email || "我").trim().slice(0, 1);
  return base.toUpperCase();
});

function openVoiceSettings() {
  if (auth.profile) void voice.open(auth.profile.id);
}

function openPersonaWorkshop() {
  persona.openWorkshop();
}
</script>

<template>
  <header :class="variant === 'chat' ? 'cnav' : 'vnav'">
    <RouterLink :to="'/'" :class="variant === 'chat' ? 'cnav__back' : 'vnav__back'">
      <span :class="variant === 'chat' ? 'cnav__arrow' : 'vnav__arrow'" aria-hidden="true">←</span>
      <span>返回</span>
    </RouterLink>

    <div :class="variant === 'chat' ? 'cnav__brand' : 'vnav__brand'">
      <span :class="variant === 'chat' ? 'cnav__dot' : 'vnav__dot'"></span>
      <span :class="variant === 'chat' ? 'cnav__name' : 'vnav__name'">微光</span>
      <span :class="variant === 'chat' ? 'cnav__tag' : 'vnav__tag'">AI 陪伴</span>
    </div>

    <template v-if="variant === 'chat'">
      <div class="cnav__actions">
        <button v-if="false" type="button" class="cnav__voice" title="管理人物角色与五层人设" @click="openPersonaWorkshop">
          🎭 角色工坊
        </button>
        <button type="button" class="cnav__voice" @click="openVoiceSettings">克隆声音</button>
        <button type="button" class="cnav__profile" aria-label="个人中心" title="个人中心" @click="auth.openAccount()">
          <img v-if="auth.profile?.avatar_download_url" :src="auth.profile.avatar_download_url" alt="账号头像" />
          <span v-else>{{ initial }}</span>
        </button>
      </div>
    </template>
    <template v-else>
      <div class="cnav__actions">
        <button v-if="false" type="button" class="cnav__voice" @click="openPersonaWorkshop">🎭 角色工坊</button>
        <button type="button" class="cnav__voice" @click="openVoiceSettings">克隆声音</button>
      </div>
    </template>
  </header>
</template>
