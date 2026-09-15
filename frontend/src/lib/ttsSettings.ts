import type { PersonaLayer2 } from "../types";

export function resolveTtsSettings(style: PersonaLayer2["voice_style"] = {}) {
  const rate = typeof style.rate === 'number' && Number.isFinite(style.rate) ? Math.max(.5,Math.min(2,style.rate)) : { slow: 0.85, normal: 1, fast: 1.15 }[style.pace || "normal"] || 1;
  const emotion = { calm: "平静", gentle: "温柔", cheerful: "愉快", playful: "俏皮", sad: "克制低落", angry: "克制地表达不满" }[style.emotion || "gentle"] || "温柔";
  const custom = typeof style.instruction === "string" ? style.instruction.trim().slice(0, 800) : "";
  const dimensions = [style.presentation, style.age_feel, style.pitch_hint, ...(style.traits || []), style.scenario].filter(Boolean).join('、');
  return {
    pitch: style.pitch ?? 1,
    use_defaults: style.use_defaults ?? false,
    volume: style.volume ?? 50,
    rate,
    sample_rate: style.sample_rate === 48000 ? 48000 : 24000,
    instruction: [emotion, dimensions, custom].filter(Boolean).join("，").slice(0,1000),
  };
}

export function messageTtsCachePayload(userId: string, messageId: number, text: string, settings: ReturnType<typeof resolveTtsSettings> & { voice?: string }) {
  return JSON.stringify({ version: 2, userId, messageId, text, ...settings });
}
