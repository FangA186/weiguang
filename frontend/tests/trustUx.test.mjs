import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const account = read("../src/components/AccountDialog.vue");
const auth = read("../src/components/AuthDialog.vue");
const voice = read("../src/components/VoiceSettingsDialog.vue");
const persona = read("../src/components/PersonaWorkshopDialog.vue");
const purchase = read("../src/views/PurchaseView.vue");
const pricing = read("../src/views/PricingView.vue");
const legal = read("../src/views/LegalView.vue");
const api = read("../src/api/index.ts");
const router = read("../src/router/index.ts");

test("account deletion and legal links are explicit and honest", () => {
  assert.match(api, /deleteAccount\(\)/);
  assert.match(api, /method: "DELETE"/);
  assert.match(account, /deleteStep/);
  assert.match(account, /确认永久注销并删除/);
  assert.match(account, /remote_cleanup/);
  assert.match(auth, /不会承诺固定账号数量/);
  assert.doesNotMatch(auth, /首批开放 100 个账号/);
  assert.match(auth, /邮箱验证邮件/);
  assert.match(auth, /忘记密码或密码重置入口/);
  for (const path of ["privacy", "terms", "data-rights"]) {
    assert.match(legal, new RegExp(`to=\\"/${path}\\"`));
    assert.match(router, new RegExp(`path: \\"/${path}\\"`));
  }
  assert.match(purchase, /链动小铺查看订单售后入口/);
});

test("free trial is presented as one seven-day period", () => {
  assert.match(pricing, /共 7 天/);
  assert.doesNotMatch(pricing, /首次 30 天|共 30 天/);
  assert.match(account, /免费体验到期日/);
});

test("ordinary voice settings hide the complete prompt", () => {
  assert.match(voice, /advancedMode/);
  assert.match(voice, /完整 System Prompt 不会在普通模式直接显示/);
  assert.match(voice, /高级模式会直接展示并编辑完整 System Prompt/);
  assert.match(voice, /v-model=\"normalManifestDraft\"/);
  assert.match(voice, /v-model=\"manifestDraft\"/);
});

test("persona forms keep OCR labels behind a quality gate", () => {
  assert.match(persona, /cleanPersonaLabel/);
  assert.match(persona, /系统消息/);
  assert.match(persona, /sanitizePersonaFields/);
  assert.match(persona, /必须叫对方'/);
});
