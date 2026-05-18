<template>
  <div class="mx-auto flex h-full max-w-[999px] flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-semibold text-theme-text">Templates</h1>
        <p class="text-xs text-theme-text-muted mt-0.5">
          {{ templates.length }} template{{ templates.length !== 1 ? 's' : '' }}
          · Create notes in the <code class="bg-theme-background-elevated px-1 rounded">_templates</code> folder to use them here
        </p>
      </div>
      <button
        @click="loadTemplates"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm
               bg-theme-background-elevated hover:bg-theme-border transition-colors text-theme-text-muted"
        title="Refresh"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"
             :class="{ 'animate-spin': loading }">
          <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
        </svg>
        Refresh
      </button>
    </div>

    <!-- Confirm delete modal -->
    <ConfirmModal
      v-model="isDeleteModalVisible"
      title="Delete Template"
      :message="`Permanently delete template '${pendingDelete?.displayName}'? This cannot be undone.`"
      confirmButtonText="Delete"
      confirmButtonStyle="danger"
      @confirm="doDeleteTemplate"
    />

    <LoadingIndicator ref="loadingIndicator" class="flex-1">
      <!-- Empty state -->
      <div
        v-if="!loading && templates.length === 0"
        class="flex flex-col items-center justify-center py-16 text-theme-text-very-muted"
      >
        <svg viewBox="0 0 64 64" class="w-16 h-16 mb-3 opacity-40">
          <path fill="currentColor" d="M52 8h-12V6a2 2 0 0 0-2-2H26a2 2 0 0 0-2 2v2H12a2 2 0 0 0 0 4h2l2 44h32l2-44h2a2 2 0 0 0 0-4zm-24-2h8v2h-8V6zM46 52H18l-1.9-40h31.8L46 52z"/>
          <path fill="currentColor" d="M24 24h4v20h-4zm12 0h4v20h-4z"/>
        </svg>
        <p class="text-sm">No templates yet</p>
        <p class="text-xs mt-1 text-theme-text-very-muted">
          Create a note in the <code class="bg-theme-background-elevated px-1 rounded">_templates</code> folder to use it here
        </p>
      </div>

      <!-- Template items -->
      <div
        v-for="tpl in templates"
        :key="tpl.title"
        class="mb-2 rounded-xl border border-theme-border bg-theme-background-elevated px-4 py-3 flex items-start justify-between gap-3"
      >
        <div class="min-w-0 flex-1 cursor-pointer" @click="editTemplate(tpl.title)">
          <div class="flex items-center gap-2 mb-1">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-very-muted">
              <path d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M15,18V16H6V18H15M18,14V12H6V14H18Z"/>
            </svg>
            <p class="font-medium text-theme-text truncate hover:text-theme-brand transition-colors">
              {{ tpl.displayName }}
            </p>
          </div>
          <div class="flex items-center gap-3 text-xs text-theme-text-muted mt-1">
            <span class="flex items-center gap-1">
              <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current">
                <path d="M19,3H18V1H16V3H8V1H6V3H5A2,2 0 0,0 3,5V21A2,2 0 0,0 5,23H19A2,2 0 0,0 21,21V5A2,2 0 0,0 19,3M19,21H5V8H19V21Z"/>
              </svg>
              {{ tpl.lastModifiedAsString }}
            </span>
          </div>
        </div>
        <div class="flex gap-2 shrink-0">
          <!-- Edit button (opens note in edit mode with template content) -->
          <button
            @click="useTemplate(tpl.title)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated transition-colors"
            title="Edit template"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
            </svg>
            Edit
          </button>
          
          <!-- Delete button (RED) -->
          <button
            @click="promptDelete(tpl)"
            class="inline-flex items-center gap-1 px-3 py-1 rounded text-sm font-medium
                   text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors"
            title="Delete template"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
        <!--    Delete -->
          </button>
        </div>
      </div>
    </LoadingIndicator>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";
import { getNote, deleteNote, getTemplates } from "../api.js";
import ConfirmModal from "../components/ConfirmModal.vue";
import LoadingIndicator from "../components/LoadingIndicator.vue";
import { getToastOptions } from "../helpers.js";

const loadingIndicator = ref();
const loading = ref(false);
const templates = ref([]);
const toast = useToast();
const router = useRouter();

const isDeleteModalVisible = ref(false);
const pendingDelete = ref(null);

async function loadTemplates() {
  loading.value = true;
  try {
    const templateNames = await getTemplates();
    const templateDetails = [];
    for (const name of templateNames) {
      try {
        const note = await getNote(`_templates/${name}`);
        templateDetails.push({
          title: note.title,
          displayName: name,
          lastModifiedAsString: note.lastModifiedAsString,
          content: note.content,
        });
      } catch (error) {
        console.warn(`Failed to load template ${name}:`, error);
      }
    }
    // Sort by last modified descending (most recent first)
    templateDetails.sort((a, b) => {
      const dateA = new Date(a.lastModifiedAsString);
      const dateB = new Date(b.lastModifiedAsString);
      return dateB - dateA;
    });
    templates.value = templateDetails;
    loadingIndicator.value?.setLoaded();
  } catch (error) {
    console.error("Failed to load templates:", error);
    toast.add(getToastOptions("Failed to load templates.", "Error", "error"));
    loadingIndicator.value?.setFailed();
  } finally {
    loading.value = false;
  }
}

function useTemplate(templateTitle) {
  // Navigate to new note with template query parameter
  router.push({ 
    name: "new", 
    query: { template: templateTitle.replace("_templates/", "") } 
  });
}

function editTemplate(templateTitle) {
  // Navigate directly to the template note for editing
  router.push({ name: "note", params: { title: templateTitle } });
}

function promptDelete(template) {
  pendingDelete.value = template;
  isDeleteModalVisible.value = true;
}

async function doDeleteTemplate() {
  if (!pendingDelete.value) return;
  try {
    await deleteNote(pendingDelete.value.title);
    toast.add(getToastOptions(`Template '${pendingDelete.value.displayName}' deleted.`, "Deleted", "success"));
    await loadTemplates();
  } catch (error) {
    console.error("Failed to delete template:", error);
    toast.add(getToastOptions("Failed to delete template.", "Error", "error"));
  } finally {
    pendingDelete.value = null;
  }
}

onMounted(loadTemplates);
</script>