// Shared 3D particle-orb canvas renderer. Deduplicates the ~80% identical
// orb code from the old chat.js and voice.js. Each view owns its own instance
// and drives the state via `setState`.
import { onBeforeUnmount, onMounted, type Ref } from "vue";

export type OrbState = "idle" | "listening" | "thinking" | "speaking";

interface Particle {
  bx: number;
  by: number;
  bz: number;
  phase: number;
  spread: number;
}

const STATE_TABLE: Record<OrbState, { rot: number; amp: number; jitter: number; radial: number; swirl: number }> = {
  idle: { rot: 0.0022, amp: 0.0, jitter: 0.0, radial: 0.0, swirl: 0.0 },
  listening: { rot: 0.001, amp: 0.35, jitter: 0.1, radial: 0.12, swirl: 0.0 },
  thinking: { rot: 0.006, amp: 0.15, jitter: 0.02, radial: 0.0, swirl: 0.25 },
  speaking: { rot: 0.003, amp: 0.7, jitter: 0.04, radial: 0.3, swirl: 0.0 },
};

function rotate(p: Particle, ry: number, rx: number) {
  const cosY = Math.cos(ry);
  const sinY = Math.sin(ry);
  const x1 = p.bx * cosY - p.bz * sinY;
  const z1 = p.bx * sinY + p.bz * cosY;
  const cosX = Math.cos(rx);
  const sinX = Math.sin(rx);
  const y1 = p.by * cosX - z1 * sinX;
  const z2 = p.by * sinX + z1 * cosX;
  return { x: x1, y: y1, z: z2 };
}

export interface UseOrbOptions {
  particleCount?: number;
  state: Ref<OrbState>;
}

export function useOrb(canvasRef: Ref<HTMLCanvasElement | null>, options: UseOrbOptions) {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const particleCount = options.particleCount ?? 140;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  let ctx: CanvasRenderingContext2D | null = null;
  let W = 0;
  let H = 0;
  let cx = 0;
  let cy = 0;
  let R = 0;
  let particles: Particle[] = [];
  let rotY = 0;
  let rotX = -0.25;
  let t = 0;
  let amplitude = 0;
  let ampTarget = 0;
  let speechUntil = 0;
  let raf = 0;
  let resizeTimer = 0;
  let resizeObserver: ResizeObserver | null = null;
  let visibilityBound = false;

  function makeParticles() {
    particles = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < particleCount; i += 1) {
      const y = 1 - (i / (particleCount - 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = golden * i;
      particles.push({
        bx: Math.cos(theta) * r,
        by: y,
        bz: Math.sin(theta) * r,
        phase: Math.random() * Math.PI * 2,
        spread: 0.7 + Math.random() * 0.6,
      });
    }
  }

  function resize() {
    const canvas = canvasRef.value;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    W = rect.width;
    H = rect.height;
    if (W < 2 || H < 2) return;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx = canvas.getContext("2d");
    ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
    cx = W / 2;
    cy = H / 2;
    R = Math.min(W, H) * 0.27;
  }

  function draw() {
    raf = 0;
    if (!ctx) return;
    t += 0.016;
    const cfg = STATE_TABLE[options.state.value];
    rotY += cfg.rot * (reduceMotion ? 0.3 : 1);
    rotX += Math.sin(t * 0.3) * 0.0006;

    if (options.state.value === "speaking") {
      speechUntil -= 0.016;
      if (speechUntil <= 0) {
        if (Math.random() < 0.12) {
          ampTarget = 0.05;
          speechUntil = 0.12 + Math.random() * 0.18;
        } else {
          ampTarget = 0.45 + Math.random() * 0.55;
          speechUntil = 0.09 + Math.random() * 0.13;
        }
      }
    } else if (options.state.value === "listening") {
      ampTarget = 0.3 + 0.12 * Math.sin(t * 2.4);
    }
    amplitude += (ampTarget - amplitude) * 0.18;

    const breath = 1 + 0.035 * Math.sin(t * 1.2);
    ctx.clearRect(0, 0, W, H);

    const coreR = R * (1.05 + amplitude * 0.25) * breath;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
    g.addColorStop(0, `rgba(251, 246, 236, ${0.16 + amplitude * 0.14})`);
    g.addColorStop(0.55, `rgba(251, 246, 236, ${0.05 + amplitude * 0.05})`);
    g.addColorStop(1, "rgba(251, 246, 236, 0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    ctx.fill();

    const projected: Array<{ x: number; y: number; z: number; size: number }> = [];
    const radial = cfg.radial * (0.4 + amplitude);
    const jitter = cfg.jitter * (0.5 + amplitude);
    const swirl = cfg.swirl;

    for (let i = 0; i < particles.length; i += 1) {
      const p = particles[i];
      const noise = Math.sin(t * 2.2 + p.phase) * 0.5 + 0.5;
      const disp = 1 + radial * (noise * p.spread);
      const jx = jitter * Math.sin(t * 5 + p.phase * 3);
      const jy = jitter * Math.cos(t * 4.6 + p.phase * 2);
      let bx = p.bx * disp + jx;
      let by = p.by * disp + jy;
      let bz = p.bz * disp;
      if (swirl) {
        const sw = swirl * (0.5 + p.by);
        const csw = Math.cos(sw);
        const ssw = Math.sin(sw);
        const nx = bx * csw - bz * ssw;
        bz = bx * ssw + bz * csw;
        bx = nx;
      }
      const rp = rotate({ bx, by, bz } as Particle, rotY, rotX);
      const scale = 2.6 / (2.6 + rp.z);
      projected.push({
        x: cx + rp.x * scale * R * breath,
        y: cy + rp.y * scale * R * breath,
        z: rp.z,
        size: (0.6 + scale * 1.7) * (0.7 + amplitude * 0.5),
      });
    }
    projected.sort((a, b) => a.z - b.z);
    for (let k = 0; k < projected.length; k += 1) {
      const pr = projected[k];
      const depth = (pr.z + 1) / 2;
      let alpha = Math.min(1, (0.18 + depth * 0.7) * (0.8 + amplitude * 0.6));
      ctx.beginPath();
      ctx.arc(pr.x, pr.y, pr.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(251, 246, 236, ${alpha.toFixed(3)})`;
      ctx.fill();
    }

    if (options.state.value === "listening") {
      const ringR = R * 1.45 + Math.sin(t * 2) * 4;
      ctx.beginPath();
      ctx.arc(cx, cy, ringR, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(251, 246, 236, ${0.05 + 0.04 * Math.sin(t * 2)})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    raf = requestAnimationFrame(draw);
  }

  function loop() {
    if (!raf) raf = requestAnimationFrame(draw);
  }

  function stop() {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = 0;
    }
  }

  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(resize, 150);
  }

  function onVisibility() {
    if (document.hidden) stop();
    else loop();
  }

  onMounted(() => {
    resize();
    makeParticles();
    loop();
    const canvas = canvasRef.value;
    if (canvas && "ResizeObserver" in window) {
      resizeObserver = new ResizeObserver(() => {
        resize();
        loop();
      });
      resizeObserver.observe(canvas);
    }
    window.addEventListener("resize", onResize);
    document.addEventListener("visibilitychange", onVisibility);
    visibilityBound = true;
  });

  onBeforeUnmount(() => {
    stop();
    resizeObserver?.disconnect();
    window.removeEventListener("resize", onResize);
    if (visibilityBound) document.removeEventListener("visibilitychange", onVisibility);
  });

  return { resize };
}

export { STATE_TABLE };
