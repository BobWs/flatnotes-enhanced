<template>
  <div class="space-y-6">

    <!-- Error state -->
    <div
      v-if="loadError"
      class="flex items-center justify-between p-4 rounded-lg border border-red-400/40 bg-red-500/5"
    >
      <div class="flex items-center gap-2 text-sm text-red-500">
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current shrink-0">
          <path d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/>
        </svg>
        Could not load maintenance data.
      </div>
      <button
        @click="loadStatus"
        class="text-xs px-2 py-1 rounded border border-red-400/40 text-red-500 hover:bg-red-500/10 transition-colors touch-manipulation"
      >Retry</button>
    </div>

    <!-- Two-column row -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">

      <!-- LEFT: Trash Manager -->
      <div class="p-4 rounded-lg border border-theme-border bg-theme-background space-y-4">
        <div class="flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-muted shrink-0">
            <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
          </svg>
          <h3 class="text-sm font-semibold text-theme-text">Trash Manager</h3>
        </div>

        <template v-if="loading">
          <div class="space-y-2">
            <div v-for="n in 4" :key="n" class="h-4 rounded bg-theme-background-elevated animate-pulse"></div>
          </div>
        </template>
        <template v-else-if="status">
          <div class="flex items-start gap-3">
            <span class="text-xs text-theme-text-muted w-24 shrink-0 pt-0.5">Auto-delete</span>
            <span
              class="text-xs font-medium px-2 py-0.5 rounded-full"
              :class="status.trash_auto_delete_days
                ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                : 'bg-theme-background-elevated text-theme-text-muted'"
            >
              {{ status.trash_auto_delete_days ? `Every ${status.trash_auto_delete_days} days` : 'Manual only' }}
            </span>
          </div>

          <div class="flex items-center gap-3">
            <span class="text-xs text-theme-text-muted w-24 shrink-0">In trash</span>
            <span class="text-sm font-medium text-theme-text">{{ status.trash_count }} note{{ status.trash_count !== 1 ? 's' : '' }}</span>
          </div>

          <div class="flex items-center gap-3">
            <span class="text-xs text-theme-text-muted w-24 shrink-0">Last cleaned</span>
            <span class="text-sm text-theme-text">{{ lastCleanupDisplay }}</span>
          </div>

          <p class="text-xs text-theme-text-very-muted leading-relaxed">
            Configure auto-delete via the
            <code class="bg-theme-background-elevated px-1 rounded">FLATNOTES_TRASH_DAYS</code>
            environment variable.
          </p>
        </template>

        <div class="pt-2 border-t border-theme-border">
          <template v-if="showConfirm">
            <div class="space-y-3">
              <p class="text-xs text-theme-text-muted leading-relaxed">
                Delete notes older than X days (0 = delete all):
              </p>
              <div class="flex items-center gap-2">
                <input
                  v-model.number="emptyDays"
                  type="number"
                  min="0"
                  max="365"
                  class="w-20 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1.5
                         outline-none focus:border-theme-brand text-theme-text"
                />
                <span class="text-xs text-theme-text-muted">days</span>
              </div>
              <div class="flex items-center gap-2">
                <button
                  @click="doEmptyTrash"
                  :disabled="emptyingTrash"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium
                         text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors
                         disabled:opacity-50 touch-manipulation"
                >
                  <svg v-if="emptyingTrash" viewBox="0 0 24 24" class="w-4 h-4 fill-current animate-spin">
                    <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
                  </svg>
                  {{ emptyingTrash ? 'Emptying…' : 'Confirm' }}
                </button>
                <button
                  @click="showConfirm = false"
                  :disabled="emptyingTrash"
                  class="px-3 py-1.5 rounded text-sm text-theme-text-muted border border-theme-border
                         hover:bg-theme-background-elevated transition-colors disabled:opacity-50 touch-manipulation"
                >Cancel</button>
              </div>
              <p v-if="emptyMsg" class="text-sm" :class="emptyOk ? 'text-green-500' : 'text-red-500'">
                {{ emptyMsg }}
              </p>
            </div>
          </template>
          <template v-else>
            <div class="flex items-center gap-3">
              <button
                @click="openConfirm"
                :disabled="loading || !status || status.trash_count === 0"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium
                       text-red-500 border border-red-400/40 hover:bg-red-500/10 transition-colors
                       disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation"
                title="Permanently delete notes in trash"
              >
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0">
                  <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
                Empty trash now
              </button>
              <p v-if="emptyMsg && !showConfirm" class="text-sm" :class="emptyOk ? 'text-green-500' : 'text-red-500'">
                {{ emptyMsg }}
              </p>
            </div>
          </template>
        </div>
      </div>

      <!-- RIGHT: Quick stats card -->
      <div class="p-4 rounded-lg border border-theme-border bg-theme-background space-y-4">
        <div class="flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-muted shrink-0">
            <path d="M3,13H15V11H3M3,6V8H21V6M3,18H9V16H3V18Z"/>
          </svg>
          <h3 class="text-sm font-semibold text-theme-text">Content Summary</h3>
        </div>

        <template v-if="loading">
          <div class="space-y-2">
            <div v-for="n in 5" :key="n" class="h-4 rounded bg-theme-background-elevated animate-pulse"></div>
          </div>
        </template>
        <template v-else-if="status">
          <dl class="space-y-3">
            <div class="flex items-center justify-between">
              <dt class="text-xs text-theme-text-muted flex items-center gap-1.5">
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/></svg>
                Notes
              </dt>
              <dd class="text-sm font-semibold text-theme-text">{{ status.note_count.toLocaleString() }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="text-xs text-theme-text-muted flex items-center gap-1.5">
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0"><path d="M3,3H21V7H3V3M4,8H20V21H4V8M9,11V13H15V11H9Z"/></svg>
                Archive
              </dt>
              <dd class="text-sm font-semibold text-theme-text">{{ status.archive_count.toLocaleString() }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="text-xs text-theme-text-muted flex items-center gap-1.5">
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0"><path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/></svg>
                Trash
              </dt>
              <dd class="text-sm font-semibold text-theme-text">{{ status.trash_count.toLocaleString() }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="text-xs text-theme-text-muted flex items-center gap-1.5">
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current shrink-0"><path d="M16.5,6V17.5A4,4 0 0,1 12.5,21.5A4,4 0 0,1 8.5,17.5V5A2.5,2.5 0 0,1 11,2.5A2.5,2.5 0 0,1 13.5,5V15.5A1,1 0 0,1 12.5,16.5A1,1 0 0,1 11.5,15.5V6H10V15.5A2.5,2.5 0 0,0 12.5,18A2.5,2.5 0 0,0 15,15.5V5A4,4 0 0,0 11,1A4,4 0 0,0 7,5V17.5A5.5,5.5 0 0,0 12.5,23A5.5,5.5 0 0,0 18,17.5V6H16.5Z"/></svg>
                Attachments
              </dt>
              <dd class="text-sm font-semibold text-theme-text">{{ status.attachment_count.toLocaleString() }}</dd>
            </div>
          </dl>
        </template>
      </div>
    </div>

    <!-- Full-width: About & System Info -->
    <div class="p-4 rounded-lg border border-theme-border bg-theme-background">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-muted shrink-0">
            <path d="M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z"/>
          </svg>
          <h3 class="text-sm font-semibold text-theme-text">About & System Info</h3>
        </div>
        <button
          @click="loadStatus"
          :disabled="loading"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs
                 bg-theme-background-elevated hover:bg-theme-border border border-theme-border
                 transition-colors text-theme-text-muted touch-manipulation"
          title="Refresh"
        >
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current" :class="{ 'animate-spin': loading }">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
          Refresh
        </button>
      </div>

      <template v-if="loading">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div v-for="n in 3" :key="n" class="h-14 rounded bg-theme-background-elevated animate-pulse"></div>
        </div>
      </template>
      <template v-else-if="status">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="p-3 rounded-lg bg-theme-background-elevated">
            <p class="text-xs text-theme-text-muted mb-1">App version</p>
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-sm font-semibold text-theme-text">v{{ status.version }}</span>
              <!-- State 1: never checked / offline -->
              <span
                v-if="status.latest_version == null"
                class="text-xs px-1.5 py-0.5 rounded-full bg-theme-border text-theme-text-muted font-medium"
              >Offline</span>
              <!-- State 2: up to date -->
              <span
                v-else-if="!status.update_available"
                class="text-xs px-1.5 py-0.5 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 font-medium"
              >Up to date</span>
              <!-- State 3: update available -->
              <span
                v-else
                class="text-xs px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400 font-medium"
              >Update available</span>
            </div>
            <!-- Update available detail -->
            <div v-if="status.update_available" class="mt-1.5 space-y-1">
              <p class="text-xs text-theme-text-muted">
                v{{ status.latest_version }} available
              </p>
              <a
                v-if="status.release_url"
                :href="status.release_url"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center gap-1 text-xs text-theme-brand hover:underline"
              >
                View release notes
                <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current shrink-0"><path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"/></svg>
              </a>
            </div>
            <!-- Last checked (when up to date) -->
            <p
              v-else-if="status.latest_version != null && status.update_checked_at"
              class="text-xs text-theme-text-very-muted mt-1"
            >Checked {{ formatRelativeTime(status.update_checked_at) }}
              <span v-if="status.update_check_source" class="opacity-60">
                via {{ status.update_check_source === 'dockerhub' ? 'Docker Hub' : 'GitHub' }}
              </span>
            </p>
          </div>

          <div class="p-3 rounded-lg bg-theme-background-elevated">
            <p class="text-xs text-theme-text-muted mb-1">Database</p>
            <p class="text-sm font-semibold text-theme-text">{{ status.db_size_human }}</p>
            <p
              v-if="status.db_path"
              class="text-xs text-theme-text-very-muted truncate mt-0.5"
              :title="status.db_path"
            >{{ status.db_path }}</p>
            <p v-else class="text-xs text-theme-text-very-muted mt-0.5">Not configured</p>
          </div>

          <div class="p-3 rounded-lg bg-theme-background-elevated">
            <p class="text-xs text-theme-text-muted mb-1">Project</p>
            <p class="text-sm font-semibold text-theme-text">Flatnotes Enhanced</p>
            <p class="text-xs text-theme-text-very-muted mt-0.5">Built with ❤️ for better note-taking, by Bob W.</p>
          </div>
        </div>
      </template>
    </div>

    <!-- Full-width: Preferences Backup & Restore -->
    <div class="p-4 rounded-lg border border-theme-border bg-theme-background">

      <!-- Header row -->
      <div class="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div class="flex items-start gap-2 min-w-0">
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-theme-text-muted shrink-0 mt-0.5">
            <path d="M12,3C7.58,3 4,4.79 4,7C4,9.21 7.58,11 12,11C16.42,11 20,9.21 20,7C20,4.79 16.42,3 12,3M4,9V12C4,14.21 7.58,16 12,16C16.42,16 20,14.21 20,12V9C20,11.21 16.42,13 12,13C7.58,13 4,11.21 4,9M4,14V17C4,19.21 7.58,21 12,21C16.42,21 20,19.21 20,17V14C20,16.21 16.42,18 12,18C7.58,18 4,16.21 4,14Z"/>
          </svg>
          <div>
            <h3 class="text-sm font-semibold text-theme-text">Preferences Backup &amp; Restore</h3>
            <p class="text-xs text-theme-text-muted mt-0.5 leading-relaxed max-w-lg">
              Backups contain your <strong class="font-medium text-theme-text">settings and preferences only</strong>
              — not your notes. Notes are stored as markdown files and are not affected by backup or restore.
            </p>
          </div>
        </div>

        <!-- Backup now button -->
        <button
          @click="doCreateBackup"
          :disabled="backupCreating"
          class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium
                 bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors
                 disabled:opacity-50 touch-manipulation"
        >
          <svg v-if="backupCreating" viewBox="0 0 24 24" class="w-4 h-4 fill-current animate-spin">
            <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current">
            <path d="M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z"/>
          </svg>
          {{ backupCreating ? 'Creating…' : 'Backup now' }}
        </button>
      </div>

      <!-- Retention setting -->
      <div class="flex flex-wrap items-center gap-3 mb-4 px-3 py-2.5 rounded-lg bg-theme-background-elevated border border-theme-border">
        <label class="text-xs font-medium text-theme-text-muted shrink-0">Backups to keep</label>
        <input
          v-model.number="retainCount"
          type="number"
          min="1"
          max="30"
          class="w-16 text-sm bg-theme-background border border-theme-border rounded px-2 py-1
                 outline-none focus:border-theme-brand text-theme-text"
          @change="saveRetainCount"
        />
        <span class="text-xs text-theme-text-very-muted">Oldest backups are automatically deleted when the limit is reached.</span>
        <span v-if="retainSaveMsg" class="text-xs ml-auto" :class="retainSaveOk ? 'text-green-500' : 'text-red-500'">
          {{ retainSaveMsg }}
        </span>
      </div>

      <!-- Restore-complete banner -->
      <div
        v-if="restoreComplete"
        class="flex flex-wrap items-center justify-between gap-3 mb-4 px-4 py-3 rounded-lg
               border border-green-400/40 bg-green-500/8"
      >
        <div class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current shrink-0">
            <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,16.5L18,9.5L16.59,8.09L11,13.67L7.41,10.09L6,11.5L11,16.5Z"/>
          </svg>
          Restore complete — reload the page to apply your restored preferences.
        </div>
        <button
          @click="reloadPage"
          class="shrink-0 px-3 py-1.5 rounded text-sm font-medium bg-green-500 hover:bg-green-600
                 text-white transition-colors touch-manipulation"
        >
          Reload page
        </button>
      </div>

      <!-- Backup list -->
      <div class="border border-theme-border rounded-lg overflow-hidden">

        <!-- Loading skeleton -->
        <template v-if="backupsLoading">
          <div class="p-3 space-y-2">
            <div v-for="n in 3" :key="n" class="h-10 rounded bg-theme-background-elevated animate-pulse"></div>
          </div>
        </template>

        <!-- Empty state -->
        <div
          v-else-if="backups.length === 0"
          class="px-4 py-8 text-center text-sm text-theme-text-very-muted"
        >
          No backups yet — click "Backup now" to create one.
        </div>

        <!-- List -->
        <div v-else class="overflow-y-auto" style="max-height: 300px;">
          <div
            v-for="backup in backups"
            :key="backup.filename"
            class="border-b border-theme-border last:border-b-0"
          >
            <!-- Normal row -->
            <div
              v-if="confirmRestoreFile !== backup.filename && confirmDeleteFile !== backup.filename"
              class="flex flex-wrap items-center gap-2 px-3 py-2.5 bg-theme-background hover:bg-theme-background-elevated/50 transition-colors"
            >
              <!-- Icon -->
              <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current text-theme-text-very-muted shrink-0">
                <path d="M12,3C7.58,3 4,4.79 4,7C4,9.21 7.58,11 12,11C16.42,11 20,9.21 20,7C20,4.79 16.42,3 12,3M4,9V12C4,14.21 7.58,16 12,16C16.42,16 20,14.21 20,12V9C20,11.21 16.42,13 12,13C7.58,13 4,11.21 4,9M4,14V17C4,19.21 7.58,21 12,21C16.42,21 20,19.21 20,17V14C20,16.21 16.42,18 12,18C7.58,18 4,16.21 4,14Z"/>
              </svg>

              <!-- Filename + meta -->
              <div class="flex-1 min-w-0">
                <p class="text-xs font-mono text-theme-text truncate" :title="'Backup filename (timestamp in UTC): ' + backup.filename">
                  {{ backup.filename }}
                </p>
                <p class="text-xs text-theme-text-very-muted mt-0.5"
                   :title="'When the database file was last saved (' + formatBackupDate(backup.created_at) + ')'">
                  Database Last Saved: {{ formatBackupDate(backup.created_at) }} · {{ backup.size_human }}
                  <span
                    v-if="backup.label && backup.label !== 'manual' && backup.label !== 'startup'"
                    class="ml-1 px-1 py-0.5 rounded bg-theme-background-elevated font-medium"
                  >{{ backup.label }}</span>
                </p>
              </div>

              <!-- Actions -->
              <div class="flex items-center gap-1.5 shrink-0">
                <button
                  @click="confirmRestoreFile = backup.filename; restoreConfirmInput = ''"
                  class="px-2.5 py-1 rounded text-xs font-medium border border-theme-border
                         text-theme-text-muted hover:bg-theme-background-elevated transition-colors touch-manipulation"
                  title="Restore this backup"
                >
                  Restore
                </button>
                <button
                  @click="confirmDeleteFile = backup.filename"
                  class="px-2.5 py-1 rounded text-xs font-medium border border-red-400/30
                         text-red-400 hover:bg-red-500/10 transition-colors touch-manipulation"
                  title="Delete this backup"
                >
                  Delete
                </button>
              </div>
            </div>

            <!-- Inline restore confirmation -->
            <div
              v-else-if="confirmRestoreFile === backup.filename"
              class="px-4 py-3 bg-red-500/5 border-l-4 border-red-400 space-y-3"
            >
              <div class="flex items-start gap-2">
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current text-red-500 shrink-0 mt-0.5">
                  <path d="M13,14H11V10H13M13,18H11V16H13M1,21H23L12,2L1,21Z"/>
                </svg>
                <div>
                  <p class="text-sm font-medium text-theme-text">Restore preferences from this backup?</p>
                  <p class="text-xs text-theme-text-muted mt-1 leading-relaxed">
                    This will replace your current settings and preferences. A safety backup will be created first.
                    You will need to reload the page after restoring.
                  </p>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <label class="text-xs text-theme-text-muted shrink-0">Type <strong>RESTORE</strong> to confirm:</label>
                <input
                  v-model="restoreConfirmInput"
                  type="text"
                  placeholder="RESTORE"
                  class="w-32 text-sm bg-theme-background border border-theme-border rounded px-2 py-1
                         outline-none focus:border-red-400 text-theme-text font-mono"
                  @keydown.enter="restoreConfirmInput === 'RESTORE' && doRestore(backup.filename)"
                  @keydown.esc="confirmRestoreFile = null; restoreConfirmInput = ''"
                />
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="confirmRestoreFile = null; restoreConfirmInput = ''"
                  :disabled="restoring"
                  class="px-3 py-1.5 rounded text-sm text-theme-text-muted border border-theme-border
                         hover:bg-theme-background-elevated transition-colors disabled:opacity-50 touch-manipulation"
                >Cancel</button>
                <button
                  @click="doRestore(backup.filename)"
                  :disabled="restoreConfirmInput !== 'RESTORE' || restoring"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium
                         bg-red-500 hover:bg-red-600 text-white transition-colors
                         disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation"
                >
                  <svg v-if="restoring" viewBox="0 0 24 24" class="w-4 h-4 fill-current animate-spin">
                    <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
                  </svg>
                  {{ restoring ? 'Restoring…' : 'Confirm Restore' }}
                </button>
              </div>
            </div>

            <!-- Inline delete confirmation -->
            <div
              v-else-if="confirmDeleteFile === backup.filename"
              class="flex flex-wrap items-center gap-3 px-4 py-2.5 bg-theme-background-elevated"
            >
              <span class="text-xs text-theme-text-muted flex-1 min-w-0">
                Delete <span class="font-mono text-theme-text">{{ backup.filename }}</span>?
              </span>
              <div class="flex items-center gap-2 shrink-0">
                <button
                  @click="confirmDeleteFile = null"
                  class="px-2.5 py-1 rounded text-xs text-theme-text-muted border border-theme-border
                         hover:bg-theme-background transition-colors touch-manipulation"
                >Cancel</button>
                <button
                  @click="doDelete(backup.filename)"
                  class="px-2.5 py-1 rounded text-xs font-medium bg-red-500 hover:bg-red-600
                         text-white transition-colors touch-manipulation"
                >Delete</button>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- Action feedback -->
      <p v-if="backupActionMsg" class="mt-2 text-xs" :class="backupActionOk ? 'text-green-500' : 'text-red-500'">
        {{ backupActionMsg }}
      </p>

    </div>
    <!-- /Backup & Restore -->

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  getMaintenanceStatus, emptyTrashNow,
  getBackups, createBackup, restoreBackup, deleteBackup,
  getPrefs, savePrefs,
} from "../api.js";

// ── Status / trash state ──────────────────────────────────────────────────────
const status     = ref(null);
const loading    = ref(false);
const loadError  = ref(false);

const showConfirm  = ref(false);
const emptyDays    = ref(0);
const emptyingTrash = ref(false);
const emptyMsg     = ref("");
const emptyOk      = ref(true);

const lastCleanupDisplay = computed(() => {
  if (!status.value?.last_trash_cleanup) return "Never";
  try {
    const dt = new Date(status.value.last_trash_cleanup);
    const diffMs   = Date.now() - dt.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays === 0)  return "Today";
    if (diffDays === 1)  return "Yesterday";
    if (diffDays < 30)   return `${diffDays} days ago`;
    const diffMonths = Math.floor(diffDays / 30);
    return `${diffMonths} month${diffMonths !== 1 ? "s" : ""} ago`;
  } catch {
    return "Unknown";
  }
});

async function loadStatus() {
  loading.value   = true;
  loadError.value = false;
  try {
    status.value = await getMaintenanceStatus();
  } catch {
    loadError.value = true;
  } finally {
    loading.value = false;
  }
}

function openConfirm() {
  emptyDays.value = 0;
  emptyMsg.value  = "";
  showConfirm.value = true;
}

async function doEmptyTrash() {
  emptyingTrash.value = true;
  emptyMsg.value      = "";
  try {
    const result = await emptyTrashNow(emptyDays.value);
    emptyOk.value   = true;
    emptyMsg.value  = `Deleted ${result.deleted_count} note${result.deleted_count !== 1 ? "s" : ""} ✓`;
    showConfirm.value = false;
    await loadStatus();
  } catch {
    emptyOk.value  = false;
    emptyMsg.value = "Failed to empty trash";
  } finally {
    emptyingTrash.value = false;
    setTimeout(() => { emptyMsg.value = ""; }, 4000);
  }
}

// ── Backup state ──────────────────────────────────────────────────────────────
const backups        = ref([]);
const backupsLoading = ref(false);
const backupCreating = ref(false);
const backupActionMsg = ref("");
const backupActionOk  = ref(true);

const confirmRestoreFile  = ref(null);  // filename currently in restore confirm mode
const restoreConfirmInput = ref("");
const restoring           = ref(false);
const restoreComplete     = ref(false);

const confirmDeleteFile = ref(null);    // filename currently in delete confirm mode

// Retention setting
const retainCount   = ref(7);
function reloadPage() { window.location.reload(); }
const retainSaveMsg = ref("");
const retainSaveOk  = ref(true);

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatBackupDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatRelativeTime(iso) {
  if (!iso) return "unknown";
  try {
    const diffMs = Date.now() - new Date(iso).getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60)  return "just now";
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60)  return `${diffMin} minute${diffMin !== 1 ? "s" : ""} ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24)   return `${diffHr} hour${diffHr !== 1 ? "s" : ""} ago`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay} day${diffDay !== 1 ? "s" : ""} ago`;
  } catch {
    return "unknown";
  }
}

