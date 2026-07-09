<template>
  <!-- Mobile overlay -->
  <div
    v-if="isOpen"
    class="fixed inset-0 z-30 bg-black/40 md:hidden"
    @click="$emit('close')"
  ></div>

  <aside
    :class="[
      'fixed top-0 left-0 z-40 h-full w-72 flex flex-col',
      'bg-theme-background border-r border-theme-border',
      'transition-transform duration-300 ease-in-out',
      isOpen ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <!-- Header: title + buttons -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border shrink-0">
      <span class="text-xs font-bold uppercase text-theme-text-very-muted tracking-wider">Folders</span>
      <div class="flex items-center gap-1">
        <!-- Move/Copy button (only shows if selection mode is active) -->
        <button
          v-if="selectionMode"
          @click="openMoveModal"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          title="Move or copy selected notes"
          :disabled="selectedNotes.size === 0"
          :class="{ 'opacity-40 cursor-not-allowed': selectedNotes.size === 0 }"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M9.5,4L8.5,3H4A2,2 0 0,0 2,5V19A2,2 0 0,0 4,21H20A2,2 0 0,0 22,19V7A2,2 0 0,0 20,5H13.5L12.5,4H9.5M15,11V13H11V16L8,12L11,8V11H15Z"/>
          </svg>
        </button>
        <!-- Trash button (only shows if selection mode is active) -->
        <button
          v-if="selectionMode"
          @click="openDeleteModal"
          class="text-theme-text-muted hover:text-red-500 transition-colors p-1 rounded"
          title="Delete selected notes"
          :disabled="selectedNotes.size === 0"
          :class="{ 'opacity-40 cursor-not-allowed': selectedNotes.size === 0 }"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
          </svg>
        </button>
        <!-- Expand/Collapse all -->
        <button
          @click="toggleExpandAll"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :title="lastExpandDirection === true ? 'Collapse all' : 'Expand all'"
        >
          <svg v-if="lastExpandDirection !== true" viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M4,6H2V20A2,2 0 0,0 4,22H18V20H4V6M20,2H8A2,2 0 0,0 6,4V16A2,2 0 0,0 8,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H8V4H20V16M13,14L18,9L16.6,7.6L13,11.2L9.4,7.6L8,9L13,14Z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M4,6H2V20A2,2 0 0,0 4,22H18V20H4V6M20,2H8A2,2 0 0,0 6,4V16A2,2 0 0,0 8,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H8V4H20V16M8,11L13,6L18,11L16.6,12.4L13,8.8L9.4,12.4L8,11Z"/>
          </svg>
        </button>
        <!-- Refresh button -->
        <button
          @click="loadFolders"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :class="{ 'animate-spin': loading }"
          title="Refresh folders"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
        </button>
        <!-- Selection mode toggle -->
        <button
          @click="toggleSelectionMode"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          :class="{ 'text-theme-brand': selectionMode }"
          title="Select notes to move"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M19,5V7H5V5H19Z"/>
          </svg>
        </button>
        <!-- Close button -->
        <button
          @click="$emit('close')"
          class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
          title="Close sidebar"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Folder list -->
    <div class="flex-1 overflow-y-auto px-2 py-2">
      <div v-if="loading" class="text-xs text-theme-text-very-muted px-2 py-4 text-center">
        Loading folders...
      </div>
      <div v-else-if="folderTree.length === 0" class="text-xs text-theme-text-very-muted px-2 py-4 text-center">
        No folders found
      </div>
      <template v-else>
        <!-- All Notes shortcut -->
        <button
          @click="navigate(null)"
          class="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-sm transition-colors text-left mb-1"
          :class="activeFolder === null
            ? 'font-semibold text-theme-text bg-theme-background-elevated'
            : 'text-theme-text-muted hover:bg-theme-background-elevated'"
        >
          <div class="flex items-center gap-2 min-w-0">
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-60">
              <path d="M3,13H15V11H3M3,6V8H21V6M3,18H9V16H3V18Z"/>
            </svg>
            <span class="truncate">All Notes</span>
          </div>
          <span v-if="totalCount > 0" class="text-xs tabular-nums font-mono ml-2 text-theme-text-muted">
            {{ totalCount }}
          </span>
        </button>

        <div class="border-t border-theme-border my-1 mx-2"></div>

        <!-- Folder tree -->
        <FolderItem
          v-for="node in folderTree"
          :key="node.path"
          :node="node"
          :activeFolder="activeFolder"
          :activeNote="activeNote"
          :forceExpand="expandAll"
          :showCheckboxes="selectionMode"
          :selectedNotes="selectedNotes"
          @navigate="navigate"
          @openNote="openNote"
          @updateSelection="updateSelection"
          @dropNote="handleDropNote"
        />

        <!-- ── Saved Searches section ─────────────────────────────────────── -->
        <template v-if="globalStore.savedSearchesEnabled && globalStore.savedSearches.length > 0">
          <div class="border-t border-theme-border my-2 mx-2"></div>

          <!-- Section header -->
          <button
            @click="savedSearchesExpanded = !savedSearchesExpanded"
            class="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-sm
                   text-theme-text-muted hover:bg-theme-background-elevated transition-colors"
          >
            <div class="flex items-center gap-2 min-w-0">
              <!-- Folder with magnifying glass icon -->
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-60">
                <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4M15.5,11H17V13H15.5V14.5H13.5V13H12V11H13.5V9.5H15.5V11Z"/>
              </svg>
              <span class="text-xs font-bold uppercase tracking-wider text-theme-text-very-muted">
                Saved Searches
              </span>
            </div>
            <svg
              viewBox="0 0 24 24"
              class="w-3 h-3 fill-current shrink-0 transition-transform duration-150"
              :class="savedSearchesExpanded ? 'rotate-90' : ''"
            >
              <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
            </svg>
          </button>

          <!-- Saved search items -->
          <div v-show="savedSearchesExpanded" class="mt-0.5">
            <button
              v-for="search in globalStore.savedSearches"
              :key="search.id"
              @click="runSavedSearch(search)"
              class="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors text-left"
              :class="activeSavedSearchId === search.id
                ? 'bg-theme-brand/10 text-theme-brand font-medium'
                : 'text-theme-text-muted hover:bg-theme-background-elevated hover:text-theme-text'"
              :title="search.query"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current shrink-0 opacity-70">
                <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
              </svg>
              <span class="truncate text-sm">{{ search.name }}</span>
            </button>
          </div>
        </template>
      </template>
    </div>

    <!-- Move folder picker modal with search and new folder -->
    <Teleport to="body">
      <div
        v-if="showMoveDialog"
        class="fixed inset-0 z-50 flex items-start justify-start"
        @click.self="closeMoveDialog"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/20 backdrop-blur-sm" @click="closeMoveDialog"></div>
        
        <!-- Modal positioned near sidebar -->
        <div
          class="relative mt-2 ml-[calc(18rem+0.5rem)] w-80 move-folder-modal"
          :class="{
            'ml-[calc(18rem+0.5rem)]': isOpen,
            'ml-2': !isOpen
          }"
        >
          <div class="bg-theme-background rounded-lg shadow-xl border border-theme-border overflow-hidden">
            <!-- Header -->
            <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border bg-theme-background-elevated">
              <span class="text-sm font-semibold text-theme-text">
                {{ operationMode === 'duplicate' ? 'Duplicate to folder' : 'Move to folder' }}
              </span>
              <button
                @click="closeMoveDialog"
                class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded"
                title="Close"
              >
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
              </button>
            </div>

            <!-- Info text -->
            <div class="px-4 pt-3 pb-2">
              <div class="text-xs text-theme-text-muted">
                <span class="font-semibold text-theme-text">{{ selectedNotes.size }}</span>
                note{{ selectedNotes.size !== 1 ? 's' : '' }} selected
              </div>
            </div>

            <!-- Operation mode toggle -->
            <div class="px-4 pb-3">
              <div class="flex rounded-md border border-theme-border overflow-hidden text-xs font-medium">
                <button
                  @click="operationMode = 'move'"
                  :class="[
                    'flex-1 py-1.5 px-2 transition-colors text-center',
                    operationMode === 'move'
                      ? 'bg-theme-brand text-white'
                      : 'text-theme-text-muted hover:bg-theme-background-elevated'
                  ]"
                >
                  Move
                </button>
                <button
                  @click="operationMode = 'duplicate'"
                  :class="[
                    'flex-1 py-1.5 px-2 transition-colors text-center border-l border-theme-border',
                    operationMode === 'duplicate'
                      ? 'bg-theme-brand text-white'
                      : 'text-theme-text-muted hover:bg-theme-background-elevated'
                  ]"
                >
                  Duplicate
                </button>
              </div>
              <p class="text-xs text-theme-text-very-muted mt-1.5 leading-snug">
                <template v-if="operationMode === 'move'">Removes originals from their current folder.</template>
                <template v-else>Copies notes; originals stay in place.</template>
              </p>
            </div>

            <!-- Folder list with search -->
            <div class="px-3 pb-3">
              <!-- Search input -->
              <div class="mb-3">
                <div class="relative">
                  <svg class="absolute left-2 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-theme-text-very-muted" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
                  </svg>
                  <input
                    v-model="folderSearchQuery"
                    type="text"
                    placeholder="Search folders..."
                    class="w-full pl-7 pr-2 py-1.5 text-sm bg-theme-background border border-theme-border rounded-md focus:border-theme-brand outline-none text-theme-text placeholder-theme-text-very-muted"
                  />
                </div>
              </div>

              <!-- Create new folder row -->
              <div class="mb-2">
                <button
                  v-if="!showNewFolderInput"
                  @click="openNewFolderInput"
                  class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                         text-theme-brand hover:bg-theme-background-elevated flex items-center gap-2"
                >
                  <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                    <path d="M20,6A2,2 0 0,1 22,8V18A2,2 0 0,1 20,20H4C2.89,20 2,19.1 2,18V6C2,4.89 2.89,4 4,4H10L12,6H20M19,14H17V12H15V14H13V16H15V18H17V16H19V14Z"/>
                  </svg>
                  <span>Create new folder…</span>
                </button>

                <div v-else class="px-3 py-2 rounded-md border border-theme-brand/40 bg-theme-background-elevated">
                  <div class="text-xs text-theme-text-muted mb-1.5 font-medium">New folder name</div>
                  <div class="flex items-center gap-1.5">
                    <input
                      ref="newFolderInputEl"
                      v-model="newFolderName"
                      type="text"
                      placeholder="e.g. projects/notes"
                      class="flex-1 min-w-0 text-sm bg-theme-background border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted"
                      @keydown.enter.prevent="confirmNewFolder"
                      @keydown.escape.prevent="cancelNewFolder"
                    />
                    <button
                      @click="confirmNewFolder"
                      class="shrink-0 p-1 rounded text-theme-brand hover:bg-theme-brand/10 transition-colors"
                      title="Create and move here"
                    >
                      <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                        <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
                      </svg>
                    </button>
                    <button
                      @click="cancelNewFolder"
                      class="shrink-0 p-1 rounded text-theme-text-muted hover:bg-theme-background-elevated transition-colors"
                      title="Cancel"
                    >
                      <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current">
                        <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                      </svg>
                    </button>
                  </div>
                  <p v-if="newFolderError" class="text-xs text-red-500 mt-1">{{ newFolderError }}</p>
                  <p v-else class="text-xs text-theme-text-very-muted mt-1">
                    Use / for sub-folders. Press Enter to confirm.
                  </p>
                </div>
              </div>

              <!-- Divider -->
              <div v-if="filteredFolderPaths.length > 0" class="border-t border-theme-border my-1"></div>

              <!-- Filtered folder list -->
              <div class="max-h-48 overflow-y-auto">
                <button
                  v-for="folder in filteredFolderPaths"
                  :key="folder"
                  @click="applyNotesAction(folder)"
                  class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors hover:bg-theme-background-elevated text-theme-text"
                >
                  <div class="flex items-center gap-2">
                    <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0 opacity-60">
                      <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
                    </svg>
                    <span class="truncate">{{ folder || 'Root' }}</span>
                  </div>
                </button>
              </div>

              <!-- No results message -->
              <div v-if="filteredFolderPaths.length === 0 && folderSearchQuery" class="text-center py-4 text-xs text-theme-text-very-muted">
                No folders matching "{{ folderSearchQuery }}"
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Batch delete confirmation modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteDialog"
        class="fixed inset-0 z-50 flex items-start justify-start"
        @click.self="closeDeleteDialog"
      >
        <div class="fixed inset-0 bg-black/20 backdrop-blur-sm" @click="closeDeleteDialog"></div>
        <div
          class="relative mt-2 move-folder-modal w-80"
          :class="isOpen ? 'ml-[calc(18rem+0.5rem)]' : 'ml-2'"
        >
          <div class="bg-theme-background rounded-lg shadow-xl border border-theme-border overflow-hidden">
            <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border bg-theme-background-elevated">
              <div class="flex items-center gap-2">
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current text-red-500">
                  <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
                </svg>
                <span class="text-sm font-semibold text-theme-text">Delete notes</span>
              </div>
              <button @click="closeDeleteDialog" class="text-theme-text-muted hover:text-theme-text transition-colors p-1 rounded" title="Close">
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
              </button>
            </div>
            <div class="px-4 py-4">
              <div class="flex gap-3 mb-4">
                <div class="shrink-0 w-9 h-9 rounded-full bg-red-500/10 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-red-500">
                    <path d="M13,14H11V10H13M13,18H11V16H13M1,21H23L12,2L1,21Z"/>
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium text-theme-text">
                    Move <span class="text-red-500 font-semibold">{{ selectedNotes.size }}</span>
                    note{{ selectedNotes.size !== 1 ? 's' : '' }} to trash?
                  </p>
                  <p class="text-xs text-theme-text-muted mt-1 leading-relaxed">
                    Notes will be soft-deleted and can be restored from trash.
                  </p>
                </div>
              </div>
              <div class="bg-theme-background-elevated rounded-md px-3 py-2 mb-4 max-h-32 overflow-y-auto">
                <div v-for="title in deletePreviewList" :key="title" class="flex items-center gap-2 py-0.5">
                  <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current shrink-0 text-theme-text-very-muted">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                  </svg>
                  <span class="text-xs text-theme-text truncate">{{ title.split('/').pop() }}</span>
                </div>
                <div v-if="selectedNotes.size > 5" class="text-xs text-theme-text-very-muted pt-1 italic">
                  &hellip;and {{ selectedNotes.size - 5 }} more
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  @click="closeDeleteDialog"
                  class="flex-1 px-3 py-2 text-sm rounded-md border border-theme-border text-theme-text-muted hover:bg-theme-background-elevated transition-colors"
                >Cancel</button>
                <button
                  @click="confirmDeleteNotes"
                  :disabled="isDeleting"
                  class="flex-1 px-3 py-2 text-sm rounded-md font-medium transition-colors bg-red-500 hover:bg-red-600 text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
                >
                  <svg v-if="isDeleting" class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
                    <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
                  </svg>
                  {{ isDeleting ? 'Deleting…' : 'Move to trash' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";

import { getFolders, getFolderNotes, updateNote, getNote, createNote, deleteNote } from "../api.js";
import FolderItem from "./FolderItem.vue";
import { getToastOptions } from "../helpers.js";
import { useGlobalStore } from "../globalStore.js";
import { searchSortOptions } from "../constants.js";

const globalStore = useGlobalStore();

const props = defineProps({ isOpen: Boolean });
const emit = defineEmits(["close"]);

const router = useRouter();
const toast = useToast();

const folderCounts = ref({});
const loading      = ref(false);
const activeFolder = ref(null);
const activeNote   = ref(null);
const expandAll    = ref(null);
// Tracks which direction was last bulk-applied so the button icon/title
// stays correct after expandAll resets to null (the one-tick pulse approach).
const lastExpandDirection = ref(null);

// Selection state
const selectionMode = ref(false);
const selectedNotes = ref(new Set());

// ── Saved searches sidebar state ──────────────────────────────────────────────
// Expand/collapse state persisted in localStorage
const savedSearchesExpanded = ref(
  localStorage.getItem("fn_saved_searches_expanded") !== "false"
);
watch(savedSearchesExpanded, (val) => {
  localStorage.setItem("fn_saved_searches_expanded", String(val));
});

// Track which saved search is currently active (matched by query + sortBy)
const activeSavedSearchId = computed(() => {
  const currentTerm   = router.currentRoute.value.query.term;
  const currentSortBy = router.currentRoute.value.query.sortBy;
  if (!currentTerm) return null;

  const SORT_MAP = {
    lastModified: searchSortOptions.lastModified,
    title:        searchSortOptions.title,
    titleDesc:    searchSortOptions.titleDesc,
    score:        searchSortOptions.score,
  };

  for (const s of globalStore.savedSearches) {
    if (s.query !== currentTerm) continue;
    // If the saved search has a sort preference, check it matches
    if (s.sort_by) {
      const expectedNumeric = SORT_MAP[s.sort_by];
      if (expectedNumeric !== undefined && String(currentSortBy) !== String(expectedNumeric)) continue;
    }
    return s.id;
  }
  return null;
});

function runSavedSearch(search) {
  const SORT_MAP = {
    lastModified: searchSortOptions.lastModified,
    title:        searchSortOptions.title,
    titleDesc:    searchSortOptions.titleDesc,
    score:        searchSortOptions.score,
  };
  const q = { term: search.query };
  if (search.sort_by && SORT_MAP[search.sort_by] !== undefined) {
    q.sortBy = SORT_MAP[search.sort_by];
  }
  router.push({ name: "search", query: q });
  // Auto-close sidebar on mobile
  if (window.innerWidth < 768) {
    emit("close");
  }
}

const showMoveDialog  = ref(false);
const operationMode   = ref("move"); // 'move' | 'duplicate'

// Delete dialog state
const showDeleteDialog = ref(false);
const isDeleting       = ref(false);

// ── New-folder-in-dialog state ────────────────────────────────────────────
const showNewFolderInput = ref(false);
const newFolderName      = ref("");
const newFolderError     = ref("");
const newFolderInputEl   = ref(null);

// ── Folder search state ────────────────────────────────────────────────────
const folderSearchQuery = ref("");

const totalCount = computed(() => {
  let total = 0;
  const paths = Object.keys(folderCounts.value);
  for (const p of paths) {
    const hasChildren = paths.some((q) => q !== p && q.startsWith(p + "/"));
    if (!hasChildren) {
      total += folderCounts.value[p] || 0;
    }
  }
  return total;
});

// List of all folder paths (including empty string for root)
const allFolderPaths = computed(() => {
  const paths = Object.keys(folderCounts.value).sort();
  return ['', ...paths]; // empty string = root
});

// Filtered folder paths based on search query
const filteredFolderPaths = computed(() => {
  if (!folderSearchQuery.value.trim()) {
    return allFolderPaths.value;
  }
  const query = folderSearchQuery.value.toLowerCase().trim();
  return allFolderPaths.value.filter(folder => 
    folder.toLowerCase().includes(query)
  );
});

const deletePreviewList = computed(() => Array.from(selectedNotes.value).slice(0, 5));

const folderTree = computed(() => {
  const root = [];
  const map  = {};
  const sorted = Object.keys(folderCounts.value).sort();

  for (const path of sorted) {
    const parts = path.split("/");
    let accumulated = "";
    for (let i = 0; i < parts.length; i++) {
      const parent = accumulated;
      accumulated = accumulated ? `${accumulated}/${parts[i]}` : parts[i];
      if (!map[accumulated]) {
        const node = {
          name:     parts[i],
          path:     accumulated,
          count:    folderCounts.value[accumulated] || 0,
          children: [],
        };
        map[accumulated] = node;
        if (i === 0)           root.push(node);
        else if (map[parent])  map[parent].children.push(node);
      }
    }
  }
  return root;
});

async function loadFolders() {
  loading.value = true;
  try {
    const data = await getFolders();
    if (data && typeof data === "object" && !Array.isArray(data)) {
      folderCounts.value = { ...data };
    } else if (Array.isArray(data)) {
      const d = {};
      data.forEach((p) => { d[p] = 0; });
      folderCounts.value = d;
    } else {
      folderCounts.value = {};
    }
  } catch {
    folderCounts.value = {};
  } finally {
    loading.value = false;
  }
}

function toggleExpandAll() {
  // Set expandAll for exactly one tick (pulse). Because all FolderItem children
  // are mounted via v-show (not v-if), every watcher at every depth fires in
  // the same tick and syncs localExpanded. nextTick then resets expandAll to
  // null so individual chevron clicks work freely at any depth afterwards.
  if (lastExpandDirection.value !== true) {
    expandAll.value = true;
    lastExpandDirection.value = true;
  } else {
    expandAll.value = false;
    lastExpandDirection.value = false;
  }
  nextTick(() => {
    expandAll.value = null;
  });
}

function toggleSelectionMode() {
  selectionMode.value = !selectionMode.value;
  if (!selectionMode.value) {
    selectedNotes.value.clear();
  }
}

function updateSelection({ noteTitle, checked }) {
  if (checked) {
    selectedNotes.value.add(noteTitle);
  } else {
    selectedNotes.value.delete(noteTitle);
  }
}

function openMoveModal() {
  if (selectedNotes.value.size === 0) {
    toast.add(getToastOptions("No notes selected", "Info", "info"));
    return;
  }
  folderSearchQuery.value = "";
  operationMode.value     = "move";
  showMoveDialog.value    = true;
}

function closeMoveDialog() {
  showMoveDialog.value = false;
  cancelNewFolder();
  folderSearchQuery.value = ""; // Reset search on close
}

// ── New-folder helpers ────────────────────────────────────────────────────

function openNewFolderInput() {
  showNewFolderInput.value = true;
  newFolderName.value      = "";
  newFolderError.value     = "";
  nextTick(() => {
    newFolderInputEl.value?.focus();
  });
}

function cancelNewFolder() {
  showNewFolderInput.value = false;
  newFolderName.value      = "";
  newFolderError.value     = "";
}

function validateFolderName(name) {
  if (!name || !name.trim()) {
    return "Folder name cannot be empty.";
  }
  const trimmed = name.trim();
  if (trimmed.startsWith("/") || trimmed.endsWith("/")) {
    return "Folder name cannot start or end with a slash.";
  }
  if (trimmed.includes("//")) {
    return "Folder name cannot contain consecutive slashes.";
  }
  if (/[\:*?"<>|]/.test(trimmed)) {
    return "Folder name contains invalid characters.";
  }
  if (trimmed.split("/").some((part) => part === ".." || part === ".")) {
    return "Folder name cannot contain '.' or '..'.";
  }
  return null;
}

async function confirmNewFolder() {
  const trimmed = newFolderName.value.trim();
  const error   = validateFolderName(trimmed);
  if (error) {
    newFolderError.value = error;
    return;
  }
  newFolderError.value = "";
  await applyNotesAction(trimmed);
  cancelNewFolder();
}

// ── Dispatcher: routes to move or duplicate based on operationMode ────────
async function applyNotesAction(targetFolder) {
  if (operationMode.value === "duplicate") {
    await duplicateNotesTo(targetFolder);
  } else {
    await moveNotesTo(targetFolder);
  }
}

async function moveNotesTo(targetFolder) {
  showMoveDialog.value = false;
  const notesToMove = Array.from(selectedNotes.value);
  let successCount = 0;
  let failCount = 0;

  for (const oldTitle of notesToMove) {
    const parts = oldTitle.split("/");
    const basename = parts.pop();
    const newTitle = targetFolder ? `${targetFolder}/${basename}` : basename;

    try {
      await updateNote(oldTitle, newTitle, undefined);
      successCount++;
    } catch (error) {
      if (error.response?.status === 409) {
        toast.add(getToastOptions(`Note "${basename}" already exists in destination. Skipping.`, "Conflict", "warn"));
      } else if (error.response?.status === 404) {
        successCount++;
      } else {
        console.error(`Failed to move ${oldTitle}:`, error);
        failCount++;
      }
    }
  }

  if (successCount > 0) {
    toast.add(getToastOptions(`Moved ${successCount} note(s)`, "Success", "success"));
    selectedNotes.value.clear();
    selectionMode.value = false;
    await loadFolders();
  }
  if (failCount > 0) {
    toast.add(getToastOptions(`Failed to move ${failCount} note(s)`, "Error", "error"));
  }
}

async function duplicateNotesTo(targetFolder) {
  showMoveDialog.value = false;
  const notesToDup = Array.from(selectedNotes.value);
  let successCount = 0;
  let failCount    = 0;

  const prefix = targetFolder ? `${targetFolder}/` : "";

  // Strip any existing " (copy)" / " (copy N)" tail so duplicating a copy
  // always counts up from the root name, never chains suffixes.
  const copyPattern = / \(copy(?:\s+\d+)?\)$/;
  const rootName = (title) => title.split("/").pop().replace(copyPattern, "");

  // Seed existingTitles from what is ACTUALLY on disk in the destination folder.
  // Without this, a second duplication run has no knowledge of copies created
  // in a previous run and collides with a 409.
  const existingTitles = new Set();
  try {
    const folderNotes = targetFolder
      ? await getFolderNotes(targetFolder)
      : await getFolderNotes(""); // root
    for (const note of folderNotes) {
      // API returns objects with a title property, e.g. { title: "Draft/Report (copy)", ... }
      const bare = typeof note === "string" ? note : (note.title ?? note.filename ?? "");
      if (bare) existingTitles.add(bare);
    }
  } catch {
    // If the folder fetch fails (empty/new folder), continue with an empty set.
  }

  // Also seed the plain root name of every note being duplicated so each one
  // always lands on at least " (copy)" — never overwrites the original.
  for (const oldTitle of notesToDup) {
    existingTitles.add(prefix + rootName(oldTitle));
  }

  for (const oldTitle of notesToDup) {
    const base = rootName(oldTitle);

    // Start at " (copy)" and increment until we find an unclaimed slot.
    let suffix   = 1;
    let newTitle = prefix + `${base} (copy)`;

    while (existingTitles.has(newTitle)) {
      suffix++;
      newTitle = prefix + `${base} (copy ${suffix})`;
    }

    // Reserve slot before the async call so the next iteration sees it.
    existingTitles.add(newTitle);

    try {
      const sourceNote = await getNote(oldTitle);
      await createNote(newTitle, sourceNote.content);
      successCount++;
    } catch (error) {
      existingTitles.delete(newTitle); // release reservation on failure
      console.error(`Failed to duplicate ${oldTitle}:`, error);
      failCount++;
    }
  }

  if (successCount > 0) {
    const dest = targetFolder || "Root";
    toast.add(getToastOptions(`Duplicated ${successCount} note(s) to "${dest}"`, "Success", "success"));
    selectedNotes.value.clear();
    selectionMode.value = false;
    await loadFolders();
  }
  if (failCount > 0) {
    toast.add(getToastOptions(`Failed to duplicate ${failCount} note(s)`, "Error", "error"));
  }
}

// Batch delete
function openDeleteModal() {
  if (selectedNotes.value.size === 0) {
    toast.add(getToastOptions("No notes selected", "Info", "info"));
    return;
  }
  showDeleteDialog.value = true;
}

function closeDeleteDialog() {
  if (isDeleting.value) return;
  showDeleteDialog.value = false;
}

async function confirmDeleteNotes() {
  isDeleting.value = true;
  const notesToDelete = Array.from(selectedNotes.value);
  let successCount = 0;
  let failCount    = 0;

  for (const title of notesToDelete) {
    try {
      await deleteNote(title);
      successCount++;
    } catch (error) {
      console.error("Failed to delete " + title + ":", error);
      failCount++;
    }
  }

  isDeleting.value       = false;
  showDeleteDialog.value = false;

  if (successCount > 0) {
    const label = successCount === 1 ? "note" : "notes";
    toast.add(getToastOptions("Moved " + successCount + " " + label + " to trash", "Deleted", "success"));
    selectedNotes.value.clear();
    selectionMode.value = false;
    await loadFolders();
  }
  if (failCount > 0) {
    toast.add(getToastOptions("Failed to delete " + failCount + " note(s)", "Error", "error"));
  }
}

async function handleDropNote({ noteTitle, targetFolder }) {
  const parts = noteTitle.split("/");
  const basename = parts.pop();
  const newTitle = targetFolder ? `${targetFolder}/${basename}` : basename;

  try {
    // Use undefined for newContent to omit it from the JSON body
    await updateNote(noteTitle, newTitle, undefined);
    toast.add(getToastOptions(`Moved "${basename}"`, "Success", "success"));
    await loadFolders();
  } catch (error) {
    if (error.response?.status === 409) {
      toast.add(getToastOptions(`Note "${basename}" already exists in destination folder.`, "Conflict", "warn"));
    } else if (error.response?.status === 404) {
      // Note was already moved — treat as success
      toast.add(getToastOptions(`Moved "${basename}"`, "Success", "success"));
      await loadFolders();
    } else {
      toast.add(getToastOptions(`Failed to move "${basename}"`, "Error", "error"));
      console.error(`Failed to move ${noteTitle}:`, error);
    }
  }
}

function navigate(folderPath) {
  activeFolder.value = folderPath;
  activeNote.value   = null;

  // Resolve sort using the same fallback chain as SearchResults/NavBar:
  // user preference → Docker env → omit (SearchResults effectiveSortBy handles it)
  const _sortMap = {
    lastModified: searchSortOptions.lastModified,
    title:        searchSortOptions.title,
    titleDesc:    searchSortOptions.titleDesc,
    score:        searchSortOptions.score,
  };
  const userPref = globalStore.notesDefaultSort;
  const envSort  = globalStore.config?.quickAccessSort;
  const resolvedSort = _sortMap[userPref] ?? _sortMap[envSort];
  // Only include sortBy in the query when a preference is resolved;
  // omitting it lets SearchResults fall through to its own effectiveSortBy default.
  const sortQuery = resolvedSort !== undefined ? { sortBy: resolvedSort } : {};

  if (!folderPath) {
    router.push({ name: "search", query: { term: "*", ...sortQuery } });
  } else {
    router.push({ name: "search", query: { term: "*", folder: folderPath, ...sortQuery } });
  }
  if (selectionMode.value) toggleSelectionMode();
  // Auto-close sidebar on mobile (below md breakpoint = 768px)
  if (window.innerWidth < 768) {
    emit("close");
  }
}

function openNote(noteTitle) {
  activeNote.value   = noteTitle;
  activeFolder.value = null;
  router.push({ name: "note", params: { title: noteTitle } });
  if (selectionMode.value) toggleSelectionMode();
  // Auto-close sidebar on mobile (below md breakpoint = 768px)
  if (window.innerWidth < 768) {
    emit("close");
  }
}

watch(() => props.isOpen, (open) => {
  if (open) loadFolders();
});

watch(
  () => router.currentRoute.value.query.folder,
  (f) => {
    activeFolder.value = f || null;
    if (f) activeNote.value = null;
  },
  { immediate: true }
);

watch(
  () => router.currentRoute.value.params.title,
  (t) => {
    if (t) {
      activeNote.value   = t;
      activeFolder.value = null;
    }
  },
  { immediate: true }
);

onMounted(() => {
  if (props.isOpen) loadFolders();
});
</script>

<style scoped>
.move-folder-modal {
  animation: modalFadeIn 0.15s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>