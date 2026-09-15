<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { PLAN_PRESENTATION, QUOTA_METRICS, formatQuotaValue, planHighlights } from "../config/plans";
import { fetchBillingChannels } from "../api";
import type { BillingChannels, PlanCode, PlanDefinition } from "../types";
import "../assets/styles/pricing.css";

const router = useRouter();
const auth = useAuthStore();
const channels = ref<BillingChannels | null>(null);
const redeemOpen = ref(false);
const redeemCode = ref("");
const redeemMessage = ref("");
const redeeming = ref(false);
const plansLoading = ref(true);
const plansError = ref("");

const planList = computed(() => auth.plans);

onMounted(async () => {
  const plansRequest = auth.fetchPlans()
    .catch((error) => { plansError.value = (error as Error).message || "套餐信息暂时不可用"; })
    .finally(() => { plansLoading.value = false; });
  const channelsRequest = fetchBillingChannels()
    .then((value) => { channels.value = value; })
    .catch(() => { channels.value = null; });
  await auth.ensureReady();
  if (auth.isLoggedIn) {
    void auth.fetchBilling();
  }
  await Promise.all([plansRequest, channelsRequest]);
});

const currentPlanCode = computed(() => {
  return auth.billingSummary?.plan_code || "free";
});
const freeTrialExpired = computed(() => auth.billingSummary?.status === "expired");
const freeActionDisabled = computed(() => auth.isLoggedIn
  && (freeTrialExpired.value || currentPlanCode.value !== "free"));

function handleFreeAction() {
  if (!auth.isLoggedIn) {
    auth.authDialogOpen = true;
    return;
  }
  if (freeActionDisabled.value) return;
  router.push("/chat");
}

function purchaseUrl(planCode: PlanCode): string {
  if (planCode === "free") return "";
  return channels.value?.ldxp[planCode] || "";
}

function planLimitText(plan: PlanDefinition, metric: typeof QUOTA_METRICS[number]): string {
  const value = plan.limits[metric.planLimit];
  return value === 0 && metric.key === "video" ? "暂未开放" : formatQuotaValue(metric.key, value);
}

function openRedeem() {
  redeemOpen.value = true;
  redeemMessage.value = "";
  if (!auth.isLoggedIn) auth.authDialogOpen = true;
}

async function submitRedemption() {
  const code = redeemCode.value.trim();
  if (!code || redeeming.value) return;
  redeeming.value = true;
  redeemMessage.value = "";
  try {
    const result = await auth.redeemSubscriptionCode(code);
    redeemCode.value = "";
    redeemMessage.value = `兑换成功，${result.grant.plan_code === "plus" ? "微光 Plus" : "微光 Pro"} 已生效。`;
  } catch (error) {
    redeemMessage.value = (error as Error).message;
  } finally {
    redeeming.value = false;
  }
}
</script>

