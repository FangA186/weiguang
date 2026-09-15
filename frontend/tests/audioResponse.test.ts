import assert from "node:assert/strict";
import test from "node:test";
import { loadWavWithFallback, pcm16MonoToWavBlob, readWavResponse } from "../src/lib/audioResponse.ts";

test("accepts WAV bytes even when the CDN sends a generic content type", async () => {
  const bytes = new TextEncoder().encode("RIFF\u0004\u0000\u0000\u0000WAVEdata");
  const blob = await readWavResponse(new Response(bytes, {
    headers: { "Content-Type": "application/octet-stream" },
  }));

  assert.equal(blob.type, "audio/wav");
  assert.equal(blob.size, bytes.length);
});

test("rejects a non-audio error body", async () => {
  await assert.rejects(
    readWavResponse(new Response('{"error":"not ready"}', {
      headers: { "Content-Type": "application/json" },
    })),
    /语音音频格式无效/,
  );
});

test("replaces an invalid reused URL during the same playback request", async () => {
  const invalidUrl = "data:application/json,%7B%22error%22%3A%22not%20ready%22%7D";
  const validUrl = "data:application/octet-stream;base64,UklGRgQAAABXQVZFZGF0YQ==";
  let created = 0;

  const result = await loadWavWithFallback(invalidUrl, async () => {
    created += 1;
    return validUrl;
  });

  assert.equal(created, 1);
  assert.equal(result.url, validUrl);
  assert.equal(result.blob.type, "audio/wav");
});

test("wraps streamed PCM chunks into one replayable WAV", async () => {
  const first = new Uint8Array([1, 0, 2, 0]);
  const second = new Uint8Array([3, 0, 4, 0]);
  const wav = pcm16MonoToWavBlob([first, second]);

  assert.ok(wav);
  const bytes = new Uint8Array(await wav.arrayBuffer());
  assert.equal(new TextDecoder().decode(bytes.slice(0, 4)), "RIFF");
  assert.equal(new TextDecoder().decode(bytes.slice(8, 12)), "WAVE");
  assert.deepEqual([...bytes.slice(44)], [1, 0, 2, 0, 3, 0, 4, 0]);
});
