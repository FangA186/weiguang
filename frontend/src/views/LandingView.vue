<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useAuthStore } from "../stores/auth";
import "../assets/styles/landing.css";

const year = new Date().getFullYear();
const auth = useAuthStore();
const nav = ref<HTMLElement | null>(null);
const canvas = ref<HTMLCanvasElement | null>(null);
const themePicker = ref<HTMLElement | null>(null);
const themeMenuOpen = ref(false);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const themes = [
  { id: "weiguang-original", name: "微光原色", colors: ["#FBF6EC", "#000000"] },
  { id: "mars-rose", name: "马尔斯绿 × 玫瑰粉", colors: ["#01847F", "#F9D2E4"] },
  { id: "ivory-cinnabar", name: "象牙白 × 朱砂红", colors: ["#FFFFF0", "#C01E25"] },
  { id: "lemon-sea", name: "柠檬黄 × 海蓝", colors: ["#F0FF0A", "#1E9BFF"] },
  { id: "cherry-clearwater", name: "樱花粉 × 清水蓝", colors: ["#F78A88", "#3F389F"] },
  { id: "amber-kingfisher", name: "琥珀黄 × 青雀头黛", colors: ["#F9B800", "#153C46"] },
  { id: "cloud-cyan", name: "云白 × 青蓝", colors: ["#F8FFFF", "#00B7C7"] },
  { id: "ice-wine", name: "冰薄荷 × 酒莓", colors: ["#88E7D2", "#A82F4F"] },
  { id: "barbie-moss", name: "芭比粉 × 苔绿", colors: ["#F1BBC9", "#4D613C"] },
  { id: "blaze-neon", name: "炽焰红 × 霓虹黑", colors: ["#E61A23", "#0A090C"] },
  { id: "mint-brick", name: "薄荷青 × 砖褐棕", colors: ["#BBF0EA", "#8D4726"] },
] as const;
const defaultTheme = "weiguang-original";
const activeTheme = ref(defaultTheme);
const selectedTheme = computed(() => themes.find((theme) => theme.id === activeTheme.value) ?? themes[0]);
const activeThemeColors = computed(() => selectedTheme.value.colors);

let raf = 0;
let resizeTimer = 0;
let ctx: CanvasRenderingContext2D | null = null;
const dpr = Math.min(window.devicePixelRatio || 1, 2);
let w = 0;
let h = 0;
let particleRgb = "251, 246, 236";
let particles: Array<{ x: number; y: number; r: number; vx: number; vy: number; a: number; tw: number; tws: number }> = [];

const accountInitial = computed(() => {
  const source = (auth.profile?.nickname || auth.profile?.email || "我").trim();
  return source.slice(0, 1).toUpperCase();
});


function openAccountEntry() {
  if (auth.isLoggedIn) {
    auth.openAccount();
    return;
  }
  auth.setAuthMode("login");
  auth.authDialogOpen = true;
}

function selectTheme(themeId: string) {
  activeTheme.value = themes.some((theme) => theme.id === themeId) ? themeId : defaultTheme;
  document.documentElement.dataset.theme = activeTheme.value;
  particleRgb = getComputedStyle(document.documentElement).getPropertyValue("--light-rgb").trim() || "251, 246, 236";
  themeMenuOpen.value = false;
}

function closeThemeMenuOnOutsidePointer(event: PointerEvent) {
  if (!themePicker.value?.contains(event.target as Node)) themeMenuOpen.value = false;
}

