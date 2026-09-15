import type { VoiceProfile } from '../types';

export function instructionUnits(text: string): number {
  return Array.from(text).reduce((sum, char) => sum + (char.codePointAt(0)! <= 127 ? 1 : 2), 0);
}

export function previewVoiceInstruction(style: VoiceProfile): string {
  if (style.use_defaults) return '';
  const manual = (style.emotion_mode || (style.emotion ? 'manual' : 'auto')) === 'manual';
  const tone = manual
    ? { calm:'平静', gentle:'温柔', cheerful:'愉快', playful:'俏皮', sad:'低落', angry:'克制地表达不满' }[style.emotion || 'calm']
    : '自然交谈';
  return [tone, style.presentation, style.age_feel, ...(style.traits || []), style.instruction].filter(Boolean).join('，');
}
