import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "landing",
      component: () => import("../views/LandingView.vue"),
    },
    {
      path: "/pricing",
      name: "pricing",
      component: () => import("../views/PricingView.vue"),
    },
    {
      path: "/privacy",
      name: "privacy",
      component: () => import("../views/LegalView.vue"),
    },
    {
      path: "/terms",
      name: "terms",
      component: () => import("../views/LegalView.vue"),
    },
    {
      path: "/data-rights",
      name: "data-rights",
      component: () => import("../views/LegalView.vue"),
    },
    {
      path: "/purchase/:planCode(plus|pro)",
      name: "purchase",
      component: () => import("../views/PurchaseView.vue"),
    },
    {
      path: "/chat",
      name: "chat",
      component: () => import("../views/ChatView.vue"),
    },
    {
      path: "/voice",
      name: "voice",
      component: () => import("../views/VoiceView.vue"),
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

// Guard: ensure the session is bootstrapped before entering app pages.
// Landing is open to all; /chat and /voice require login. If a guarded
// route is hit without a session, prompt login and bounce back to landing.
router.beforeEach(async (to) => {
  const auth = useAuthStore();
  await auth.ensureReady();
  const requiresAuth = to.name === "chat" || to.name === "voice";
  if (requiresAuth) {
    if (!auth.isLoggedIn) {
      auth.setAuthMode("login");
      auth.authDialogOpen = true;
      return { name: "landing" };
    }
  }
  return true;
});

export default router;
