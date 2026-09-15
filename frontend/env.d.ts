/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

// AudioWorklet processor globals (only present inside the worklet realm).
declare const sampleRate: number;
declare const AudioWorkletProcessor: {
  new (options?: AudioWorkletNodeOptions): {
    readonly port: MessagePort;
  };
};
declare function registerProcessor(
  name: string,
  processorCtor: { new (options?: AudioWorkletNodeOptions): AudioWorkletProcessor },
): void;

