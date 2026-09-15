// Voice and character settings use the browser compatibility API; cloned voice
// records are additionally loaded from the backend persistence store.
import { defineStore } from "pinia";
import { ref } from "vue";
import type { DeleteVoiceCloneResponse, VoiceCloneListResponse, VoiceCloneRecord, VoiceSettingsRecord } from "../types";
import * as api from "../api";

export type VoiceDialogMode = "clone" | "settings";

const DEFAULT_MANIFEST =
  "你是微光，一个明确标注为 AI 的温和陪伴角色。你认真倾听，简短自然地回应，不冒充或替代任何真实的人。";

export const useVoiceConfigStore = defineStore("voiceConfig", () => {
  const speaker = ref("");
  const characterManifest = ref(DEFAULT_MANIFEST);
  const voiceClone = ref<VoiceCloneRecord | null>(null);
  const voiceClones = ref<VoiceCloneRecord[]>([]);
  const dialogOpen = ref(false);
  const dialogMode = ref<VoiceDialogMode>("clone");
  const loadedUserID = ref("");
  let loadPromise: Promise<VoiceSettingsRecord> | null = null;

  function selectedClone(voiceId = speaker.value): VoiceCloneRecord | null {
    return voiceClones.value.find((clone) => clone.voice_id === voiceId) || null;
  }

  function applyRecord(record: VoiceSettingsRecord, clones?: VoiceCloneListResponse) {
    speaker.value = record.speaker || "";
    characterManifest.value = record.character_manifest || DEFAULT_MANIFEST;
    if (clones) voiceClones.value = clones.voice_clones;
    voiceClone.value = selectedClone() || (
      record.voice_clone?.voice_id === speaker.value ? record.voice_clone : null
    );
  }

  async function ensureReady(userID: string): Promise<VoiceSettingsRecord> {
    if (loadedUserID.value === userID && loadPromise) return loadPromise;
    if (loadedUserID.value === userID) {
      return {
        speaker: speaker.value,
        character_manifest: characterManifest.value,
        updated_at: "",
        voice_clone: voiceClone.value,
      };
    }
    loadedUserID.value = userID;
    loadPromise = Promise.all([api.fetchVoiceSettings(), api.fetchVoiceClones()])
      .then(([record, clones]) => {
        applyRecord(record, clones);
        return record;
      });
    try {
      const record = await loadPromise;
      return record;
    } catch (error) {
      loadedUserID.value = "";
      throw error;
    } finally {
      loadPromise = null;
    }
  }

  async function save(next: { speaker?: string; characterManifest?: string }) {
    const record = await api.saveVoiceSettings({
      speaker: next.speaker !== undefined ? next.speaker.trim() : speaker.value,
      character_manifest:
        next.characterManifest !== undefined
          ? next.characterManifest.trim() || DEFAULT_MANIFEST
          : characterManifest.value,
      voice_clone: voiceClone.value,
    });
    record.voice_clone = selectedClone(record.speaker);
    applyRecord(record);
    return record;
  }

  function addVoiceClone(record: VoiceCloneRecord) {
    voiceClones.value = [record, ...voiceClones.value.filter((clone) => clone.voice_id !== record.voice_id)];
  }

  function selectVoiceClone(voiceId: string) {
    const clone = voiceClones.value.find((candidate) => candidate.voice_id === voiceId);
    if (!clone) return null;
    speaker.value = clone.voice_id;
    voiceClone.value = clone;
    return clone;
  }

  async function deleteVoiceClone(voiceId: string): Promise<DeleteVoiceCloneResponse> {
    const result = await api.deleteVoiceClone(voiceId);
    voiceClones.value = result.voice_clones;
    speaker.value = result.speaker || "";
    voiceClone.value = selectedClone() || (
      result.voice_clone?.voice_id === speaker.value ? result.voice_clone : null
    );
    return result;
  }

  async function renameVoiceClone(voiceId: string, name: string): Promise<VoiceCloneRecord> {
    const renamed = await api.renameVoiceClone(voiceId, name);
    voiceClones.value = voiceClones.value.map((clone) => clone.voice_id === voiceId ? renamed : clone);
    if (voiceClone.value?.voice_id === voiceId) voiceClone.value = renamed;
    return renamed;
  }

  async function open(userID: string, mode: VoiceDialogMode = "clone") {
    await ensureReady(userID);
    dialogMode.value = mode;
    dialogOpen.value = true;
  }

  function close() {
    dialogOpen.value = false;
  }

  function reset() {
    speaker.value = "";
    characterManifest.value = DEFAULT_MANIFEST;
    voiceClone.value = null;
    voiceClones.value = [];
    dialogOpen.value = false;
    dialogMode.value = "clone";
    loadedUserID.value = "";
    loadPromise = null;
  }

  return {
    speaker,
    characterManifest,
    voiceClone,
    voiceClones,
    dialogOpen,
    dialogMode,
    ensureReady,
    save,
    addVoiceClone,
    selectVoiceClone,
    deleteVoiceClone,
    renameVoiceClone,
    open,
    close,
    reset,
  };
});
