<script setup lang="ts">
import { ref, toRef } from "vue";
import { useOrb, type OrbState } from "../composables/useOrb";

const props = defineProps<{
  state: OrbState;
  particleCount?: number;
}>();

const canvas = ref<HTMLCanvasElement | null>(null);
useOrb(canvas, {
  particleCount: props.particleCount,
  state: toRef(props, "state"),
});
</script>

<template>
  <canvas ref="canvas" class="orb" aria-hidden="true"></canvas>
</template>
