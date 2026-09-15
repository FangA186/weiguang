import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const chat = read("../src/views/ChatView.vue");
const landing = read("../src/views/LandingView.vue");
const voice = read("../src/views/VoiceView.vue");
const chatCss = read("../src/assets/styles/chat.css");
const orb = read("../src/composables/useOrb.ts");
const appNav = read("../src/components/AppNav.vue");
const voiceDialog = read("../src/components/VoiceSettingsDialog.vue");
const frontendApi = read("../src/api/index.ts");
const voiceStore = read("../src/stores/voiceConfig.ts");
const api = read("../src/api/index.ts");
const chatImport = read("../src/components/ChatImportDialog.vue");
const index = read("../index.html");
const audioEncoder = read("../src/utils/audioEncoder.ts");

test("mobile chat exposes reachable conversation, chat, and voice views", () => {
  assert.match(chat, /class="mobile-chat-tabs"/);
  assert.match(chat, /setMobileView\('conversations'\)/);
  assert.match(chat, /setMobileView\('chat'\)/);
  assert.match(chat, /setMobileView\('voice'\)/);
  assert.match(chatCss, /stage\[data-mobile-view="conversations"\]/);
  assert.match(chatCss, /stage\[data-mobile-view="voice"\]/);
  assert.match(chatCss, /\.chat-panel__main\s*\{\s*display:\s*flex/);
});

test("conversation view keeps import and voice selection reachable", () => {
  assert.match(chat, /＋ 导入/);
  assert.match(chat, /选择克隆音色/);
  assert.match(chat, /class="orb-voice-settings" aria-label="音色设置"/);
  assert.match(appNav, />克隆声音<\/button>/);
  assert.match(chatCss, /\.chat-shell \.cnav__voice \{ display: inline-flex;/);
  assert.doesNotMatch(chatCss, /\.chat-shell \.cnav__voice \{ display: none;/);
  assert.match(chat, /voice\.open\(auth\.profile\.id, "settings"\)/);
  assert.match(voiceStore, /VoiceDialogMode = "clone" \| "settings"/);
  assert.match(voiceDialog, /dialogMode === "settings" \? "音色设置" : "克隆声音"/);
  assert.match(voiceDialog, /<VoiceProfileForm v-model="voiceProfileDraft"/);
  assert.match(voiceDialog, /savePersona\(active\.id, \{ voice_style: voiceProfileDraft\.value \}\)/);
  assert.match(chat, /<AppNav variant="chat" @new-chat/);
  assert.match(chat, /<h1 class="chat-page-title">\{\{ chatHeaderTitle \}\}<\/h1>/);
  assert.match(voiceDialog, /建议上传 10–20 秒的单人连续清晰说话录音/);
  assert.match(voiceDialog, /去除背景噪声并试听/);
  assert.match(voiceDialog, /使用净化音/);
  assert.match(voiceDialog, /确认裁剪后去除背景噪声/);
  assert.match(voiceDialog, /:disabled="isTrimPanelOpen \|\| denoiseSaving/);
  assert.match(voiceDialog, /v-if="denoisedPreviewUrl && !isTrimPanelOpen"/);
  assert.match(voiceDialog, /请先确认裁剪，再生成净化试听/);
  assert.match(voiceDialog, /bailianVoiceSaving \|\| voiceSlotsFull \|\| isTrimPanelOpen/);
  assert.match(frontendApi, /\/api\/uploads\/denoise/);
  assert.match(audioEncoder, /new OfflineAudioContext\(1,/);
  assert.match(audioEncoder, /_48k_mono\.wav/);
});

test("chat input has a hard 2000 character browser limit", () => {
  assert.match(chat, /maxlength="2000"/);
  assert.match(chat, /input\.length \}\} \/ 2000/);
});

test("IME confirmation Enter never sends a composing message", () => {
  assert.match(chat, /event\.isComposing \|\| event\.keyCode === 229/);
  assert.match(chat, /if \(event\.key === "Enter" && !event\.shiftKey\)/);
});

test("mobile accessibility basics stay in the page source", () => {
  assert.match(landing, /<main\b/);
  assert.match(landing, /<h1\b/);
  assert.match(chat, /<main\b/);
  assert.match(chat, /<h1 class="chat-page-title">/);
  assert.match(voice, /<main\b/);
  assert.match(voice, /<h1 class="voice-page-title">/);
  assert.doesNotMatch(index, /user-scalable\s*=\s*["']no/i);
  assert.doesNotMatch(index, /maximum-scale\s*=/i);
  assert.doesNotMatch(index, /fonts\.(?:googleapis|gstatic)\.com/);
});

test("message actions stay visually compact", () => {
  assert.match(chatCss, /\.msg__audio[\s\S]*?width:\s*34px;/);
  assert.match(chatCss, /\.msg__audio[\s\S]*?height:\s*34px;/);
});

test("imported counterpart messages can be synthesized as speech", () => {
  assert.match(chat, /v-if="msg\.who === 'ai' && !voiceReplying && orbState === 'idle'"/);
  assert.doesNotMatch(chat, /v-if="msg\.who === 'ai' && !msg\.imported && !voiceReplying/);
});

test("orb restarts after a hidden mobile panel becomes visible", () => {
  assert.match(orb, /new ResizeObserver/);
  assert.match(orb, /resizeObserver\.observe\(canvas\)/);
  assert.match(orb, /resize\(\);\s*loop\(\);/);
});

test("selected and explicit default voices reach adaptive voice requests", () => {
  assert.match(chat, /voice: voice\.speaker\.trim\(\) \|\| "__default__"/);
  assert.match(voice, /voice:voice\.speaker\.trim\(\) \|\| "__default__"/);
  assert.match(api, /if \(!options\.replayTurnId && options\.voice\) query\.set\("voice", options\.voice\)/);
});

test("voice names and OCR conversation nicknames persist through backend APIs", () => {
  assert.match(api, /renameVoiceClone\(voiceId: string, name: string\)/);
  assert.match(voiceDialog, /新的音色名称/);
  assert.match(voiceDialog, /voice\.renameVoiceClone\(clone\.voice_id, name\)/);
  assert.match(chatImport, /aria-label="当前对话人的网名"/);
  assert.match(chatImport, /请填写当前对话人的网名/);
  assert.match(chat, /title: conversationName\?\.trim\(\) \|\| importConversationTitle\(batch\)/);
});
