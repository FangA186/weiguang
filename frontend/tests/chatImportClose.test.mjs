import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import test from 'node:test';
import { parse, compileScript } from '@vue/compiler-sfc';
import ts from 'typescript';
import * as vue from 'vue';

const require = createRequire(import.meta.url);
const source = readFileSync(new URL('../src/components/ChatImportDialog.vue', import.meta.url), 'utf8');
const chatSource = readFileSync(new URL('../src/views/ChatView.vue', import.meta.url), 'utf8');
const { descriptor } = parse(source);
const code = ts.transpileModule(compileScript(descriptor, { id:'close-test' }).content, {
  compilerOptions: { module:ts.ModuleKind.CommonJS, target:ts.ScriptTarget.ES2022 },
}).outputText;

function setup(persona = {autoDistillFromImport:async()=>{},autoApplyImport:async()=>{}}, api = {}, auth = {}) {
  const events = [];
  const module = { exports:{} };
  vm.runInNewContext(code, { module, exports:module.exports, require(name) {
    if (name === 'vue') return { ...vue, watch:()=>{}, onMounted:()=>{}, onBeforeUnmount:()=>{} };
    if (name.includes('stores/auth')) return {useAuthStore:()=>auth};
    if (name.includes('stores/personaStore')) return {usePersonaStore:()=>persona};
    if (name === '../api') return api;
    if (name.startsWith('../') || name.endsWith('.vue')) return {};
    return require(name);
  }});
  const state = module.exports.default.setup({open:true}, {expose:()=>{}, emit:event=>events.push(event)});
  return {state,events};
}

test('import cannot close on backdrop or during work; success and idle close still work', async () => {
  const {state,events} = setup();
  const dialog = descriptor.template.content.match(/<dialog\b[^>]*>/)[0];
  assert.doesNotMatch(dialog, /@click|closeOnBackdrop/);
  assert.match(dialog, /@cancel="handleCancel"/);
  assert.match(source, /禁止上传长截图/);
  assert.match(source, /识别失败/);
  assert.match(source, /:disabled="closeLocked"/);
  for (const flag of ['uploading','saving','isAutoDistilling','avatarUploading']) {
    state[flag].value = flag === 'avatarUploading' ? 'left' : true;
    state.handleClose();
    const event = new Event('cancel', {cancelable:true});
    state.handleCancel(event);
    assert.equal(event.defaultPrevented,true,flag);
    assert.equal(events.length,0,flag);
    state[flag].value = flag === 'avatarUploading' ? null : false;
  }
  state.step.value = 'processing';
  state.handleClose();
  assert.equal(events.length,0);
  state.step.value = 'upload';
  state.isPreviewOpen.value = true;
  const preview = new Event('cancel',{cancelable:true});
  state.handleCancel(preview);
  assert.ok(preview.defaultPrevented);
  assert.equal(state.isPreviewOpen.value,false);
  const idle = new Event('cancel',{cancelable:true});
  state.handleCancel(idle);
  assert.equal(idle.defaultPrevented,false);
  state.handleClose();
  assert.deepEqual(events,['close']);
  state.currentBatch.value = {id:1};
  await state.handleAutoDistill();
  assert.deepEqual(events,['close','close']);
});

test('confirm applies voice only when selected; save failures keep the import open', async () => {
  const calls = [];
  let fail = false;
  const persona = {
    activePersona:{id:'role-a',name:'当前角色'},
    async autoApplyImport() {},
    async savePersona(id,payload) { if(fail) throw new Error('角色保存失败'); calls.push({id,payload}); },
  };
  const api = {
    async updateChatImport() { return {id:1,messages:[]}; },
    async confirmChatImport() { calls.push('confirm'); return {id:1,messages:[]}; },
  };
  const {state,events} = setup(persona,api);
  state.resetState();
  assert.equal(state.applyVoiceToCurrentPersona.value,true);
  state.currentBatch.value = {id:1};
  state.voiceProfile.value = {rate:.85,emotion_mode:'manual',emotion:'gentle'};
  await state.handleConfirmImport();
  assert.equal(calls[0].id,'role-a');
  assert.equal(calls[0].payload.voice_style.rate,.85);
  assert.equal(calls[1],'confirm');
  assert.deepEqual(events,['confirmed']);
  calls.length = 0; events.length = 0;
  state.step.value = 'review'; fail = true;
  await state.handleConfirmImport();
  assert.equal(calls.length,0);
  assert.equal(events.length,0);
  assert.equal(state.step.value,'review');
  assert.equal(state.errorMessage.value,'角色保存失败');
  state.applyVoiceToCurrentPersona.value = false;
  await state.handleConfirmImport();
  assert.deepEqual(calls,['confirm']);
  calls.length = 0; fail = false;
  state.currentBatch.value = {id:1,left_avatar_object_key:'owned-avatar'};
  await state.handleConfirmImport();
  assert.deepEqual(calls,['confirm']); // A chat avatar must not update the shared persona.
});

test('extraction shows billing progress, blocks double clicks and allows retry after failure', async () => {
  let finishBilling;
  let checks = 0;
  const auth = {fetchBilling:()=>{checks++;return new Promise(resolve=>{finishBilling=resolve;});}};
  const {state} = setup(undefined,{quotaExceededMessage:()=>''},auth);
  state.selectedFiles.value = [{name:'test.png',size:100}];
  const pending = state.startExtraction();
  assert.equal(state.step.value,'processing');
  assert.equal(state.uploading.value,true);
  assert.match(state.processingText.value,/检查可用额度/);
  await state.startExtraction();
  assert.equal(checks,1);
  finishBilling(null);
  await pending;
  assert.equal(state.step.value,'upload');
  assert.equal(state.uploading.value,false);
  assert.match(state.errorMessage.value,/无法读取可用额度/);
  assert.equal(state.selectedFiles.value.length,1);
  const retry = state.startExtraction();
  finishBilling({metrics:{chat_import_batch:{remaining:0}}});
  await retry;
  assert.equal(state.uploading.value,false);
  assert.match(state.errorMessage.value,/已用完/);
});

test('OCR only accepts counterpart avatar; every user message uses account profile avatar',()=>{
  assert.doesNotMatch(source,/右侧 · 我|rightAvatarInputEl|right_avatar_object_key/);
  assert.match(source,/选择导入会话/);
  assert.match(chatSource,/msg\.who === 'user'/);
  assert.match(chatSource,/auth\.profile\?\.avatar_download_url/);
  assert.match(chatSource,/我的账号头像/);
});
