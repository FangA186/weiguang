import { streamChatAndTTS } from '../api';
import { pcm16MonoToWavBlob, readWavResponse } from './audioResponse';

export async function loadSpeechReplay(turnId: string) {
  const response = await fetch(`/api/speech-turns/${encodeURIComponent(turnId)}/audio`, { credentials:'same-origin' });
  if (response.ok) return readWavResponse(response);
  if (response.status !== 410) throw new Error('原语音未完整生成或无权访问');
  const chunks: Uint8Array[] = [];
  let sampleRate = 24000;
  let total = 0;
  let failure = '';
  let complete = false;
  const abort = new AbortController();
  await streamChatAndTTS([{role:'user',content:'恢复已保存的朗读计划'}], { replayTurnId: turnId }, event => {
    if (event.type === 'audio.delta' && event.audio) {
      const bytes = Uint8Array.from(atob(event.audio), c => c.charCodeAt(0));
      total += bytes.length;
      if (total > 12 * 1024 * 1024) { failure = '语音过长，无法缓存'; abort.abort(); return; }
      sampleRate = event.sample_rate || sampleRate;
      chunks.push(bytes);
    }
    if (['audio.error','audio.quota_exhausted','error'].includes(event.type)) failure = event.message || '重播合成未完成';
    if (event.type === 'audio.asset') complete = true;
  }, abort.signal);
  const blob = pcm16MonoToWavBlob(chunks, sampleRate);
  if (failure || !blob || !complete) throw new Error(failure || '语音未完整生成，请重试');
  return blob;
}
