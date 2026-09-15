import assert from "node:assert/strict";
import test from "node:test";
import { resolveTtsSettings, messageTtsCachePayload } from "../src/lib/ttsSettings.ts";
import { pcm16MonoToWavBlob } from "../src/lib/audioResponse.ts";

test("OCR description cannot suppress manual pace/emotion selection", () => {
  const settings = resolveTtsSettings({ instruction: "语速缓慢，温柔", pace: "fast", emotion: "angry" });
  assert.equal(settings.rate, 1.15);
  assert.match(settings.instruction, /语速缓慢，温柔/);
  assert.match(settings.instruction, /本次朗读以以下设置为准：情绪为克制地表达不满/);
  assert.ok(resolveTtsSettings({ instruction: "字".repeat(2000) }).instruction.length <= 1000);
});

test("voice settings create separate cache entries; identical settings reuse them", () => {
  const base = { ...resolveTtsSettings(), voice: "voice-a" };
  const key = messageTtsCachePayload("user-a", 1, "你好", base);
  assert.equal(key, messageTtsCachePayload("user-a", 1, "你好", { ...base }));
  for (const patch of [{ rate: 0.85 }, { sample_rate: 48000 }, { instruction: "开心" }, { voice: "voice-b" }]) {
    assert.notEqual(key, messageTtsCachePayload("user-a", 1, "你好", { ...base, ...patch }));
  }
});

test("48 kHz PCM encodes correct WAV duration and header", async () => {
  const wav = pcm16MonoToWavBlob([new Uint8Array(96000)], 48000)!;
  const view = new DataView(await wav.arrayBuffer());
  assert.equal(view.getUint32(24, true), 48000);
  assert.equal(view.getUint32(40, true) / view.getUint32(28, true), 1);
});
