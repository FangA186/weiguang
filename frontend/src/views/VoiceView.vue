<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import OrbCanvas from "../components/OrbCanvas.vue";
import AppNav from "../components/AppNav.vue";
import PersonaWorkshopDialog from "../components/PersonaWorkshopDialog.vue";
import { isQuotaExceededError, quotaExceededMessage, streamChat, streamChatAndTTS } from "../api";
import { useAuthStore } from "../stores/auth";
import { useVoiceConfigStore } from "../stores/voiceConfig";
import { usePersonaStore } from "../stores/personaStore";
import type { OrbState } from "../composables/useOrb";
import type { BailianStreamEvent } from "../types";
import { PCMStreamPlayer } from "../lib/pcmStreamPlayer";
import "../assets/styles/voice.css";

const router = useRouter();
const auth = useAuthStore();
const voice = useVoiceConfigStore();
const personaStore = usePersonaStore();
const orbState = ref<OrbState>("idle");
const statusText = ref("轻触光球，开始说话");
const tapHint = ref("轻触开始");
const lines = ref<Array<{ id: number; text: string; who: "ai" | "user" }>>([]);

let lineId = 0;
let active = false;
let busy = false;
let recognition: any = null;
let recognitionStarting = false;
let activeStreamPlayer: PCMStreamPlayer | null = null;
let activeTurnAbort: AbortController | null = null;
let audioPlaying = false;
let audioCooldownUntil = 0;
let voiceTextOnly = false;

function addLine(text: string, who: "ai" | "user") {
  lines.value.push({ id: ++lineId, text, who });
  while (lines.value.length > 4) lines.value.shift();
}

function setState(state: OrbState) {
  orbState.value = state;
  statusText.value = state === "idle"
    ? "轻触光球，开始说话"
    : state === "listening" ? (voiceTextOnly ? "正在聆听…（仅文字回答）" : "正在聆听…")
      : state === "thinking" ? "正在想想…" : "回应中";
  tapHint.value = { idle: "轻触开始", listening: "正在聆听", thinking: "请稍候", speaking: "轻触打断" }[state];
}

function stopAudio() {
  activeStreamPlayer?.stop();
  activeStreamPlayer = null;
  audioPlaying = false;
  audioCooldownUntil = Date.now() + 700;
}

function abortActiveTurn(reason = "voice-interrupted") {
  activeTurnAbort?.abort(reason);
}

function stopRecognition() {
  const current = recognition;
  recognition = null;
  recognitionStarting = false;
  if (current) {
    try { current.stop(); } catch { /* already stopped */ }
  }
}

function startRecognition() {
  if (!active || busy || recognition || recognitionStarting) return;
  if (audioPlaying || Date.now() < audioCooldownUntil) {
    window.setTimeout(startRecognition, Math.max(120, audioCooldownUntil - Date.now()));
    return;
  }
  const Recognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!Recognition) {
    addLine("当前浏览器不支持语音转写，请返回聊天页使用文字输入。", "ai");
    active = false;
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
    if (final && text.trim()) {
      stopRecognition();
      void submitTurn(text.trim());
    }
  };
  current.onerror = (event: any) => {
    recognitionStarting = false;
    if (event?.error === "not-allowed" || event?.error === "service-not-allowed") {
      addLine("浏览器没有授予麦克风或语音识别权限。", "ai");
      active = false;
      setState("idle");
    }
  };
  current.onend = () => {
    recognitionStarting = false;
    if (recognition === current) recognition = null;
    if (active && !busy) window.setTimeout(startRecognition, 180);
  };
  recognition = current;
  try { current.start(); } catch { recognitionStarting = false; recognition = null; }
}

