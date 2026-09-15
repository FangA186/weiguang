<script setup lang="ts">
import { ref, watch, computed, onBeforeUnmount, nextTick } from "vue";
import { useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { useAuthStore } from "../stores/auth";
import { QUOTA_METRICS, formatQuotaValue } from "../config/plans";

const router = useRouter();
const auth = useAuthStore();
const { accountDialogOpen, profile, billingSummary, plans } = storeToRefs(auth);

const dialogRef = ref<HTMLDialogElement | null>(null);
const nicknameDraft = ref("");
const profileMessage = ref("");
const savingNickname = ref(false);
const avatarInput = ref<HTMLInputElement|null>(null);
const savingAvatar = ref(false);
const redemptionCode = ref("");
const redemptionMessage = ref("");
const redeeming = ref(false);
const deleteStep = ref<0 | 1>(0);
const deletingAccount = ref(false);
const deletionResult = ref("");

const currentPlan = computed(() => {
  const code = billingSummary.value?.plan_code || "free";
  return plans.value.find((plan) => plan.code === code) || null;
});
const planExpired = computed(() => billingSummary.value?.status === "expired");

function formatDate(value?: string): string {
  if (!value) return "待后端返回";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "待后端返回";
  return date.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" });
}

const resetDateText = computed(() => formatDate(billingSummary.value?.reset_at || billingSummary.value?.period_end));
const accessEndText = computed(() => formatDate(
  billingSummary.value?.renewed_until || billingSummary.value?.access_ends_at,
));
const enforcementText = computed(() => billingSummary.value?.enforcement_mode === "hard"
  ? "硬额度已开启"
  : "影子统计中");

const usageCards = computed(() => QUOTA_METRICS.map((definition) => {
  const metric = billingSummary.value?.metrics?.[definition.key];
  const limit = metric?.limit;
  const used = metric?.used;
  const reserved = metric?.reserved;
  const remaining = metric?.remaining;
  const percent = limit && limit > 0 && used != null
    ? Math.min(100, Math.round(((used + (reserved || 0)) / limit) * 100))
    : 0;
  return {
    ...definition,
    used,
    reserved,
    limit,
    remaining,
    percent,
  };
}));

function formatUsageValue(metric: typeof QUOTA_METRICS[number]["key"], value?: number) {
  return formatQuotaValue(metric, value);
}

function goToPricing() {
  accountDialogOpen.value = false;
  router.push("/pricing");
}

async function saveProfile() {
  if (!nicknameDraft.value.trim() || savingNickname.value) return;
  savingNickname.value = true;
  profileMessage.value = "";
  try {
    await auth.saveNickname(nicknameDraft.value.trim());
    profileMessage.value = "昵称已保存。";
  } catch (error) {
    profileMessage.value = (error as Error).message;
  } finally {
    savingNickname.value = false;
  }
}

async function uploadAvatar(event:Event) {
  const input=event.target as HTMLInputElement;
  const file=input.files?.[0]; input.value='';
  if (!file || savingAvatar.value) return;
  savingAvatar.value=true; profileMessage.value='';
  try { await auth.saveAvatar(file); profileMessage.value='头像已保存。'; }
  catch(error) { profileMessage.value=(error as Error).message; }
  finally { savingAvatar.value=false; }
}

async function handleLogout() {
  await auth.doLogout();
  router.push("/");
}

function cleanupWarning(value: unknown): string {
  if (!value) return "";
  if (typeof value === "string") {
    const state = value.trim().toLowerCase();
    if (["ok", "done", "complete", "completed", "success", "succeeded", "none"].includes(state)) return "";
    if (/(pending|queued|partial|failed|incomplete|清理中|未完成|失败)/i.test(state)) {
      return "账号主数据已删除，但部分外部资产仍在清理中；完成状态以后端结果为准。";
    }
    return value.trim();
  }
  if (typeof value === "object") {
    if (Array.isArray(value)) return value.length ? "账号主数据已删除，但部分外部资产仍在清理中；完成状态以后端结果为准。" : "";
    const details = value as Record<string, unknown>;
    const state = String(details.status || details.state || "").toLowerCase();
    if (["pending", "queued", "partial", "failed", "incomplete"].includes(state) || details.pending === true) {
      return "账号主数据已删除，但部分外部资产仍在清理中；完成状态以后端结果为准。";
    }
    if (["ok", "done", "complete", "completed", "success", "succeeded", "none"].includes(state) || details.completed === true || details.pending === false) return "";
    if (typeof details.message === "string" && details.message.trim()) return details.message;
  }
  return "账号主数据已删除；部分外部资产的清理状态以后端结果为准。";
}

function deletedCountsText(counts: unknown): string {
  if (!counts || typeof counts !== "object") return "账号主数据已处理。";
  const total = Object.values(counts as Record<string, unknown>)
    .reduce((sum: number, value: unknown) => {
      const parsed = typeof value === "number" ? value : Number(value);
      return sum + (Number.isFinite(parsed) && parsed > 0 ? parsed : 0);
    }, 0);
  return total > 0 ? `已删除 ${total} 项账号数据。` : "账号主数据已处理。";
}

function armAccountDeletion() {
  deleteStep.value = 1;
  profileMessage.value = "";
}

function cancelAccountDeletion() {
  deleteStep.value = 0;
}

async function confirmAccountDeletion() {
  if (deletingAccount.value || !profile.value) return;
  deletingAccount.value = true;
  profileMessage.value = "";
  try {
    const response = await auth.doDeleteAccount();
    const cleanup = cleanupWarning(response.remote_cleanup);
    deletionResult.value = `${deletedCountsText(response.deleted_counts)}${cleanup ? ` ${cleanup}` : ""}`;
    deleteStep.value = 0;
    await router.push("/");
  } catch (error) {
    profileMessage.value = (error as Error).message || "账号注销失败，请稍后重试。";
  } finally {
    deletingAccount.value = false;
  }
}

async function redeemCode() {
  const code = redemptionCode.value.trim();
  if (!code || redeeming.value) return;
  redeeming.value = true;
  redemptionMessage.value = "";
  try {
    const result = await auth.redeemSubscriptionCode(code);
    redemptionCode.value = "";
    redemptionMessage.value = `兑换成功，${result.grant.plan_code === "plus" ? "微光 Plus" : "微光 Pro"} 已生效。`;
  } catch (error) {
    redemptionMessage.value = (error as Error).message;
  } finally {
    redeeming.value = false;
  }
}

async function syncOpen() {
  await nextTick();
  const el = dialogRef.value;
  if (!el) return;
  if (accountDialogOpen.value) {
    if (!el.open) {
      nicknameDraft.value = profile.value?.nickname ?? "";
      profileMessage.value = "";
      redemptionCode.value = "";
      redemptionMessage.value = "";
      deleteStep.value = 0;
      deletionResult.value = "";
      try {
        el.showModal();
      } catch (e) {
        console.warn("showModal failed", e);
      }
      void auth.fetchPlans().catch(() => undefined);
      void auth.fetchBilling();
    }
  } else {
    if (el.open) {
      el.close();
    }
  }
}

watch(accountDialogOpen, syncOpen);
watch(dialogRef, syncOpen);
watch(profile, (p) => {
  if (accountDialogOpen.value) nicknameDraft.value = p?.nickname ?? "";
});

function onClose() {
  redemptionCode.value = "";
  redemptionMessage.value = "";
  deleteStep.value = 0;
  deletionResult.value = "";
  if (accountDialogOpen.value) accountDialogOpen.value = false;
}

function closeOnBackdrop(event: MouseEvent) {
  if (event.target === dialogRef.value) {
    accountDialogOpen.value = false;
  }
}

onBeforeUnmount(() => dialogRef.value?.close());
</script>

<template>
  <dialog ref="dialogRef" class="account-dialog" @close="onClose" @click="closeOnBackdrop">
    <header class="account-head">
      <h2>个人中心</h2>
      <button class="account-close" type="button" aria-label="关闭" @click="accountDialogOpen = false">×</button>
    </header>
    
    <div v-if="deletionResult" class="account-body account-delete-result" role="status" aria-live="polite">
      <h3>账号注销已完成</h3>
      <p>{{ deletionResult }}</p>
      <p>该账号已退出当前设备。若服务端提示外部资产仍在清理，请等待后端任务完成。</p>
      <button type="button" class="account-action account-action--primary" @click="accountDialogOpen = false">关闭</button>
    </div>

    <div class="account-body" v-else-if="profile">
      <!-- Plan Card -->
      <section class="account-plan-card">
        <div class="account-plan-card__info">
          <h4>当前计划：{{ planExpired ? `${currentPlan?.name || "套餐"}已到期` : currentPlan?.name || "正在读取套餐" }}</h4>
          <template v-if="planExpired">
            <p>免费体验每个账号仅限一次，请购买或兑换套餐后继续使用。</p>
          </template>
          <template v-else-if="billingSummary?.plan_code === 'free'">
            <p>免费体验到期日：{{ accessEndText }}</p>
          </template>
          <template v-else>
            <p>本期额度重置日：{{ resetDateText }}</p>
            <p>访问续费至：{{ accessEndText }}</p>
          </template>
        </div>
        <button type="button" class="account-plan-card__btn" @click="goToPricing">查看计划</button>
      </section>

      <section class="account-redeem-card">
        <div class="account-redeem-card__copy">
          <h3>兑换套餐权益码</h3>
          <p>输入从链动小铺获得的一次性兑换码。</p>
        </div>
        <form class="account-redeem-card__form" @submit.prevent="redeemCode">
          <input
            v-model="redemptionCode"
            type="password"
            autocomplete="one-time-code"
            maxlength="80"
            placeholder="粘贴兑换码"
            aria-label="套餐兑换码"
            :disabled="redeeming"
          />
          <button type="submit" :disabled="!redemptionCode.trim() || redeeming">
            {{ redeeming ? "兑换中…" : "兑换" }}
          </button>
        </form>
        <p v-if="redemptionMessage" class="account-redeem-card__message" aria-live="polite">{{ redemptionMessage }}</p>
      </section>

      <!-- Multi-dimensional Usage Metrics -->
      <section class="account-section">
        <div class="usage-header">
          <h3>本期用量</h3>
          <span class="shadow-notice">{{ enforcementText }}</span>
        </div>

        <div class="usage-grid">
          <div v-for="card in usageCards" :key="card.key" class="usage-card">
            <div class="usage-card__top">
              <span class="usage-card__title">{{ card.label }}</span>
              <span class="usage-card__values">已用 <b>{{ formatUsageValue(card.key, card.used) }}</b> / 上限 {{ formatUsageValue(card.key, card.limit) }}</span>
            </div>
            <div class="usage-progress">
              <div class="usage-progress-bar" :class="{ 'is-full': card.percent >= 100 }" :style="{ width: card.percent + '%' }"></div>
            </div>
            <p class="usage-card__detail">预留 {{ formatUsageValue(card.key, card.reserved) }} · 剩余 {{ formatUsageValue(card.key, card.remaining) }}</p>
          </div>
        </div>
      </section>

      <!-- Profile Section -->
      <section class="account-section">
        <h3>个人资料</h3>
        <div class="account-avatar-editor">
          <img v-if="profile.avatar_download_url" :src="profile.avatar_download_url" alt="账号头像" />
          <span v-else aria-hidden="true">{{ (profile.nickname || profile.email).slice(0,1) }}</span>
          <div><button class="account-action" type="button" :disabled="savingAvatar" @click="avatarInput?.click()">{{ savingAvatar ? '上传中…' : profile.avatar_download_url ? '更换头像' : '上传头像' }}</button><p>支持 JPG、PNG、WEBP，最大 5MB。</p></div>
          <input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/webp" hidden @change="uploadAvatar" />
        </div>
        <label class="account-field">
          <span>昵称</span>
          <input v-model="nicknameDraft" maxlength="24" placeholder="请输入你的昵称" />
        </label>
        <label class="account-field">
          <span>邮箱</span>
          <input :value="profile.email" disabled />
        </label>
        <div style="display:flex; gap:12px; align-items:center; margin-top:8px">
          <button class="account-action account-action--primary" type="button" :disabled="savingNickname" @click="saveProfile">
            {{ savingNickname ? "保存中…" : "保存昵称" }}
          </button>
          <div class="account-message" style="margin:0" v-if="profileMessage">{{ profileMessage }}</div>
        </div>
      </section>

      <section class="account-section account-privacy-section">
        <h3>隐私与数据</h3>
        <p>你可以查看数据如何使用、保存多久，以及如何提交删除请求。</p>
        <nav class="account-legal-links" aria-label="隐私与协议">
          <router-link to="/privacy" @click="accountDialogOpen = false">隐私政策</router-link>
          <router-link to="/terms" @click="accountDialogOpen = false">用户协议</router-link>
          <router-link to="/data-rights" @click="accountDialogOpen = false">数据保留与删除</router-link>
        </nav>
        <div class="account-delete-box">
          <div>
            <strong>注销账号并删除数据</strong>
            <p>此操作不可撤销，会结束当前会话并请求服务端删除账号关联数据。</p>
          </div>
          <button
            v-if="deleteStep === 0"
            class="account-action account-action--danger"
            type="button"
            :disabled="deletingAccount"
            @click="armAccountDeletion"
          >
            开始注销
          </button>
        </div>
        <div v-if="deleteStep === 1" class="account-delete-confirm" role="alert">
          <p><strong>请再次确认：</strong>账号、对话、角色、导入记录和账号内声音设置将提交删除；外部渠道或备份中的资产可能需要额外时间清理。</p>
          <div class="account-delete-confirm__actions">
            <button class="account-action" type="button" :disabled="deletingAccount" @click="cancelAccountDeletion">取消</button>
            <button class="account-action account-action--danger" type="button" :disabled="deletingAccount" @click="confirmAccountDeletion">
              {{ deletingAccount ? "注销中…" : "确认永久注销并删除" }}
            </button>
          </div>
        </div>
      </section>

      <section class="account-section" style="display:flex; justify-content:flex-end; align-items:center">
        <button class="account-action account-action--danger" type="button" @click="handleLogout">退出登录</button>
      </section>
    </div>
  </dialog>
</template>