<template>
  <div class="pricing-view">
    <!-- Top Nav -->
    <header class="pricing-nav">
      <router-link to="/" class="pricing-nav__brand">
        <span class="dot"></span>
        <span>微光 · AI 陪伴</span>
      </router-link>
      <div class="pricing-nav__actions">
        <router-link to="/" class="pricing-nav__btn">返回首页</router-link>
        <template v-if="auth.isLoggedIn">
          <button class="pricing-nav__btn" @click="auth.openAccount">个人中心</button>
          <router-link to="/chat" class="pricing-nav__btn pricing-nav__btn--primary">进入对话</router-link>
        </template>
        <template v-else>
          <button class="pricing-nav__btn pricing-nav__btn--primary" @click="auth.authDialogOpen = true">
            登录 / 注册
          </button>
        </template>
      </div>
    </header>

    <!-- Main Content -->
    <main class="pricing-container">
      <!-- Hero -->
      <section class="pricing-hero">
        <span class="pricing-hero__tag">TRANSPARENT PRICING</span>
        <h1 class="pricing-hero__title">选择适合你的陪伴方式</h1>
        <p class="pricing-hero__subtitle">
          每个账号可免费体验一次，共 7 天。需要更长的 AI 语音和更多对话时，再决定是否升级。
        </p>
      </section>

      <!-- Plan Cards -->
      <p v-if="plansLoading" class="pricing-redeem__message" aria-live="polite">正在读取当前套餐权益…</p>
      <p v-else-if="plansError" class="pricing-redeem__message" aria-live="polite">{{ plansError }}</p>
      <section v-else class="pricing-grid">
        <div
          v-for="plan in planList"
          :key="plan.code"
          class="pricing-card"
          :class="{ 'pricing-card--featured': PLAN_PRESENTATION[plan.code].featured }"
        >
          <span v-if="PLAN_PRESENTATION[plan.code].tag" class="pricing-card__badge">{{ PLAN_PRESENTATION[plan.code].tag }}</span>
          
          <div class="pricing-card__header">
            <h2 class="pricing-card__name">{{ plan.name }}</h2>
            <p class="pricing-card__desc">{{ PLAN_PRESENTATION[plan.code].description }}</p>
          </div>

          <div class="pricing-card__price-box">
            <span class="pricing-card__currency">¥</span>
            <span class="pricing-card__amount">{{ plan.price_cny }}</span>
            <span class="pricing-card__unit">/ {{ plan.code === 'free' ? `首次 ${plan.billing_period_days} 天` : `${plan.billing_period_days} 天` }}</span>
          </div>

          <ul class="pricing-card__features">
            <li v-for="(feat, idx) in planHighlights(plan)" :key="idx" class="pricing-card__feature-item">
              <span class="pricing-card__feature-icon">✦</span>
              <span>{{ feat }}</span>
            </li>
          </ul>

          <div class="pricing-card__footer">
            <button
              v-if="plan.code === 'free'"
              class="pricing-card__btn pricing-card__btn--active"
              :class="{ 'pricing-card__btn--disabled': freeActionDisabled }"
              :disabled="freeActionDisabled"
              @click="handleFreeAction"
            >
              {{ freeTrialExpired
                ? '免费体验已结束'
                : auth.isLoggedIn && currentPlanCode !== 'free' ? '当前为付费套餐'
                : auth.isLoggedIn && currentPlanCode === 'free' ? '进入对话 (当前计划)' : '开始体验一次' }}
            </button>
            <router-link
              v-else-if="purchaseUrl(plan.code)"
              class="pricing-card__btn pricing-card__btn--active"
              :to="{ name: 'purchase', params: { planCode: plan.code } }"
            >
              购买或兑换
            </router-link>
            <button
              v-else
              class="pricing-card__btn pricing-card__btn--disabled"
              disabled
              title="链动小铺商品链接尚未配置"
            >
              即将开放
            </button>
          </div>
        </div>
      </section>

      <section class="pricing-redeem" aria-labelledby="pricing-redeem-title">
        <div>
          <span class="pricing-redeem__eyebrow">已在外部渠道购买？</span>
          <h2 id="pricing-redeem-title">兑换套餐权益码</h2>
          <p>兑换码只使用一次；套餐和到期日以微光数据库返回结果为准。</p>
        </div>
        <button v-if="!redeemOpen" type="button" class="pricing-redeem__toggle" @click="openRedeem">
          输入兑换码
        </button>
        <form v-else-if="auth.isLoggedIn" class="pricing-redeem__form" @submit.prevent="submitRedemption">
          <label for="pricingRedeemCode">兑换码</label>
          <div class="pricing-redeem__controls">
            <input
              id="pricingRedeemCode"
              v-model="redeemCode"
              type="password"
              autocomplete="one-time-code"
              maxlength="80"
              placeholder="WG-XXXX-XXXX-XXXX-XXXX"
              :disabled="redeeming"
            />
            <button type="submit" :disabled="!redeemCode.trim() || redeeming">
              {{ redeeming ? "兑换中…" : "立即兑换" }}
            </button>
          </div>
          <p v-if="redeemMessage" class="pricing-redeem__message" aria-live="polite">{{ redeemMessage }}</p>
        </form>
        <button v-else type="button" class="pricing-redeem__toggle" @click="auth.authDialogOpen = true">
          登录后兑换
        </button>
      </section>

      <!-- Detailed Comparison Table -->
      <section class="pricing-comparison">
        <h2 class="pricing-section-title">权益对比</h2>
        <div class="pricing-table-wrap">
          <table class="pricing-table">
            <thead>
              <tr>
                <th>功能权益</th>
                <th v-for="plan in planList" :key="plan.code" :class="{ 'col-featured': PLAN_PRESENTATION[plan.code].featured }">
                  {{ plan.name }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="metric in QUOTA_METRICS" :key="metric.key">
                <td>{{ metric.label }}</td>
                <td v-for="plan in planList" :key="plan.code" :class="{ 'col-featured': PLAN_PRESENTATION[plan.code].featured, 'text-muted': plan.limits[metric.planLimit] === 0 }">
                  {{ planLimitText(plan, metric) }}<template v-if="plan.limits[metric.planLimit] > 0"> / {{ plan.code === 'free' ? `首次 ${plan.billing_period_days} 天` : `${plan.billing_period_days} 天` }}</template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Explanation & Privacy Notes -->
      <section class="pricing-notes">
        <div class="pricing-note-card">
          <h3 class="pricing-note-card__title">
            <span>📊</span> 如何计算额度
          </h3>
          <p class="pricing-note-card__content">
            AI 语音时长仅计算微光为您合成并播放的回答时间。您的麦克风由浏览器完成本地/系统级转写，微光服务端不接收麦克风原始录音；浏览器厂商可能会使用在线识别服务。
          </p>
        </div>
        <div class="pricing-note-card">
          <h3 class="pricing-note-card__title">
            <span>🛡️</span> 声音授权与隐私安全
          </h3>
          <p class="pricing-note-card__content">
            请仅复刻本人声音或已获得声音权利人明确授权的声音。微光始终以 AI 身份回应，不冒充真实的人；所有音色仅在您的账号内私有使用。
          </p>
        </div>
      </section>
      <nav class="pricing-legal-links" aria-label="隐私与协议">
        <router-link to="/privacy">隐私政策</router-link>
        <router-link to="/terms">用户协议</router-link>
        <router-link to="/data-rights">数据保留与删除</router-link>
      </nav>
    </main>
  </div>
</template>
