<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { PLAN_PRESENTATION } from "../config/plans";
import { fetchBillingChannels } from "../api";
import type { BillingChannels, PlanCode, RedemptionResult } from "../types";
import "../assets/styles/purchase.css";

const route = useRoute();
const auth = useAuthStore();
const channels = ref<BillingChannels | null>(null);
const code = ref("");
const showCode = ref(false);
const redeeming = ref(false);
const message = ref("");
const result = ref<RedemptionResult | null>(null);
const maskedCode = ref("");
const checkoutOpened = ref(false);
const plansLoading = ref(true);
const plansError = ref("");

const planCode = computed<"plus" | "pro">(() => route.params.planCode === "pro" ? "pro" : "plus");
const plan = computed(() => auth.plans.find((candidate) => candidate.code === planCode.value) || null);
const purchaseUrl = computed(() => channels.value?.ldxp[planCode.value] || "");
const billingConfirmed = computed(() => auth.isLoggedIn && auth.billingStatus === "ready" && auth.billingSummary !== null);
const billingLoading = computed(() => auth.isLoggedIn && (auth.billingStatus === "idle" || auth.billingStatus === "loading"));
const billingVerificationFailed = computed(() => auth.isLoggedIn && auth.billingStatus === "error");
const currentPlanCode = computed<PlanCode | null>(() => billingConfirmed.value ? auth.billingSummary!.plan_code : null);
const currentPaidActive = computed(() => {
  if (!billingConfirmed.value || !currentPlanCode.value) return false;
  const end = auth.billingSummary?.renewed_until
    || auth.billingSummary?.access_ends_at
    || auth.billingSummary?.period_end;
  return currentPlanCode.value !== "free" && Boolean(end) && new Date(end!).getTime() > Date.now();
});
const crossPlanBlocked = computed(() => currentPaidActive.value && currentPlanCode.value !== planCode.value);
const renewal = computed(() => currentPaidActive.value && currentPlanCode.value === planCode.value);
const checkoutDisabled = computed(() => !purchaseUrl.value || (
  auth.isLoggedIn && (!billingConfirmed.value || crossPlanBlocked.value)
));
const resultEndDate = computed(() => {
  const value = result.value?.billing.renewed_until
    || result.value?.billing.access_ends_at
    || result.value?.grant.period_end;
  return value ? new Date(value).toLocaleDateString("zh-CN") : "";
});
const resetDate = computed(() => {
  const value = auth.billingSummary?.reset_at || auth.billingSummary?.period_end;
  return value ? new Date(value).toLocaleDateString("zh-CN") : "";
});
const accessEndDate = computed(() => {
  const value = auth.billingSummary?.renewed_until || auth.billingSummary?.access_ends_at;
  return value ? new Date(value).toLocaleDateString("zh-CN") : "";
});

onMounted(async () => {
  const plansRequest = auth.fetchPlans()
    .catch((error) => { plansError.value = (error as Error).message || "套餐信息暂时不可用"; })
    .finally(() => { plansLoading.value = false; });
  channels.value = await fetchBillingChannels().catch(() => null);
  await auth.ensureReady();
  if (auth.isLoggedIn) await auth.fetchBilling();
  await plansRequest;
});

function openCheckout() {
  if (!purchaseUrl.value) return;
  if (!auth.isLoggedIn) {
    requireLogin();
    return;
  }
  if (!billingConfirmed.value || crossPlanBlocked.value) return;
  window.open(purchaseUrl.value, "_blank", "noopener,noreferrer");
  checkoutOpened.value = true;
}

async function retryBilling() {
  await auth.fetchBilling();
}

function checkoutLabel(): string {
  if (!purchaseUrl.value) return "商品暂不可用";
  if (!auth.isLoggedIn) return "登录后购买";
  if (billingLoading.value) return "套餐状态校验中…";
  if (billingVerificationFailed.value) return "套餐状态校验失败";
  if (crossPlanBlocked.value) return "当前套餐不支持跨档";
  return "打开链动小铺购买";
}

function requireLogin() {
  auth.setAuthMode("login");
  auth.authDialogOpen = true;
}

function mask(value: string): string {
  const compact = value.replace(/\s+/g, "");
  return compact.length > 6 ? `${compact.slice(0, 2)}-••••-${compact.slice(-4)}` : "已使用";
}

async function redeem() {
  if (!auth.isLoggedIn) {
    requireLogin();
    return;
  }
  const rawCode = code.value.trim();
  if (!rawCode || redeeming.value) return;
  redeeming.value = true;
  message.value = "";
  try {
    const redemption = await auth.redeemSubscriptionCode(rawCode);
    result.value = redemption;
    maskedCode.value = mask(rawCode);
    code.value = "";
    showCode.value = false;
  } catch (error) {
    message.value = (error as Error).message;
  } finally {
    redeeming.value = false;
  }
}
</script>

