<script setup lang="ts">
// App shell: router-view is the page. Global dialogs (auth/account/voice
// settings) are teleported to body, so they live here once and can be opened
// from any view via the Pinia stores.
// Session bootstrapping is handled by the router guard (auth.ensureReady()),
// which properly catches 401 errors when the user is not logged in.
import { RouterView } from "vue-router";
import AuthDialog from "./components/AuthDialog.vue";
import AccountDialog from "./components/AccountDialog.vue";
import VoiceSettingsDialog from "./components/VoiceSettingsDialog.vue";
</script>

<template>
  <RouterView />
  <AuthDialog />
  <AccountDialog />
  <VoiceSettingsDialog />
</template>
