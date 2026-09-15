<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { sliceAudioBuffer, encodeWAV } from "../utils/audioEncoder";

const props = defineProps<{
  file: File;
}>();

const emit = defineEmits<{
  (e: "trimmed", payload: { file: File; duration: number }): void;
  (e: "cancel"): void;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const isLoading = ref(true);
const errorMsg = ref("");
const totalDuration = ref(0);
const startTime = ref(0);
const endTime = ref(0);
const isPlaying = ref(false);
const playbackCurrentTime = ref<number | null>(null);

let audioCtx: AudioContext | null = null;
let decodedBuffer: AudioBuffer | null = null;
let currentSourceNode: AudioBufferSourceNode | null = null;
let playbackStartTime = 0;
let playbackOffset = 0;
let animFrameId: number | null = null;

const selectedDuration = computed(() => {
  return Math.max(0, endTime.value - startTime.value);
});

const durationStatus = computed(() => {
  const dur = selectedDuration.value;
  if (dur < 5) {
    return { type: "warn", text: `⚠️ 选区 ${dur.toFixed(1)} 秒（百炼要求至少 5 秒）` };
  }
  if (dur >= 10 && dur <= 20) {
    return { type: "perfect", text: `🌟 选区 ${dur.toFixed(1)} 秒（10–20 秒效果最佳）` };
  }
  if (dur > 30) {
    return { type: "warn", text: `⚠️ 选区 ${dur.toFixed(1)} 秒（建议不超过 30 秒）` };
  }
  return { type: "ok", text: `✓ 选区 ${dur.toFixed(1)} 秒（合规 5–30 秒）` };
});

const isTrimValid = computed(() => {
  return selectedDuration.value >= 3 && selectedDuration.value <= 60;
});

async function loadAndDecodeAudio() {
  isLoading.value = true;
  errorMsg.value = "";
  stopPreview();

  try {
    const arrayBuf = await props.file.arrayBuffer();
    const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!audioCtx || audioCtx.state === "closed") {
      audioCtx = new AudioCtxClass();
    }
    if (audioCtx.state === "suspended") {
      await audioCtx.resume();
    }

    decodedBuffer = await audioCtx.decodeAudioData(arrayBuf);
    totalDuration.value = decodedBuffer.duration;

    // Default selection: start at 0, end at min(15, totalDuration)
    startTime.value = 0;
    endTime.value = Math.min(15, +(decodedBuffer.duration).toFixed(1));

    await nextTick();
    drawWaveform();
  } catch (err: unknown) {
    errorMsg.value = (err as Error).message || "音频解析失败，请检查格式是否有效";
  } finally {
    isLoading.value = false;
  }
}

watch(() => props.file, loadAndDecodeAudio);

// Step adjust helpers
function stepStart(delta: number) {
  const next = Math.max(0, Math.min(+(startTime.value + delta).toFixed(1), +(endTime.value - 1).toFixed(1)));
  startTime.value = next;
  drawWaveform();
}

function stepEnd(delta: number) {
  const next = Math.max(+(startTime.value + 1).toFixed(1), Math.min(totalDuration.value, +(endTime.value + delta).toFixed(1)));
  endTime.value = next;
  drawWaveform();
}

function onStartSliderChange(e: Event) {
  const val = +(e.target as HTMLInputElement).value;
  if (val >= endTime.value) {
    startTime.value = Math.max(0, +(endTime.value - 1).toFixed(1));
  } else {
    startTime.value = val;
  }
  drawWaveform();
}

function onEndSliderChange(e: Event) {
  const val = +(e.target as HTMLInputElement).value;
  if (val <= startTime.value) {
    endTime.value = Math.min(totalDuration.value, +(startTime.value + 1).toFixed(1));
  } else {
    endTime.value = val;
  }
  drawWaveform();
}

function drawWaveform() {
  const canvas = canvasRef.value;
  if (!canvas || !decodedBuffer) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, width, height);

  // Background
  ctx.fillStyle = "#101622";
  ctx.fillRect(0, 0, width, height);

  // Extract peak samples
  const channelData = decodedBuffer.getChannelData(0);
  const totalLength = channelData.length;
  const barCount = Math.floor(width / 4); // each bar 2px wide, 2px gap
  const step = Math.floor(totalLength / barCount);

  // Draw peaks
  const startX = (startTime.value / totalDuration.value) * width;
  const endX = (endTime.value / totalDuration.value) * width;

  for (let i = 0; i < barCount; i++) {
    const x = i * 4;
    let min = 1.0;
    let max = -1.0;

    for (let j = 0; j < step; j++) {
      const datum = channelData[i * step + j];
      if (datum < min) min = datum;
      if (datum > max) max = datum;
    }

    const peak = Math.max(0.04, Math.max(Math.abs(min), Math.abs(max)));
    const barHeight = peak * (height * 0.85);
    const y = (height - barHeight) / 2;

    const inSelection = x >= startX && x <= endX;

    if (inSelection) {
      ctx.fillStyle = "#e6b980";
    } else {
      ctx.fillStyle = "#4a5568";
    }
    ctx.fillRect(x, y, 2, barHeight);
  }

  // Non-selected dim overlay (left)
  if (startX > 0) {
    ctx.fillStyle = "rgba(7, 10, 17, 0.6)";
    ctx.fillRect(0, 0, startX, height);
  }
  // Non-selected dim overlay (right)
  if (endX < width) {
    ctx.fillStyle = "rgba(7, 10, 17, 0.6)";
    ctx.fillRect(endX, 0, width - endX, height);
  }

  // Selected region border / handles
  ctx.strokeStyle = "#e6b980";
  ctx.lineWidth = 2;
  ctx.strokeRect(startX, 0, endX - startX, height);

  // Start Handle Line
  ctx.fillStyle = "#ffd599";
  ctx.fillRect(Math.max(0, startX - 2), 0, 4, height);

  // End Handle Line
  ctx.fillStyle = "#ffd599";
  ctx.fillRect(Math.min(width - 4, endX - 2), 0, 4, height);

  // Playback Cursor
  if (playbackCurrentTime.value !== null && isPlaying.value) {
    const playX = (playbackCurrentTime.value / totalDuration.value) * width;
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(playX - 1.5, 0, 3, height);
  }
}

