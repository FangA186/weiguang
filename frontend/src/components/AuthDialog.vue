<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from "vue";
import { storeToRefs } from "pinia";
import { useAuthStore } from "../stores/auth";
import { emailError, passwordChecks } from '../lib/authValidation';

const auth = useAuthStore();
const { authDialogOpen, authMode } = storeToRefs(auth);

const dialogRef = ref<HTMLDialogElement | null>(null);
const email = ref("");
const password = ref("");
const nickname = ref("");
const passwordConfirm = ref("");
const message = ref("");
const submitting = ref(false);

const registering = () => authMode.value === "register";
const registrationEmailError = computed(() => registering() && email.value ? emailError(email.value) : '');
const checks = computed(() => passwordChecks(password.value));
const registrationValid = computed(() => !registering() || (!emailError(email.value) && checks.value.every(c=>c.ok) && password.value===passwordConfirm.value));

function toggleMode() {
  auth.setAuthMode(registering() ? "login" : "register");
  message.value = "";
}

async function submit() {
  if (!registrationValid.value) { message.value = password.value!==passwordConfirm.value ? '两次输入的密码不一致' : registrationEmailError.value || '请满足全部密码要求'; return; }
  submitting.value = true;
  message.value = registering() ? "正在创建账号…" : "正在登录…";
  try {
    if (registering()) {
      await auth.doRegister(email.value, password.value, nickname.value);
    } else {
      await auth.doLogin(email.value, password.value);
    }
    email.value = "";
    password.value = "";
    passwordConfirm.value = "";
    nickname.value = "";
  } catch (error) {
    message.value = (error as Error).message;
  } finally {
    submitting.value = false;
  }
}

function syncOpen() {
  const el = dialogRef.value;
  if (!el) return;
  if (authDialogOpen.value && !el.open) el.showModal();
  else if (!authDialogOpen.value && el.open) el.close();
}

watch(authDialogOpen, syncOpen);
watch(dialogRef, syncOpen);

function onClose() {
  if (authDialogOpen.value) authDialogOpen.value = false;
}

onBeforeUnmount(() => {
  dialogRef.value?.close();
});
</script>

<template>
  <dialog ref="dialogRef" class="auth-dialog" @close="onClose">
    <header class="account-head"><h2>{{ registering() ? "注册微光" : "登录微光" }}</h2></header>
    <div class="account-body">
      <p class="auth-copy">登录后继续对话。注册后的可用额度以服务端当前套餐规则为准；微光不会承诺固定账号数量。</p>
      <form @submit.prevent="submit">
        <label class="account-field" v-if="registering()"><span>怎么称呼你</span><input v-model="nickname" maxlength="24" autocomplete="nickname" /></label>
        <label class="account-field"><span>邮箱</span><input v-model="email" type="email" autocomplete="email" required /></label>
        <p v-if="registrationEmailError" class="auth-validation-error">{{ registrationEmailError }}</p>
        <label class="account-field"><span>密码</span><input v-model="password" type="password" :minlength="registering() ? 10 : 8" maxlength="72" :autocomplete="registering() ? 'new-password' : 'current-password'" required /></label>
        <div v-if="registering()" class="password-checks" aria-live="polite"><span v-for="check in checks" :key="check.label" :class="{ok:check.ok}">{{ check.ok ? '✓' : '○' }} {{ check.label }}</span></div>
        <label class="account-field" v-if="registering()"><span>确认密码</span><input v-model="passwordConfirm" type="password" minlength="10" maxlength="72" autocomplete="new-password" required /></label>
        <p v-if="registering() && passwordConfirm && password!==passwordConfirm" class="auth-validation-error">两次输入的密码不一致</p>
        <button class="account-action account-action--primary account-action--wide" type="submit" :disabled="submitting || !registrationValid">
          {{ registering() ? "注册并开始体验" : "登录" }}
        </button>
        <div class="account-message" aria-live="polite">{{ message }}</div>
      </form>
      <p class="auth-status-note" aria-live="polite">
        {{ registering() ? "当前不会发送邮箱验证邮件；请使用可长期访问的邮箱并妥善保存密码。" : "当前尚未提供忘记密码或密码重置入口，请妥善保存密码。" }}
      </p>
      <nav class="auth-legal-links" aria-label="注册前阅读">
        <span>继续即表示你已阅读</span>
        <router-link to="/privacy" @click="authDialogOpen = false">隐私政策</router-link>
        <router-link to="/terms" @click="authDialogOpen = false">用户协议</router-link>
        <router-link to="/data-rights" @click="authDialogOpen = false">数据保留与删除</router-link>
      </nav>
      <p class="auth-toggle">
        <span>{{ registering() ? "已经有账号？" : "还没有账号？" }}</span>
        <button type="button" @click="toggleMode">{{ registering() ? "登录" : "注册" }}</button>
      </p>
    </div>
  </dialog>
</template>
