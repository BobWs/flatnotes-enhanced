<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="cancel"
    >
      <div
        class="bg-theme-background rounded-t-2xl sm:rounded-xl border border-theme-border shadow-xl
               w-full sm:w-[440px] sm:max-w-full"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border">
          <div class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-brand shrink-0">
              <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
            </svg>
            <h3 class="text-base font-semibold text-theme-text">
              {{ isEditing ? 'Edit Saved Search' : 'New Saved Search' }}
            </h3>
          </div>
          <button
            @click="cancel"
            class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded touch-manipulation"
            title="Close"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="px-4 py-4 space-y-4">

          <!-- Name -->
          <div>
            <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">
              Name <span class="text-theme-brand">*</span>
            </label>
            <input
              ref="nameInputEl"
              v-model="form.name"
              type="text"
              placeholder="e.g. Work Notes"
              maxlength="80"
              class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg
                     px-3 py-2 outline-none focus:border-theme-brand text-theme-text
                     placeholder:text-theme-text-very-muted transition-colors"
              @keydown.enter.prevent="save"
              @keydown.esc.prevent="cancel"
            />
            <p v-if="errors.name" class="text-xs text-red-500 mt-1">{{ errors.name }}</p>
          </div>

          <!-- Query -->
          <div>
            <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">
              Search query <span class="text-theme-brand">*</span>
            </label>
            <input
              v-model="form.query"
              type="text"
              placeholder="e.g. tags:work or project proposal"
              maxlength="500"
              class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg
                     px-3 py-2 outline-none focus:border-theme-brand text-theme-text
                     placeholder:text-theme-text-very-muted font-mono transition-colors"
              @keydown.enter.prevent="save"
              @keydown.esc.prevent="cancel"
            />
            <p v-if="errors.query" class="text-xs text-red-500 mt-1">{{ errors.query }}</p>
            <p class="text-xs text-theme-text-very-muted mt-1">
              Any search term works: plain text, <code class="bg-theme-background-elevated px-1 rounded">tags:work</code>,
              <code class="bg-theme-background-elevated px-1 rounded">"exact phrase"</code>, or combinations.
            </p>
          </div>

          <!-- Sort by -->
          <div>
            <label class="block text-xs font-medium text-theme-text-muted mb-1.5 uppercase tracking-wide">
              Default sort
            </label>
            <select
              v-model="form.sortBy"
              class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded-lg
                     px-3 py-2 outline-none focus:border-theme-brand text-theme-text transition-colors"
            >
              <option value="">App default</option>
              <option value="score">Relevance</option>
              <option value="title">Title A–Z</option>
              <option value="titleDesc">Title Z–A</option>
              <option value="lastModified">Last modified</option>
            </select>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-2 px-4 py-3 border-t border-theme-border">
          <button
            @click="cancel"
            class="px-4 py-2 rounded-lg text-sm text-theme-text-muted border border-theme-border
                   hover:bg-theme-background-elevated active:bg-theme-background-elevated
                   transition-colors touch-manipulation"
          >Cancel</button>
          <button
            @click="save"
            class="px-4 py-2 rounded-lg text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
                   text-white transition-colors touch-manipulation"
          >{{ isEditing ? 'Save changes' : 'Save search' }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";

const props = defineProps({
  show: { type: Boolean, default: false },
  // Pass null to create, or a search object to edit
  search: { type: Object, default: null },
});

const emit = defineEmits(["save", "close"]);

const nameInputEl = ref(null);

const form = ref({ name: "", query: "", sortBy: "" });
const errors = ref({});

const isEditing = computed(() => props.search !== null);

// Populate form when modal opens or search prop changes
watch(() => props.show, (val) => {
  if (val) {
    if (props.search) {
      form.value = {
        name:   props.search.name   || "",
        query:  props.search.query  || "",
        sortBy: props.search.sort_by || "",
      };
    } else {
      form.value = { name: "", query: "", sortBy: "" };
    }
    errors.value = {};
    nextTick(() => { nameInputEl.value?.focus(); });
  }
});

function validate() {
  const e = {};
  if (!form.value.name.trim()) e.name = "Name is required.";
  if (!form.value.query.trim()) e.query = "Search query is required.";
  errors.value = e;
  return Object.keys(e).length === 0;
}

function save() {
  if (!validate()) return;
  emit("save", {
    name:    form.value.name.trim(),
    query:   form.value.query.trim(),
    sort_by: form.value.sortBy || null,
  });
}

function cancel() {
  errors.value = {};
  emit("close");
}
</script>