// Preview playback
function togglePreview() {
  if (isPlaying.value) {
    stopPreview();
  } else {
    startPreview();
  }
}

function startPreview() {
  if (!audioCtx || !decodedBuffer) return;
  stopPreview();

  const source = audioCtx.createBufferSource();
  source.buffer = decodedBuffer;
  source.connect(audioCtx.destination);

  const start = startTime.value;
  const duration = selectedDuration.value;

  playbackOffset = start;
  playbackStartTime = audioCtx.currentTime;
  isPlaying.value = true;
  playbackCurrentTime.value = start;

  source.start(0, start, duration);
  currentSourceNode = source;

  source.onended = () => {
    stopPreview();
  };

  updatePlaybackCursor();
}

function updatePlaybackCursor() {
  if (!isPlaying.value || !audioCtx) return;
  const elapsed = audioCtx.currentTime - playbackStartTime;
  const cur = playbackOffset + elapsed;

  if (cur >= endTime.value) {
    stopPreview();
    return;
  }

  playbackCurrentTime.value = cur;
  drawWaveform();
  animFrameId = requestAnimationFrame(updatePlaybackCursor);
}

function stopPreview() {
  if (currentSourceNode) {
    try {
      currentSourceNode.stop();
      currentSourceNode.disconnect();
    } catch {}
    currentSourceNode = null;
  }
  if (animFrameId) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }
  isPlaying.value = false;
  playbackCurrentTime.value = null;
  drawWaveform();
}

// Confirm trim and export WAV file
async function confirmTrim() {
  if (!audioCtx || !decodedBuffer) return;
  stopPreview();

  try {
    const sliced = sliceAudioBuffer(audioCtx, decodedBuffer, startTime.value, endTime.value);
    const wavBlob = encodeWAV(sliced);

    // Build new file name
    const originalName = props.file.name.replace(/\.[^/.]+$/, "");
    const newFileName = `${originalName}_trim_${selectedDuration.value.toFixed(1)}s.wav`;
    const trimmedFile = new File([wavBlob], newFileName, { type: "audio/wav" });

    emit("trimmed", {
      file: trimmedFile,
      duration: selectedDuration.value,
    });
  } catch (err: unknown) {
    errorMsg.value = `裁剪失败: ${(err as Error).message || "未知错误"}`;
  }
}

function handleCancel() {
  stopPreview();
  emit("cancel");
}

onMounted(() => {
  loadAndDecodeAudio();
});

onBeforeUnmount(() => {
  stopPreview();
  if (audioCtx && audioCtx.state !== "closed") {
    audioCtx.close().catch(() => {});
  }
});
</script>