<template>
  <div class="purchase-view">
    <header class="purchase-nav">
      <router-link to="/pricing" class="purchase-nav__back">← 返回套餐</router-link>
      <router-link to="/" class="purchase-nav__brand"><span></span>微光 · AI陪伴</router-link>
      <button v-if="auth.isLoggedIn" type="button" @click="auth.openAccount">个人中心</button>
      <button v-else type="button" @click="requireLogin">登录</button>
    </header>

    <main class="purchase-main">
      <section v-if="result" class="purchase-success" aria-live="polite">
        <span class="purchase-success__mark">✓</span>
        <p class="purchase-kicker">兑换成功</p>
        <h1>{{ result.grant.plan_code === "plus" ? "微光 Plus" : "微光 Pro" }} 已生效</h1>
        <p>套餐有效期至 {{ resultEndDate }}</p>
        <div class="purchase-success__code">已使用卡密：{{ maskedCode }}</div>
        <div class="purchase-actions">
          <router-link to="/chat" class="purchase-primary">开始对话</router-link>
          <button type="button" class="purchase-secondary" @click="auth.openAccount">查看套餐与用量</button>
        </div>
      </section>

      <section v-else-if="plansLoading" class="purchase-hero" aria-live="polite">
        <p class="purchase-kicker">正在读取套餐权益…</p>
      </section>

      <section v-else-if="plansError || !plan" class="purchase-hero" aria-live="polite">
        <p class="purchase-kicker">{{ plansError || "未找到该套餐" }}</p>
        <router-link to="/pricing" class="purchase-secondary">返回套餐页</router-link>
      </section>

      <template v-else>
        <section class="purchase-hero">
          <p class="purchase-kicker">{{ plan.billing_period_days }} 天套餐兑换</p>
          <h1>开通 {{ plan.name }}</h1>
          <p>{{ PLAN_PRESENTATION[plan.code].description }}</p>
          <div class="purchase-price"><span>¥</span>{{ plan.price_cny }}<small>/ {{ plan.billing_period_days }} 天</small></div>
          <p v-if="billingLoading" class="purchase-status purchase-status--checking" aria-live="polite">
            正在校验套餐状态…
          </p>
          <p v-else-if="billingVerificationFailed" class="purchase-status purchase-status--blocked" aria-live="polite">
            套餐状态校验失败，请重试。
            <button type="button" class="purchase-status__retry" @click="retryBilling">重试</button>
          </p>
          <p v-else-if="renewal" class="purchase-status purchase-status--ok">
            你当前已是 {{ plan.name }}。本期额度在 {{ resetDate || "当前周期结束日" }} 重置；再次购买并兑换后，访问权将从 {{ accessEndDate || "当前访问到期日" }} 继续顺延 {{ plan.billing_period_days }} 天。
          </p>
          <p v-else-if="crossPlanBlocked" class="purchase-status purchase-status--blocked">
            当前付费套餐仍有效至 {{ accessEndDate || "当前访问到期日" }}，暂不支持跨档兑换。请勿购买此卡密。
          </p>
        </section>

        <section class="purchase-steps" aria-label="购买与兑换流程">
          <article>
            <span>01</span>
            <h2>前往链动小铺付款</h2>
            <p>付款成功后，链动小铺订单详情会显示一次性卡密。</p>
            <button
              type="button"
              class="purchase-primary"
              :disabled="checkoutDisabled"
              @click="openCheckout"
            >
              {{ checkoutLabel() }}
            </button>
          </article>

          <article :class="{ 'is-current': checkoutOpened }">
            <span>02</span>
            <h2>复制订单中的卡密</h2>
            <p>完成支付后回到本页面，复制完整卡密进行兑换。</p>
          </article>

          <article class="purchase-redeem" :class="{ 'is-current': checkoutOpened }">
            <span>03</span>
            <h2>登录微光并兑换</h2>
            <p>兑换成功后立即显示套餐名称和新的到期日期。</p>
            <form v-if="auth.isLoggedIn" @submit.prevent="redeem">
              <div class="purchase-code-field">
                <input
                  v-model="code"
                  :type="showCode ? 'text' : 'password'"
                  autocomplete="one-time-code"
                  maxlength="80"
                  placeholder="粘贴链动小铺卡密"
                  aria-label="套餐兑换码"
                  :disabled="redeeming || crossPlanBlocked"
                />
                <button type="button" @click="showCode = !showCode">{{ showCode ? "隐藏" : "显示" }}</button>
              </div>
              <button class="purchase-primary" type="submit" :disabled="!code.trim() || redeeming || crossPlanBlocked">
                {{ redeeming ? "兑换中…" : "确认兑换" }}
              </button>
              <p v-if="message" class="purchase-error" aria-live="polite">{{ message }}</p>
            </form>
            <button v-else type="button" class="purchase-primary" @click="requireLogin">登录后兑换</button>
          </article>
        </section>

        <section class="purchase-note">
          <h2>购买说明</h2>
          <ul>
            <li>本商品为单次购买，不会自动续费或自动扣款。</li>
            <li>同档套餐按该套餐的 {{ plan.billing_period_days }} 天周期续费；有效付费套餐暂不支持跨档兑换。</li>
            <li>完整卡密只在链动小铺订单中展示；微光兑换成功后仅显示掩码。</li>
            <li>未兑换退款请通过链动小铺订单售后处理；已兑换权益需人工审核，微光不会自动回滚已使用额度。</li>
          </ul>
          <div class="purchase-support">
            <strong>需要售后？</strong>
            <span>支付、发货、未兑换退款以链动小铺订单状态为准；链动订单不会自动同步成微光退款结果。</span>
            <a v-if="purchaseUrl" :href="purchaseUrl" target="_blank" rel="noopener noreferrer">前往链动小铺查看订单售后入口 ↗</a>
            <span v-else>当前商品链接尚未配置，请稍后再试。</span>
          </div>
          <nav class="purchase-legal-links" aria-label="购买前阅读">
            <router-link to="/privacy">隐私政策</router-link>
            <router-link to="/terms">用户协议</router-link>
            <router-link to="/data-rights">数据保留与删除</router-link>
          </nav>
        </section>
      </template>
    </main>
  </div>
</template>
