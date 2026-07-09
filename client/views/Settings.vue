<template>
  <div class="flex h-full max-w-[999px] flex-col">

    <!-- Page header -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-theme-text">Settings</h1>
      <p class="text-sm text-theme-text-muted mt-1">Customise your Flatnotes experience.</p>
    </div>

    <!-- Tab bar — horizontally scrollable on mobile -->
    <div class="border-b border-theme-border mb-6">
      <div class="flex gap-1 overflow-x-auto scrollbar-none">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap touch-manipulation flex-shrink-0"
          :class="activeTab === tab.id
            ? 'border-theme-brand text-theme-brand'
            : 'border-transparent text-theme-text-muted hover:text-theme-text'"
        >{{ tab.label }}</button>
      </div>
    </div>

    <!-- Tab content -->
    <SettingsCallouts       v-if="activeTab === 'callouts'" />
    <SettingsAppearance     v-if="activeTab === 'appearance'" />
    <SettingsAdvanced       v-if="activeTab === 'advanced'" />
    <SettingsTags           v-if="activeTab === 'tags'" />
    <SettingsTaskIcons      v-if="activeTab === 'taskicons'" />
    <SettingsPrefs          v-if="activeTab === 'prefs'" @switchTab="(tab) => activeTab = tab" />
    <SettingsSavedSearches  v-if="activeTab === 'searches'" />
    <SettingsMaintenance    v-if="activeTab === 'maintenance'" />

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import SettingsCallouts      from "./SettingsCallouts.vue";
import SettingsAppearance    from "./SettingsAppearance.vue";
import SettingsAdvanced      from "./SettingsAdvanced.vue";
import SettingsTags          from "./SettingsTags.vue";
import SettingsTaskIcons     from "./SettingsTaskIcons.vue";
import SettingsPrefs         from "./SettingsPrefs.vue";
import SettingsSavedSearches from "./SettingsSavedSearches.vue";
import SettingsMaintenance   from "./SettingsMaintenance.vue";

const route = useRoute();

const tabs = [
  { id: "callouts",    label: "Callouts" },
  { id: "appearance",  label: "Appearance" },
  { id: "advanced",    label: "Advanced" },
  { id: "tags",        label: "Tags" },
  { id: "taskicons",   label: "Task Icons" },
  { id: "prefs",       label: "Preferences" },
  { id: "searches",    label: "Searches" },
  { id: "maintenance", label: "Maintenance" },
];

const VALID_TABS = new Set(tabs.map(t => t.id));

// Default to callouts; honour ?tab=xxx query param if valid
const activeTab = ref("callouts");

onMounted(() => {
  const requested = route.query.tab;
  if (requested && VALID_TABS.has(requested)) {
    activeTab.value = requested;
  }
});
</script>

<style scoped>
.scrollbar-none {
  scrollbar-width: none;
}
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
</style>