function rand(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

function spawn() {
  return {
    x: rand(0, w),
    y: rand(0, h),
    r: rand(0.4, 1.6),
    vx: rand(-0.12, 0.12),
    vy: rand(-0.18, -0.04),
    a: rand(0.15, 0.6),
    tw: rand(0, Math.PI * 2),
    tws: rand(0.004, 0.012),
  };
}

function resize() {
  const canvasEl = canvas.value;
  if (!canvasEl) return;
  w = window.innerWidth;
  h = window.innerHeight;
  canvasEl.width = w * dpr;
  canvasEl.height = h * dpr;
  canvasEl.style.width = w + "px";
  canvasEl.style.height = h + "px";
  ctx = canvasEl.getContext("2d");
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function initParticles() {
  const count = window.innerWidth < 760 ? 36 : 70;
  particles = [];
  for (let i = 0; i < count; i += 1) particles.push(spawn());
}

function draw() {
  if (!ctx) return;
  ctx.clearRect(0, 0, w, h);
  for (let i = 0; i < particles.length; i += 1) {
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    p.tw += p.tws;
    if (p.y < -10) {
      p.y = h + 10;
      p.x = rand(0, w);
    }
    if (p.x < -10) p.x = w + 10;
    if (p.x > w + 10) p.x = -10;
    const flicker = 0.5 + 0.5 * Math.sin(p.tw);
    const alpha = p.a * (0.4 + 0.6 * flicker);
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${particleRgb}, ${alpha.toFixed(3)})`;
    ctx.fill();
  }
  raf = requestAnimationFrame(draw);
}

function start() {
  if (!raf) raf = requestAnimationFrame(draw);
}
function stop() {
  if (raf) {
    cancelAnimationFrame(raf);
    raf = 0;
  }
}

function onScroll() {
  if (!nav.value) return;
  nav.value.classList.toggle("scrolled", window.scrollY > 40);
}

function onResize() {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(() => {
    stop();
    resize();
    initParticles();
    start();
  }, 200);
}

function onVisibility() {
  if (document.hidden) stop();
  else start();
}

let observer: IntersectionObserver | null = null;

onMounted(async () => {
  selectTheme(document.documentElement.dataset.theme || defaultTheme);
  await nextTick();
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
  document.addEventListener("pointerdown", closeThemeMenuOnOutsidePointer);

  const reveals = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || reduceMotion) {
    reveals.forEach((el) => el.classList.add("visible"));
  } else {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer?.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    reveals.forEach((el) => observer?.observe(el));
  }

  if (!reduceMotion) {
    resize();
    initParticles();
    start();
    window.addEventListener("resize", onResize);
    document.addEventListener("visibilitychange", onVisibility);
  }
});

onBeforeUnmount(() => {
  stop();
  window.removeEventListener("scroll", onScroll);
  window.removeEventListener("resize", onResize);
  document.removeEventListener("visibilitychange", onVisibility);
  document.removeEventListener("pointerdown", closeThemeMenuOnOutsidePointer);
  observer?.disconnect();
});
</script>

<template>
  <div class="landing">
    <canvas ref="canvas" class="particles" aria-hidden="true"></canvas>

    <header class="nav" ref="nav">
      <div class="nav__inner">
        <a class="nav__logo" href="#top">
          <span class="nav__dot"></span>
          <span class="nav__name">微光</span>
        </a>
        <div class="nav__right">
          <div ref="themePicker" class="theme-picker" @keydown.esc.prevent.stop="themeMenuOpen = false">
            <button
              type="button"
              class="theme-picker__trigger"
              aria-haspopup="listbox"
              :aria-expanded="themeMenuOpen"
              aria-controls="theme-options"
              @click="themeMenuOpen = !themeMenuOpen"
            >
              <span
                class="theme-picker__swatch"
                :style="{ '--swatch-a': activeThemeColors[0], '--swatch-b': activeThemeColors[1] }"
                aria-hidden="true"
              ></span>
              <span class="theme-picker__label">{{ selectedTheme.name }}</span>
              <span class="theme-picker__arrow" aria-hidden="true">⌄</span>
            </button>
            <div v-if="themeMenuOpen" id="theme-options" class="theme-picker__menu" role="listbox" aria-label="全局配色">
              <button
                v-for="theme in themes"
                :key="theme.id"
                type="button"
                class="theme-picker__option"
                :class="{ 'is-selected': activeTheme === theme.id }"
                role="option"
                :aria-selected="activeTheme === theme.id"
                @click="selectTheme(theme.id)"
              >
                <span
                  class="theme-picker__swatch"
                  :style="{ '--swatch-a': theme.colors[0], '--swatch-b': theme.colors[1] }"
                  aria-hidden="true"
                ></span>
                <span>{{ theme.name }}</span>
                <span v-if="activeTheme === theme.id" class="theme-picker__check" aria-hidden="true">✓</span>
              </button>
            </div>
          </div>
          <nav class="nav__links">
            <router-link to="/pricing">计划</router-link>
          </nav>
          <button class="nav__account" :class="{ 'is-logged-in': auth.isLoggedIn }" type="button" @click="openAccountEntry">
            <span v-if="auth.isLoggedIn" class="nav__avatar" aria-hidden="true">{{ accountInitial }}</span>
            <span>{{ auth.isLoggedIn ? "个人中心" : "登录" }}</span>
          </button>
        </div>
      </div>
    </header>

    <main id="main-content">
    <section class="hero" id="top">
      <div class="hero__orb" aria-hidden="true">
        <div class="hero__core"></div>
        <div class="hero__halo"></div>
      </div>
      <p class="hero__kicker">黑暗中出现的一点光</p>
      <h1 class="hero__title">
        不是替代某个人<br />
        而是在最难熬的时候<br />
        <span class="hero__title-em">陪你重新开始说话</span>
      </h1>
      <p class="hero__sub">生成一个专属的虚拟陪伴角色。</p>
      <div class="hero__actions">
        <RouterLink class="btn btn--primary" to="/chat">开始陪伴</RouterLink>
      </div>
      <div class="hero__scroll" aria-hidden="true"><span class="hero__scroll-line"></span></div>
    </section>

    <section class="chapter" id="longing">
      <div class="chapter__inner reveal">
        <p class="chapter__index">01</p>
        <h2 class="chapter__title">你怀念的，也许不只是那个人。</h2>
        <div class="chapter__body">
          <p>而是深夜里有人回应，</p>
          <p>分享日常时有人听懂，</p>
          <p>以及那些只有你们才明白的表达方式。</p>
        </div>
      </div>
    </section>

    <section class="chapter chapter--alt" id="how">
      <div class="chapter__inner reveal">
        <p class="chapter__index">02</p>
        <h2 class="chapter__title">陪伴，是怎样发生的</h2>
        <div class="steps">
          <article class="step">
            <div class="step__num">一</div>
            <h3 class="step__title">上传过往</h3>
            <p class="step__text">上传你的过往，生成你的陪伴体验。</p>
          </article>
          <article class="step">
            <div class="step__num">二</div>
            <h3 class="step__title">成为你记忆中的那个人</h3>
            <p class="step__text">理解你们之间独有的表达，让你在需要时感陪伴着你</p>
          </article>
          <article class="step">
            <div class="step__num">三</div>
            <h3 class="step__title">走出过往</h3>
            <p class="step__text">为你生成一个记忆中的那个人，在你需要的时刻，接住没有说完的话。</p>
          </article>
        </div>
      </div>
    </section>

    <section class="chapter" id="boundary">
      <div class="chapter__inner reveal">
        <p class="chapter__index">03</p>
        <h2 class="chapter__title">它是什么，不是什么</h2>
        <div class="duality">
          <div class="duality__col duality__col--is">
            <p class="duality__label">它是</p>
            <ul class="duality__list">
              <li>在突然失落时，可以陪你聊聊的存在</li>
              <li>接住没有说完的话的那个人</li>
              <li>帮你慢慢找回熟悉交流感的陪伴</li>
            </ul>
          </div>
          <div class="duality__divider" aria-hidden="true"></div>
          <div class="duality__col duality__col--isnt">
            <p class="duality__label">它不是</p>
            <ul class="duality__list">
              <li>它不会冒充对方</li>
              <li>它无法替代真实的人</li>
              <li>它始终明确标注为 AI</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="chapter chapter--alt" id="control">
      <div class="chapter__inner reveal">
        <p class="chapter__index">04</p>
        <h2 class="chapter__title">始终在你的掌控之中</h2>
        <div class="control-grid">
          <div class="control-item">
            <span class="control-item__icon" aria-hidden="true">◇</span>
            <p class="control-item__title">随时调整</p>
            <p class="control-item__text">调整它的性格、语气和陪伴方式。</p>
          </div>
          <div class="control-item">
            <span class="control-item__icon" aria-hidden="true">⏸</span>
            <p class="control-item__title">随时暂停</p>
            <p class="control-item__text">不想聊的时候，可以随时停下来。</p>
          </div>
          <div class="control-item">
            <span class="control-item__icon" aria-hidden="true">✕</span>
            <p class="control-item__title">随时删除</p>
            <p class="control-item__text">数据随时可删，不留痕迹。</p>
          </div>
          <div class="control-item">
            <span class="control-item__icon" aria-hidden="true">✦</span>
            <p class="control-item__title">始终透明</p>
            <p class="control-item__text">角色始终标注为 AI，聊天仅用于你授权的体验。</p>
          </div>
        </div>
      </div>
    </section>

    <section class="closing" id="closing">
      <div class="closing__inner reveal">
        <div class="closing__orb" aria-hidden="true"></div>
        <p class="closing__line">有些关系已经结束，</p>
        <p class="closing__line">但你的感受不必被强行清空。</p>
        <p class="closing__gap" aria-hidden="true">&nbsp;</p>
        <p class="closing__line">让思念有一个安全的出口，</p>
        <p class="closing__line">也让自己在被陪伴的过程中，慢慢向前走。</p>
        <p class="closing__gap" aria-hidden="true">&nbsp;</p>
        <p class="closing__emph">不是替代某个人，</p>
        <p class="closing__emph">而是在最难熬的时候，陪你重新开始说话。</p>
      </div>
    </section>
    </main>

    <footer class="footer">
      <div class="footer__inner">
        <div class="footer__brand">
          <span class="footer__dot"></span>
          <span>微光</span>
        </div>
        <p class="footer__note">虚拟陪伴角色始终明确标注为 AI。本服务不冒充、不替代任何真实的人。</p>
        <p class="footer__copy">© {{ year }} 微光 · 让思念有安全的出口</p>
      </div>
    </footer>
  </div>
</template>