async function submitTurn(text: string) {
  if (!text || busy) return;
  await auth.ensureReady();
  await voice.ensureReady(auth.profile!.id);
  addLine(text, "user");
  busy = true;
  setState("thinking");
  let answerText = "";
  let streamError = "";
  let voiceQuotaExhausted = false;
  let enqueueChain = Promise.resolve();
  const wantsVoiceAudio = !voiceTextOnly;
  const turnAbort = wantsVoiceAudio ? new AbortController() : null;
  if (turnAbort) activeTurnAbort = turnAbort;
  const streamPlayer = wantsVoiceAudio ? new PCMStreamPlayer({
    onStart: () => { audioPlaying = true; setState("speaking"); },
    onIdle: () => { audioPlaying = false; audioCooldownUntil = Date.now() + 700; },
  }) : null;
  activeStreamPlayer = streamPlayer;
  try {
    const history = lines.value.map((line) => ({ role: line.who === "user" ? "user" : "assistant", content: line.text }));
    const effectiveSystemPrompt = personaStore.activeCompiledPrompt || voice.characterManifest;
    const messages = [
      { role: "system", content: effectiveSystemPrompt },
      ...history,
    ];
    const onStreamEvent = (event: BailianStreamEvent) => {
      if (event.type === "text.delta" && event.text) {
        answerText += event.text;
        const current = lines.value[lines.value.length - 1];
        if (current?.who === "ai") current.text = answerText;
        else addLine(answerText, "ai");
      } else if (event.type === "audio.delta" && event.audio && streamPlayer) {
        enqueueChain = enqueueChain.then(() => streamPlayer.enqueue(event.audio!, event.sample_rate || 24000)).catch((error) => { streamError = (error as Error).message; });
      } else if (event.type === "audio.quota_exhausted") {
        voiceQuotaExhausted = true;
        voiceTextOnly = true;
      } else if (event.type === "audio.error" || event.type === "error") {
        streamError = event.message || "百炼流式语音生成失败";
      }
    };
    if (wantsVoiceAudio) {
      await streamChatAndTTS(
        messages,
        { adaptiveVoice:true, personaId:personaStore.activePersona?.id, voice:voice.speaker.trim() || "__default__" },
        onStreamEvent,
        turnAbort?.signal,
      );
    } else {
      await streamChat(messages, onStreamEvent);
    }
    await enqueueChain;
    if (streamPlayer) {
      streamPlayer.finish();
      await streamPlayer.waitForIdle();
    }
    if (streamError && !voiceQuotaExhausted) {
      addLine(streamError, "ai");
    }
  } catch (error) {
    if (isQuotaExceededError(error) && error.metric === "ai_voice_seconds") {
      voiceQuotaExhausted = true;
      voiceTextOnly = true;
      void auth.fetchBilling();
    }
    const message = quotaExceededMessage(error) || (error as Error).message || "语音对话请求失败";
    addLine(message, "ai");
  } finally {
    busy = false;
    activeTurnAbort = null;
    if (active) setState("listening");
    else setState("idle");
  }
}

async function onOrbTap() {
  if (busy) {
    stopAudio();
    abortActiveTurn("voice-interrupted");
    return;
  }
  if (active) {
    active = false;
    stopRecognition();
    stopAudio();
    setState("idle");
    return;
  }
  active = true;
  await startRecognition();
}

function onKeydown(event: KeyboardEvent) {
  if (event.code === "Space" && !event.repeat) {
    event.preventDefault();
    void onOrbTap();
  }
}

async function exitToChat() {
  active = false;
  abortActiveTurn("page-unload");
  stopRecognition();
  stopAudio();
  await router.push("/chat");
}

onMounted(async () => {
  await auth.ensureReady();
  if (auth.profile) await voice.ensureReady(auth.profile.id);
  await personaStore.loadPersonas();
  setState("idle");
  window.addEventListener("keydown", onKeydown);
});

onBeforeUnmount(() => {
  active = false;
  abortActiveTurn("page-unload");
  stopRecognition();
  stopAudio();
  window.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <div class="voice-shell" :data-state="orbState" data-provider="bailian">
    <AppNav variant="voice" />
    <main class="stage">
      <h1 class="voice-page-title">全屏语音陪伴</h1>
      <div class="orb-stage" id="orbStage">
        <OrbCanvas :state="orbState" :particle-count="150" />
        <div class="orb-halo" aria-hidden="true"></div>
        <button class="orb-tap" id="orbTap" aria-label="开始或继续对话" @click="onOrbTap"><span class="orb-tap__hint">{{ tapHint }}</span></button>
      </div>
      <p class="status" aria-live="polite">{{ statusText }}</p>
      <div class="transcript" aria-live="polite">
        <div v-for="line in lines" :key="line.id" class="tline" :class="'tline--' + line.who">
          <template v-if="line.who === 'ai'"><span class="tline__who">{{ personaStore.activePersonaName }} · AI</span>{{ line.text }}</template>
          <template v-else>{{ line.text }}</template>
        </div>
      </div>
      <p class="footnote">虚拟角色始终为 AI，不冒充、不替代任何真实的人。</p>
    </main>
    <div class="dock"><button class="dock-btn" id="endBtn" aria-label="结束全屏语音并返回对话" @click="exitToChat"><span class="dock-btn__icon">✕</span></button></div>

    <PersonaWorkshopDialog />
  </div>
</template>
