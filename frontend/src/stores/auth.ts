import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { Profile, BillingSummary, PlanDefinition } from "../types";
import * as api from "../api";
import { useVoiceConfigStore } from "./voiceConfig";

export const useAuthStore = defineStore("auth", () => {
  const profile = ref<Profile | null>(null);
  const billingSummary = ref<BillingSummary | null>(null);
  const billingStatus = ref<"idle" | "loading" | "ready" | "error">("idle");
  const billingError = ref("");
  const plans = ref<PlanDefinition[]>([]);
  const initialized = ref(false);
  const authDialogOpen = ref(false);
  const accountDialogOpen = ref(false);
  const authMode = ref<"login" | "register">("login");

  let readyPromise: Promise<Profile | null> | null = null;

  const isLoggedIn = computed(() => profile.value !== null);
  const quotaRemaining = computed(() => profile.value?.quota_remaining ?? 0);

  function canRequest(): boolean {
    return profile.value !== null && billingSummary.value?.status !== "expired";
  }

  function applyProfile(next: Profile | null) {
    profile.value = next;
  }

  function resetBilling() {
    billingSummary.value = null;
    billingStatus.value = "idle";
    billingError.value = "";
  }

  function isConfirmedBillingSummary(summary: BillingSummary): boolean {
    if (!(["free", "plus", "pro"] as const).includes(summary.plan_code)) return false;
    if (!(["active", "expired"] as const).includes(summary.status)) return false;
    const accessEnd = summary.renewed_until || summary.access_ends_at || summary.period_end;
    return typeof summary.period_start === "string"
      && Number.isFinite(Date.parse(summary.period_start))
      && typeof accessEnd === "string"
      && Number.isFinite(Date.parse(accessEnd));
  }

  /** Idempotent: initializes the profile. Resolves with it. */
  function ensureReady(): Promise<Profile | null> {
    if (readyPromise) return readyPromise;
    readyPromise = (async () => {
      void fetchPlans().catch(() => undefined);
      const me = await api.fetchMe();
      applyProfile(me);
      initialized.value = true;
      return me;
    })();
    return readyPromise;
  }

  async function fetchMe() {
    const me = await api.fetchMe();
    applyProfile(me);
    return me;
  }

  async function doLogin(email: string, password: string) {
    const me = await api.login({ email, password });
    resetBilling();
    applyProfile(me);
    readyPromise = Promise.resolve(me);
    void useVoiceConfigStore().ensureReady(me.id);
    void fetchBilling();
    authDialogOpen.value = false;
    return me;
  }

  async function doRegister(email: string, password: string, nickname: string) {
    const me = await api.register({ email, password, nickname });
    resetBilling();
    applyProfile(me);
    readyPromise = Promise.resolve(me);
    void useVoiceConfigStore().ensureReady(me.id);
    void fetchBilling();
    authDialogOpen.value = false;
    return me;
  }

  async function doLogout() {
    await api.logout();
    applyProfile(null);
    resetBilling();
    useVoiceConfigStore().reset();
    readyPromise = Promise.resolve(null);
    initialized.value = true;
    accountDialogOpen.value = false;
    authMode.value = "login";
    authDialogOpen.value = false;
  }

  async function doDeleteAccount() {
    const result = await api.deleteAccount();
    applyProfile(null);
    resetBilling();
    useVoiceConfigStore().reset();
    readyPromise = Promise.resolve(null);
    initialized.value = true;
    authDialogOpen.value = false;
    authMode.value = "login";
    return result;
  }

  async function saveNickname(nickname: string) {
    const me = await api.patchMe({ nickname });
    applyProfile(me);
    return me;
  }

  async function saveAvatar(file: File) {
    const me=await api.uploadAccountAvatar(file);
    applyProfile(me);
    return me;
  }

  async function fetchBilling() {
    if (!profile.value) {
      resetBilling();
      return null;
    }
    billingStatus.value = "loading";
    billingError.value = "";
    try {
      const summary = await api.fetchBillingSummary();
      if (!isConfirmedBillingSummary(summary)) throw new Error("套餐状态校验失败，请重试");
      billingSummary.value = summary;
      billingStatus.value = "ready";
      return summary;
    } catch (error) {
      billingSummary.value = null;
      billingStatus.value = "error";
      billingError.value = (error as Error).message || "套餐状态校验失败，请重试";
      return null;
    }
  }

  async function fetchPlans() {
    const nextPlans = await api.fetchPlans();
    plans.value = nextPlans;
    return nextPlans;
  }

  async function redeemSubscriptionCode(code: string) {
    const result = await api.redeemSubscriptionCode(code);
    billingSummary.value = result.billing;
    billingStatus.value = "ready";
    billingError.value = "";
    return result;
  }

  function openAccount() {
    accountDialogOpen.value = true;
    void fetchBilling();
  }

  function setAuthMode(mode: "login" | "register") {
    authMode.value = mode;
  }

  return {
    profile,
    billingSummary,
    billingStatus,
    billingError,
    plans,
    initialized,
    authDialogOpen,
    accountDialogOpen,
    authMode,
    isLoggedIn,
    quotaRemaining,
    canRequest,
    ensureReady,
    fetchMe,
    fetchBilling,
    fetchPlans,
    redeemSubscriptionCode,
    doLogin,
    doRegister,
    doLogout,
    doDeleteAccount,
    saveNickname,
    saveAvatar,
    openAccount,
    setAuthMode,
  };
});