function showActionMsg(msg, ok = true, ms = 4000) {
  backupActionMsg.value = msg;
  backupActionOk.value  = ok;
  setTimeout(() => { backupActionMsg.value = ""; }, ms);
}

// ── Backup list ───────────────────────────────────────────────────────────────
async function loadBackups() {
  backupsLoading.value = true;
  try {
    backups.value = await getBackups();
  } catch {
    backups.value = [];
  } finally {
    backupsLoading.value = false;
  }
}

// ── Create ────────────────────────────────────────────────────────────────────
async function doCreateBackup() {
  backupCreating.value = true;
  try {
    await createBackup("manual");
    showActionMsg("Backup created ✓");
    await loadBackups();
  } catch {
    showActionMsg("Backup failed", false);
  } finally {
    backupCreating.value = false;
  }
}

// ── Restore ───────────────────────────────────────────────────────────────────
async function doRestore(filename) {
  restoring.value = true;
  try {
    await restoreBackup(filename);
    confirmRestoreFile.value  = null;
    restoreConfirmInput.value = "";
    restoreComplete.value     = true;
    await loadBackups();
  } catch {
    showActionMsg("Restore failed", false);
    confirmRestoreFile.value  = null;
    restoreConfirmInput.value = "";
  } finally {
    restoring.value = false;
  }
}

// ── Delete ────────────────────────────────────────────────────────────────────
async function doDelete(filename) {
  confirmDeleteFile.value = null;
  try {
    await deleteBackup(filename);
    showActionMsg("Backup deleted ✓");
    await loadBackups();
  } catch {
    showActionMsg("Delete failed", false);
  }
}

// ── Retention count ───────────────────────────────────────────────────────────
async function loadRetainCount() {
  try {
    const prefs = await getPrefs();
    const stored = prefs.backup_retain_count;
    if (stored) retainCount.value = Number(stored);
  } catch {
    // keep default 7
  }
}

async function saveRetainCount() {
  retainSaveMsg.value = "";
  try {
    await savePrefs({ backup_retain_count: retainCount.value });
    retainSaveOk.value  = true;
    retainSaveMsg.value = "Saved ✓";
  } catch {
    retainSaveOk.value  = false;
    retainSaveMsg.value = "Save failed";
  } finally {
    setTimeout(() => { retainSaveMsg.value = ""; }, 3000);
  }
}

// ── Mount ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadStatus(), loadBackups(), loadRetainCount()]);
});
</script>