<template>
  <div class="audio-trimmer">
    <div class="audio-trimmer__header">
      <div class="audio-trimmer__title">
        <span class="audio-trimmer__icon">✂️</span>
        <strong>在线音频裁剪</strong>
        <span class="audio-trimmer__meta" v-if="totalDuration">原时长 {{ totalDuration.toFixed(1) }} 秒</span>
      </div>
      <div class="audio-trimmer__badge" :class="'badge--' + durationStatus.type">
        {{ durationStatus.text }}
      </div>
    </div>

    <!-- Error / Loading -->
    <div v-if="isLoading" class="audio-trimmer__status">
      <span class="audio-trimmer__spinner"></span> 正在解码音频波形…
    </div>
    <div v-else-if="errorMsg" class="audio-trimmer__status audio-trimmer__status--error">
      {{ errorMsg }}
    </div>

    <!-- Canvas Waveform -->
    <div v-show="!isLoading && !errorMsg" class="audio-trimmer__canvas-box">
      <canvas ref="canvasRef" class="audio-trimmer__canvas"></canvas>
      <div class="audio-trimmer__time-tags">
        <span class="time-tag time-tag--start">{{ startTime.toFixed(1) }}s</span>
        <span class="time-tag time-tag--center">选中 {{ selectedDuration.toFixed(1) }}s</span>
        <span class="time-tag time-tag--end">{{ endTime.toFixed(1) }}s</span>
      </div>
    </div>

    <!-- Dual Range Sliders -->
    <div v-if="!isLoading && !errorMsg" class="audio-trimmer__sliders">
      <div class="slider-row">
        <label>起点: {{ startTime.toFixed(1) }}s</label>
        <input
          type="range"
          min="0"
          :max="totalDuration"
          step="0.1"
          :value="startTime"
          @input="onStartSliderChange"
        />
      </div>
      <div class="slider-row">
        <label>终点: {{ endTime.toFixed(1) }}s</label>
        <input
          type="range"
          min="0"
          :max="totalDuration"
          step="0.1"
          :value="endTime"
          @input="onEndSliderChange"
        />
      </div>
    </div>

    <!-- Fine Tuning & Stepper Controls -->
    <div v-if="!isLoading && !errorMsg" class="audio-trimmer__controls">
      <div class="trim-group">
        <span class="trim-label">起点微调</span>
        <div class="btn-stepper">
          <button type="button" class="btn-step" @click="stepStart(-0.5)">-0.5s</button>
          <span class="step-val">{{ startTime.toFixed(1) }}s</span>
          <button type="button" class="btn-step" @click="stepStart(0.5)">+0.5s</button>
        </div>
      </div>

      <div class="trim-group">
        <button
          type="button"
          class="btn-preview-play"
          :class="{ 'is-playing': isPlaying }"
          @click="togglePreview"
        >
          {{ isPlaying ? "⏹ 停止试听" : "▶ 试听选区" }}
        </button>
      </div>

      <div class="trim-group">
        <span class="trim-label">终点微调</span>
        <div class="btn-stepper">
          <button type="button" class="btn-step" @click="stepEnd(-0.5)">-0.5s</button>
          <span class="step-val">{{ endTime.toFixed(1) }}s</span>
          <button type="button" class="btn-step" @click="stepEnd(0.5)">+0.5s</button>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="audio-trimmer__actions">
      <button type="button" class="btn-cancel" @click="handleCancel">取消</button>
      <button
        type="button"
        class="btn-confirm"
        :disabled="!isTrimValid || isLoading"
        @click="confirmTrim"
      >
        ✓ 确认裁剪 (导出为无损 WAV)
      </button>
    </div>
  </div>
</template>

<style scoped>
.audio-trimmer {
  background: rgba(14, 20, 32, 0.95);
  border: 1px solid rgba(230, 185, 128, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audio-trimmer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.audio-trimmer__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #f1f5f9;
}

.audio-trimmer__icon {
  font-size: 1.05rem;
}

.audio-trimmer__meta {
  font-size: 0.78rem;
  color: #94a3b8;
}

.audio-trimmer__badge {
  font-size: 0.76rem;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 500;
}

.badge--perfect {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.badge--ok {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.badge--warn {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.audio-trimmer__status {
  padding: 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
}

.audio-trimmer__status--error {
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 6px;
}

.audio-trimmer__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #e6b980;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.audio-trimmer__canvas-box {
  position: relative;
  background: #101622;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.audio-trimmer__canvas {
  width: 100%;
  height: 90px;
  display: block;
}

.audio-trimmer__time-tags {
  position: absolute;
  bottom: 4px;
  left: 8px;
  right: 8px;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.time-tag {
  font-size: 0.72rem;
  background: rgba(15, 23, 42, 0.75);
  padding: 2px 6px;
  border-radius: 4px;
  color: #cbd5e1;
}

.time-tag--center {
  color: #e6b980;
  font-weight: 600;
}

.audio-trimmer__sliders {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.78rem;
  color: #cbd5e1;
}

.slider-row label {
  width: 90px;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.slider-row input[type="range"] {
  flex: 1;
  accent-color: #e6b980;
  height: 4px;
  cursor: pointer;
}

.audio-trimmer__controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.trim-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.trim-label {
  font-size: 0.72rem;
  color: #94a3b8;
}

.btn-stepper {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.btn-step {
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 0.72rem;
  padding: 4px 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-step:hover {
  background: rgba(255, 255, 255, 0.1);
}

.step-val {
  font-size: 0.76rem;
  color: #e6b980;
  padding: 0 6px;
  min-width: 42px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.btn-preview-play {
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #38bdf8;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-preview-play:hover {
  background: rgba(56, 189, 248, 0.25);
}

.btn-preview-play.is-playing {
  background: rgba(244, 63, 94, 0.2);
  border-color: rgba(244, 63, 94, 0.4);
  color: #fb7185;
}

.audio-trimmer__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.btn-cancel {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #94a3b8;
  font-size: 0.8rem;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #f1f5f9;
}

.btn-confirm {
  background: linear-gradient(135deg, #e6b980 0%, #eac775 100%);
  border: none;
  color: #1a1610;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  opacity: 0.92;
}

.btn-confirm:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
