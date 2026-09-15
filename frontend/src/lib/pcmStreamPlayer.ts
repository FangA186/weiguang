import { pcm16MonoToWavBlob } from "./audioResponse";

export interface PCMStreamPlayerOptions {
  onStart?: () => void;
  onIdle?: () => void;
}

/** Schedule raw 24 kHz PCM chunks on one AudioContext timeline. */
export class PCMStreamPlayer {
  private context: AudioContext | null = null;
  private nextPlayTime = 0;
  private started = false;
  private finished = false;
  private stopped = false;
  private pcmChunks: Uint8Array[] = [];
  private sampleRate = 24000;
  private activeSources = new Set<AudioBufferSourceNode>();
  private idlePromise: Promise<void>;
  private resolveIdle!: () => void;

  constructor(private readonly options: PCMStreamPlayerOptions = {}) {
    this.idlePromise = new Promise<void>((resolve) => { this.resolveIdle = resolve; });
  }

  async enqueue(base64: string, sampleRate = 24000): Promise<void> {
    if (this.stopped || !base64) return;
    await this.ensureContext();
    if (this.stopped) return;
    const raw = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));
    if (raw.byteLength < 2) return;
    if (!this.pcmChunks.length) this.sampleRate = sampleRate;
    this.pcmChunks.push(raw);
    const samples = Math.floor(raw.byteLength / 2);
    const view = new DataView(raw.buffer);
    const buffer = this.context!.createBuffer(1, samples, sampleRate);
    const channel = buffer.getChannelData(0);
    for (let index = 0; index < samples; index += 1) {
      channel[index] = view.getInt16(index * 2, true) / 32768;
    }
    const source = this.context!.createBufferSource();
    source.buffer = buffer;
    source.connect(this.context!.destination);
    const lead = this.nextPlayTime > 0 ? 0.015 : 0.12;
    const startAt = Math.max(this.context!.currentTime + lead, this.nextPlayTime || 0);
    source.start(startAt);
    this.nextPlayTime = startAt + buffer.duration;
    this.activeSources.add(source);
    if (!this.started) {
      this.started = true;
      this.options.onStart?.();
    }
    source.onended = () => {
      this.activeSources.delete(source);
      this.checkIdle();
    };
  }

  finish(): void {
    this.finished = true;
    this.checkIdle();
  }

  waitForIdle(): Promise<void> {
    return this.idlePromise;
  }

  toWavBlob(): Blob | null {
    return this.stopped ? null : pcm16MonoToWavBlob(this.pcmChunks, this.sampleRate);
  }

  stop(): void {
    if (this.stopped) return;
    this.stopped = true;
    for (const source of this.activeSources) {
      try { source.stop(); } catch { /* already ended */ }
    }
    this.activeSources.clear();
    this.resolveIdle();
  }

  private async ensureContext(): Promise<void> {
    const Context = window.AudioContext || (window as any).webkitAudioContext;
    if (!Context) throw new Error("当前浏览器不支持 Web Audio");
    if (!this.context || this.context.state === "closed") {
      this.context = new Context({ latencyHint: "interactive" });
    }
    if (this.context.state === "suspended") await this.context.resume();
  }

  private checkIdle(): void {
    if (!this.finished || this.activeSources.size > 0 || this.stopped) return;
    const delay = Math.max(0, (this.nextPlayTime - (this.context?.currentTime || 0)) * 1000);
    window.setTimeout(() => {
      if (!this.stopped && this.finished && this.activeSources.size === 0) {
        this.options.onIdle?.();
        this.resolveIdle();
      }
    }, delay);
  }
}
