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
    <SettingsCallouts    v-if="activeTab === 'callouts'" />
    <SettingsAppearance  v-if="activeTab === 'appearance'" />
    <SettingsAdvanced    v-if="activeTab === 'advanced'" />
    <SettingsTags        v-if="activeTab === 'tags'" />
    <SettingsTaskIcons   v-if="activeTab === 'taskicons'" />
    <SettingsPrefs       v-if="activeTab === 'prefs'" />
    <SettingsMaintenance v-if="activeTab === 'maintenance'" />

  </div>
</template>

<script setup>
import { ref } from "vue";
import SettingsCallouts    from "./SettingsCallouts.vue";
import SettingsAppearance  from "./SettingsAppearance.vue";
import SettingsAdvanced    from "./SettingsAdvanced.vue";
import SettingsTags        from "./SettingsTags.vue";
import SettingsTaskIcons   from "./SettingsTaskIcons.vue";
import SettingsPrefs       from "./SettingsPrefs.vue";
import SettingsMaintenance from "./SettingsMaintenance.vue";

const tabs = [
  { id: "callouts",    label: "Callouts" },
  { id: "appearance",  label: "Appearance" },
  { id: "advanced",    label: "Advanced" },
  { id: "tags",        label: "Tags" },
  { id: "taskicons",   label: "Task Icons" },
  { id: "prefs",       label: "Preferences" },
  { id: "maintenance", label: "Maintenance" },
];

const activeTab = ref("callouts");
</script>

<style scoped>
.scrollbar-none {
  scrollbar-width: none;
}
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
</style>
