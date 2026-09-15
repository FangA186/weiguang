/**
 * Audio encoding and slicing utilities using Web Audio API.
 * Encodes AudioBuffer into standard 16-bit PCM RIFF WAV format.
 */

export function sliceAudioBuffer(
  ctx: BaseAudioContext,
  buffer: AudioBuffer,
  startSec: number,
  endSec: number,
): AudioBuffer {
  const sampleRate = buffer.sampleRate;
  const totalDuration = buffer.duration;
  const clampedStart = Math.max(0, Math.min(startSec, totalDuration));
  const clampedEnd = Math.max(clampedStart, Math.min(endSec, totalDuration));

  const startOffset = Math.floor(clampedStart * sampleRate);
  const endOffset = Math.max(startOffset + 1, Math.floor(clampedEnd * sampleRate));
  const frameCount = endOffset - startOffset;

  const newBuffer = ctx.createBuffer(buffer.numberOfChannels, frameCount, sampleRate);

  for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
    const sourceData = buffer.getChannelData(channel);
    const destData = newBuffer.getChannelData(channel);
    destData.set(sourceData.subarray(startOffset, endOffset));
  }

  return newBuffer;
}

export function encodeWAV(buffer: AudioBuffer): Blob {
  const numChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const format = 1; // 1 = PCM
  const bitDepth = 16;
  const bytesPerSample = bitDepth / 8;
  const blockAlign = numChannels * bytesPerSample;

  const numFrames = buffer.length;
  const dataByteLength = numFrames * blockAlign;
  const totalByteLength = 44 + dataByteLength;

  const arrayBuffer = new ArrayBuffer(totalByteLength);
  const view = new DataView(arrayBuffer);

  function writeString(offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  // 1. RIFF chunk descriptor
  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataByteLength, true);
  writeString(8, "WAVE");

  // 2. "fmt " sub-chunk
  writeString(12, "fmt ");
  view.setUint32(16, 16, true); // SubChunk1Size (16 for PCM)
  view.setUint16(20, format, true); // AudioFormat (1 for PCM)
  view.setUint16(22, numChannels, true); // NumChannels
  view.setUint32(24, sampleRate, true); // SampleRate
  view.setUint32(28, sampleRate * blockAlign, true); // ByteRate
  view.setUint16(32, blockAlign, true); // BlockAlign
  view.setUint16(34, bitDepth, true); // BitsPerSample

  // 3. "data" sub-chunk
  writeString(36, "data");
  view.setUint32(40, dataByteLength, true);

  // 4. Write interleaved 16-bit PCM samples
  const channelData: Float32Array[] = [];
  for (let c = 0; c < numChannels; c++) {
    channelData.push(buffer.getChannelData(c));
  }

  let offset = 44;
  for (let i = 0; i < numFrames; i++) {
    for (let c = 0; c < numChannels; c++) {
      let sample = channelData[c][i];
      // Clamp between -1.0 and 1.0
      sample = Math.max(-1, Math.min(1, sample));
      // Scale to signed 16-bit integer (-32768 to 32767)
      const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      view.setInt16(offset, intSample, true);
      offset += 2;
    }
  }

  return new Blob([arrayBuffer], { type: "audio/wav" });
}

export async function normalizeVoiceReference(file: File): Promise<File> {
  const context = new AudioContext();
  try {
    const decoded = await context.decodeAudioData(await file.arrayBuffer());
    const sampleRate = 48000;
    const offline = new OfflineAudioContext(1, Math.max(1, Math.ceil(decoded.duration * sampleRate)), sampleRate);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();
    const rendered = await offline.startRendering();
    const baseName = file.name.replace(/\.[^.]+$/, "") || "voice-reference";
    return new File([encodeWAV(rendered)], `${baseName}_48k_mono.wav`, { type: "audio/wav" });
  } finally {
    await context.close();
  }
}
