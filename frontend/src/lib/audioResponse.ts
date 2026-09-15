export async function readWavResponse(response: Response): Promise<Blob> {
  if (!response.ok) {
    throw new Error(`语音音频下载失败（HTTP ${response.status}）`);
  }

  const blob = await response.blob();
  if (!blob.size) throw new Error("语音音频为空");

  const header = new Uint8Array(await blob.slice(0, 12).arrayBuffer());
  const isWav = header.length === 12
    && String.fromCharCode(...header.slice(0, 4)) === "RIFF"
    && String.fromCharCode(...header.slice(8, 12)) === "WAVE";
  if (!isWav) throw new Error("语音音频格式无效");

  return new Blob([blob], { type: "audio/wav" });
}

export function pcm16MonoToWavBlob(chunks: Uint8Array[], sampleRate = 24000): Blob | null {
  const pcmBytes = chunks.reduce((total, chunk) => total + chunk.byteLength, 0);
  if (!pcmBytes) return null;

  const wav = new ArrayBuffer(44 + pcmBytes);
  const view = new DataView(wav);
  const write = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) view.setUint8(offset + index, value.charCodeAt(index));
  };
  write(0, "RIFF");
  view.setUint32(4, 36 + pcmBytes, true);
  write(8, "WAVEfmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  write(36, "data");
  view.setUint32(40, pcmBytes, true);
  const output = new Uint8Array(wav, 44);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new Blob([wav], { type: "audio/wav" });
}

export async function loadWavWithFallback(
  initialUrl: string | undefined,
  createUrl: () => Promise<string>,
): Promise<{ blob: Blob; url: string }> {
  let url = initialUrl;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    if (!url) url = await createUrl();
    try {
      return { blob: await readWavResponse(await fetch(url)), url };
    } catch (error) {
      if (!initialUrl || attempt > 0) throw error;
      url = undefined;
    }
  }
  throw new Error("语音音频格式无效");
}
