<template>
  <div class="flex h-full max-w-[999px] flex-col">

    <!-- Page header -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-theme-text">Settings</h1>
      <p class="text-sm text-theme-text-muted mt-1">Customise your Flatnotes experience.</p>
    </div>

    <!-- Tab bar — horizontally scrollable on mobile -->
    <!-- Outer div owns the bottom border; inner div scrolls without clipping the -mb-px trick -->
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

    <!-- ── Tab: Callouts ──────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'callouts'">
      <h3 class="text-lg font-medium text-theme-text mb-1">Callout Styling</h3>
      <div class="flex flex-wrap items-start justify-between gap-2 mb-4">
        <p class="text-sm text-theme-text-muted flex-1 min-w-0">
          Define your callout types. Built-in types can be recolored but not deleted.
          Use <code class="bg-theme-background-elevated px-1 rounded text-xs">&gt; [!type] Title</code> in notes.
        </p>
        <button
          @click="addCallout"
          class="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded text-sm
                 bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text touch-manipulation"
        >
          <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
          Add callout
        </button>
      </div>

      <!-- Callout list — scrollable locked frame -->
      <div class="border border-theme-border rounded-lg overflow-hidden mb-3">
        <div class="overflow-y-auto" style="max-height: 375px;">
          <div class="space-y-3 p-3">
            <div
              v-for="(c, i) in editableCallouts"
              :key="c._key"
              class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 p-3 rounded-lg border border-theme-border bg-theme-background"
            >
              <!-- Row 1 on mobile: preview chip + type name + delete -->
              <div class="flex items-center gap-2 sm:contents">
                <!-- Live preview chip -->
                <div
                  class="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold w-28"
                  :style="previewStyle(c)"
                >
                  <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current flex-shrink-0"><path :d="c.icon"/></svg>
                  <span class="truncate">{{ c.label || c.type }}</span>
                </div>

                <!-- Type name -->
                <input
                  v-model="c.type"
                  :disabled="c.builtin"
                  placeholder="type"
                  class="w-28 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1.5
                         outline-none focus:border-theme-brand text-theme-text disabled:opacity-50 disabled:cursor-not-allowed"
                  @input="c.type = c.type.toLowerCase().replace(/[^a-z0-9-]/g, '')"
                />

                <!-- Delete/Status — pushed to right on mobile row 1 -->
                <div class="ml-auto sm:hidden w-8 shrink-0 flex justify-end">
                  <button
                    v-if="!c.builtin"
                    @click="removeCallout(i)"
                    class="text-theme-text-muted hover:text-red-500 transition-colors p-1.5 rounded touch-manipulation"
                    title="Delete callout"
                  >
                    <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                      <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                    </svg>
                  </button>
                  <span v-else class="text-theme-text-very-muted" title="Built-in callout (cannot be deleted)">
                    <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                      <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                    </svg>
                  </span>
                </div>
              </div>

              <!-- Row 2 on mobile: label + color picker group + icon + delete (desktop) -->
              <div class="flex flex-wrap items-center gap-2 sm:contents">
                <!-- Label -->
                <input
                  v-model="c.label"
                  placeholder="Label"
                  class="w-32 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1.5
                         outline-none focus:border-theme-brand text-theme-text"
                />

                <!-- Color picker group -->
                <div class="flex items-center gap-2 shrink-0">
                  <input
                    type="color"
                    v-model="c.color"
                    class="w-8 h-8 rounded cursor-pointer border border-theme-border bg-transparent shrink-0"
                    title="Pick color"
                  />
                  <input
                    v-model="c.color"
                    placeholder="#337AB7"
                    class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                           rounded px-2 py-1.5 outline-none focus:border-theme-brand text-theme-text uppercase"
                    @input="c.color = normalizeHex($event.target.value)"
                  />
                </div>

                <!-- Icon button -->
                <button
                  @click="openIconPicker(i)"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm border border-theme-border
                         bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text-muted shrink-0 w-20 justify-center touch-manipulation"
                  title="Change icon"
                >
                  <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path :d="c.icon"/></svg>
                  <span>Icon</span>
                </button>

                <!-- Delete/Status — desktop only -->
                <div class="hidden sm:flex w-20 shrink-0 justify-end">
                  <button
                    v-if="!c.builtin"
                    @click="removeCallout(i)"
                    class="text-theme-text-muted hover:text-red-500 transition-colors p-1.5 rounded touch-manipulation"
                    title="Delete callout"
                  >
                    <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                      <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                    </svg>
                  </button>
                  <span v-else class="text-theme-text-very-muted" title="Built-in callout (cannot be deleted)">
                    <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                      <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                    </svg>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- /Callout list scrollable frame -->

      <!-- Save / status -->
      <div class="mt-5 flex items-center gap-3">
        <button
          @click="saveCallouts"
          :disabled="calloutsaving"
          class="px-4 py-2 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
                 text-white transition-colors disabled:opacity-50 touch-manipulation"
        >
          {{ calloutsaving ? 'Saving…' : 'Save callouts' }}
        </button>
        <span v-if="calloutSaveMsg" class="text-sm" :class="calloutSaveOk ? 'text-green-500' : 'text-red-500'">
          {{ calloutSaveMsg }}
        </span>
      </div>
    </div>

    <!-- ── Tab: Appearance (Header & Highlight Colors) ─────────────────────── -->
    <div v-if="activeTab === 'appearance'">
      <div class="space-y-6">
        
        <!-- Header Colors Section -->
        <div>
          <h3 class="text-lg font-medium text-theme-text mb-1">Header Colors</h3>
          <p class="text-sm text-theme-text-muted mb-4">Customize colors for headings H1 through H6.</p>

          <!-- Enable / disable slider -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
            <div>
              <p class="text-sm font-medium text-theme-text">Enable custom header colors</p>
              <p class="text-xs text-theme-text-muted mt-0.5">Apply custom colors to H1–H6 headings.</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" v-model="headersEnabled" class="sr-only peer" />
              <div class="w-11 h-6 bg-theme-border rounded-full peer
                          peer-checked:bg-theme-brand transition-colors
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-5 after:w-5
                          after:transition-transform peer-checked:after:translate-x-5"></div>
            </label>
          </div>

          <div class="space-y-2 p-4 rounded-lg border border-theme-border bg-theme-background"
               :class="!headersEnabled ? 'opacity-50 pointer-events-none' : ''">
            <div v-for="header in editableHeaders" :key="header.level"
                 class="flex flex-wrap items-center gap-3 py-1">
              <!-- Level label -->
              <div class="w-8 text-sm font-semibold text-theme-text shrink-0">H{{ header.level }}</div>

              <!-- Color square -->
              <input
                type="color"
                v-model="header.color"
                :disabled="!header.enabled"
                class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent shrink-0 disabled:opacity-40"
              />

              <!-- Hex input -->
              <input
                v-model="header.color"
                :disabled="!header.enabled"
                class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                       rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text
                       uppercase disabled:opacity-40"
              />

              <!-- Live preview -->
              <span
                :style="{ color: header.enabled ? header.color : 'var(--theme-text-muted)' }"
                class="flex-1 min-w-[6rem] text-sm font-semibold truncate transition-colors"
              >
                Heading {{ header.level }} preview
              </span>

              <!-- Per-row enabled slider -->
              <label class="relative inline-flex items-center cursor-pointer shrink-0">
                <input type="checkbox" v-model="header.enabled" class="sr-only peer" />
                <div class="w-9 h-5 bg-theme-border rounded-full peer
                            peer-checked:bg-theme-brand transition-colors
                            after:content-[''] after:absolute after:top-0.5 after:left-0.5
                            after:bg-white after:rounded-full after:h-4 after:w-4
                            after:transition-transform peer-checked:after:translate-x-4"></div>
              </label>
            </div>
          </div>

          <div class="mt-3 flex items-center gap-3">
            <button
              @click="saveHeaders"
              :disabled="headersSaving"
              class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
            >{{ headersSaving ? 'Saving…' : 'Save Header Colors' }}</button>
            <span v-if="headersSaveMsg" class="text-sm" :class="headersSaveOk ? 'text-green-500' : 'text-red-500'">{{ headersSaveMsg }}</span>
          </div>
        </div>

        <!-- Divider -->
        <div class="border-t border-theme-border my-4"></div>

        <!-- Highlight Colors Section -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-lg font-medium text-theme-text">Highlight Colors</h3>
            <button
              @click="addHighlightColor"
              class="flex items-center gap-1.5 px-2 py-1 rounded text-xs
                     bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text touch-manipulation"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
              Add color
            </button>
          </div>
          <p class="text-sm text-theme-text-muted mb-4">
            These colors appear in the highlight picker. The default color is used when highlighting text with the toolbar button.
          </p>
          
          <div class="space-y-3">
            <div v-for="(hc, idx) in editableHighlights" :key="hc._key"
                 class="flex flex-wrap items-center gap-2 p-2 rounded-lg border border-theme-border bg-theme-background">
              <input type="color" v-model="hc.color" :disabled="!hc.enabled"
                     class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent shrink-0 disabled:opacity-40" />
              <input v-model="hc.name" placeholder="Name"
                     class="w-24 text-sm bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text" />
              <input v-model="hc.color"
                     class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase" />
              <!-- Per-row enabled slider -->
              <label class="relative inline-flex items-center cursor-pointer shrink-0 ml-1">
                <input type="checkbox" v-model="hc.enabled" class="sr-only peer" />
                <div class="w-9 h-5 bg-theme-border rounded-full peer
                            peer-checked:bg-theme-brand transition-colors
                            after:content-[''] after:absolute after:top-0.5 after:left-0.5
                            after:bg-white after:rounded-full after:h-4 after:w-4
                            after:transition-transform peer-checked:after:translate-x-4"></div>
              </label>
              <button
                @click="setDefaultHighlight(hc.name)"
                class="px-2 py-1 rounded text-xs border border-theme-border bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors touch-manipulation"
                :class="{ 'bg-theme-brand/20 border-theme-brand': defaultHighlightName === hc.name }"
                title="Set as default"
              >
                Default
              </button>
              <button
                v-if="!hc.isDefault"
                @click="removeHighlightColor(idx)"
                class="text-theme-text-muted hover:text-red-500 transition-colors p-1 rounded shrink-0 touch-manipulation"
                title="Delete color"
              >
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                  <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
              </button>
              <span v-else class="text-theme-text-very-muted" title="Built-in color (cannot be deleted)">
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                  <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                </svg>
              </span>
            </div>
          </div>
          
          <div class="mt-4 p-3 rounded-lg bg-theme-background-elevated border border-theme-border">
            <p class="text-sm text-theme-text-muted mb-2">Preview with default highlight:</p>
            <mark :style="{ backgroundColor: defaultHighlightColor, padding: '0 4px', borderRadius: '2px' }">This is how highlighted text appears</mark>
          </div>
          
          <div class="mt-3 flex items-center gap-3">
            <button
              @click="saveHighlights"
              :disabled="highlightsSaving"
              class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
            >{{ highlightsSaving ? 'Saving…' : 'Save Highlight Colors' }}</button>
            <span v-if="highlightsSaveMsg" class="text-sm" :class="highlightsSaveOk ? 'text-green-500' : 'text-red-500'">{{ highlightsSaveMsg }}</span>
          </div>
        </div>
        
      </div>
    </div>

    <!-- ── Tab: Advanced (Table & Quote Styling) ─────────────────────────────── -->
    <div v-if="activeTab === 'advanced'">
      <div class="space-y-8">
        
        <!-- Table Styling Section -->
        <div>
          <h3 class="text-lg font-medium text-theme-text mb-1">Table Styling</h3>
          <p class="text-sm text-theme-text-muted mb-4">Customize how tables appear in your notes.</p>
          <!-- Enable / disable slider -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
            <div>
              <p class="text-sm font-medium text-theme-text">Enable custom table styling</p>
              <p class="text-xs text-theme-text-muted mt-0.5">Apply custom header colors and zebra-striped rows.</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" v-model="tableStyle.enabled" class="sr-only peer" />
              <div class="w-11 h-6 bg-theme-border rounded-full peer
                          peer-checked:bg-theme-brand transition-colors
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-5 after:w-5
                          after:transition-transform peer-checked:after:translate-x-5"></div>
            </label>
          </div>
          
          <div class="space-y-4 p-4 rounded-lg border border-theme-border bg-theme-background">
            <!-- Header color picker -->
            <div class="flex flex-wrap items-center gap-4">
              <div class="w-24 text-sm text-theme-text">Header color</div>
              <input
                type="color"
                v-model="tableStyle.header_color"
                :disabled="!tableStyle.enabled"
                class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
              />
              <input
                v-model="tableStyle.header_color"
                :disabled="!tableStyle.enabled"
                class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase disabled:opacity-50"
              />
            </div>
            
            <!-- Zebra striping toggle -->
            <div class="flex items-center gap-4">
              <div class="w-24 text-sm text-theme-text shrink-0">Zebra striping</div>
              <label class="relative inline-flex items-center cursor-pointer" :class="!tableStyle.enabled ? 'opacity-40 pointer-events-none' : ''">
                <input type="checkbox" v-model="tableStyle.zebra_striping" :disabled="!tableStyle.enabled" class="sr-only peer" />
                <div class="w-9 h-5 bg-theme-border rounded-full peer
                            peer-checked:bg-theme-brand transition-colors
                            after:content-[''] after:absolute after:top-0.5 after:left-0.5
                            after:bg-white after:rounded-full after:h-4 after:w-4
                            after:transition-transform peer-checked:after:translate-x-4"></div>
              </label>
              <span class="text-sm text-theme-text-muted">Alternate row colors</span>
            </div>
            
            <!-- Table preview -->
            <div class="mt-4 pt-4 border-t border-theme-border">
              <p class="text-xs text-theme-text-very-muted mb-3">Preview:</p>
              <div class="overflow-x-auto">
                <table class="w-full text-sm border-collapse">
                  <thead>
                    <tr>
                      <th :style="tableStyle.enabled ? { backgroundColor: tableStyle.header_color, color: 'white' } : {}" class="border border-theme-border px-3 py-2 text-left">Header 1</th>
                      <th :style="tableStyle.enabled ? { backgroundColor: tableStyle.header_color, color: 'white' } : {}" class="border border-theme-border px-3 py-2 text-left">Header 2</th>
                      <th :style="tableStyle.enabled ? { backgroundColor: tableStyle.header_color, color: 'white' } : {}" class="border border-theme-border px-3 py-2 text-left">Header 3</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr :class="tableStyle.enabled && tableStyle.zebra_striping ? 'bg-theme-background-elevated' : ''">
                      <td class="border border-theme-border px-3 py-2">Row 1, Cell 1</td>
                      <td class="border border-theme-border px-3 py-2">Row 1, Cell 2</td>
                      <td class="border border-theme-border px-3 py-2">Row 1, Cell 3</td>
                    </tr>
                    <tr :class="tableStyle.enabled && tableStyle.zebra_striping ? '' : 'bg-theme-background-elevated'">
                      <td class="border border-theme-border px-3 py-2">Row 2, Cell 1</td>
                      <td class="border border-theme-border px-3 py-2">Row 2, Cell 2</td>
                      <td class="border border-theme-border px-3 py-2">Row 2, Cell 3</td>
                    </tr>
                    <tr :class="tableStyle.enabled && tableStyle.zebra_striping ? 'bg-theme-background-elevated' : ''">
                      <td class="border border-theme-border px-3 py-2">Row 3, Cell 1</td>
                      <td class="border border-theme-border px-3 py-2">Row 3, Cell 2</td>
                      <td class="border border-theme-border px-3 py-2">Row 3, Cell 3</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <div class="mt-3 flex items-center gap-3">
            <button
              @click="saveTableStyle"
              :disabled="tableSaving"
              class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
            >{{ tableSaving ? 'Saving…' : 'Save Table Style' }}</button>
            <span v-if="tableSaveMsg" class="text-sm" :class="tableSaveOk ? 'text-green-500' : 'text-red-500'">{{ tableSaveMsg }}</span>
          </div>
        </div>

        <!-- Divider -->
        <div class="border-t border-theme-border my-4"></div>

        <!-- Quote Styling Section -->
        <div>
          <h3 class="text-lg font-medium text-theme-text mb-1">Quote Styling</h3>
          <p class="text-sm text-theme-text-muted mb-4">Customize how blockquotes appear in your notes.</p>
          <!-- Enable / disable slider -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
            <div>
              <p class="text-sm font-medium text-theme-text">Enable custom quote styling</p>
              <p class="text-xs text-theme-text-muted mt-0.5">Apply custom border color and background to blockquotes.</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" v-model="quoteStyle.enabled" class="sr-only peer" />
              <div class="w-11 h-6 bg-theme-border rounded-full peer
                          peer-checked:bg-theme-brand transition-colors
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-5 after:w-5
                          after:transition-transform peer-checked:after:translate-x-5"></div>
            </label>
          </div>
          
          <div class="space-y-4 p-4 rounded-lg border border-theme-border bg-theme-background">
            <!-- Border color picker -->
            <div class="flex flex-wrap items-center gap-4">
              <div class="w-24 text-sm text-theme-text">Border color</div>
              <input
                type="color"
                v-model="quoteStyle.border_color"
                :disabled="!quoteStyle.enabled"
                class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
              />
              <input
                v-model="quoteStyle.border_color"
                :disabled="!quoteStyle.enabled"
                class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase disabled:opacity-50"
              />
            </div>
            
            <!-- Light mode background picker -->
            <div class="flex flex-wrap items-center gap-4">
              <div class="w-24 text-sm text-theme-text">Light background</div>
              <input
                type="color"
                v-model="quoteStyle.background_color"
                :disabled="!quoteStyle.enabled"
                class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
              />
              <input
                v-model="quoteStyle.background_color"
                :disabled="!quoteStyle.enabled"
                class="w-28 text-xs font-mono bg-theme-background-elevated border border-theme-border rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase disabled:opacity-50"
              />
            </div>
            
            <!-- Dark mode background picker (color + opacity) -->
            <div class="flex flex-wrap items-center gap-4">
              <div class="w-24 text-sm text-theme-text">Dark background</div>
              <input
                type="color"
                v-model="darkBgHex"
                :disabled="!quoteStyle.enabled"
                class="w-10 h-10 rounded cursor-pointer border border-theme-border bg-transparent disabled:opacity-50"
              />
              <div class="flex flex-col gap-1">
                <div class="flex items-center gap-2">
                  <span class="text-xs text-theme-text-muted w-14">Opacity</span>
                  <input
                    type="range"
                    v-model.number="darkBgOpacity"
                    :disabled="!quoteStyle.enabled"
                    min="0" max="100" step="1"
                    class="w-24 accent-theme-brand disabled:opacity-50"
                  />
                  <span class="text-xs font-mono text-theme-text w-8">{{ darkBgOpacity }}%</span>
                </div>
                <p class="text-xs text-theme-text-very-muted">Applied only in dark mode</p>
              </div>
            </div>
            
            <!-- Quote preview — respects current dark/light theme -->
            <div class="mt-4 pt-4 border-t border-theme-border">
              <div class="flex items-center justify-between mb-3">
                <p class="text-xs text-theme-text-very-muted">Preview:</p>
                <span class="text-xs text-theme-text-very-muted italic">
                  {{ isDark ? "dark theme" : "light theme" }}
                </span>
              </div>
              <div
                :style="quoteStyle.enabled ? {
                  borderLeft: `6px solid ${quoteStyle.border_color}`,
                  backgroundColor: isDark
                    ? quoteStyle.dark_background_color
                    : quoteStyle.background_color,
                  color: isDark ? '#dadada' : '#085294',
                  borderRadius: '4px',
                  padding: '0.5em 1em',
                } : { borderLeft: '6px solid #e5e5e5', borderRadius: '4px', padding: '0.5em 1em' }"
              >
                <p class="text-sm">This is a sample blockquote — it will appear with your chosen colors.</p>
                <p class="text-sm mt-2" style="margin-bottom: 0">Quote styling adds visual emphasis to important information.</p>
              </div>
            </div>
          </div>
          
          <div class="mt-3 flex items-center gap-3">
            <button
              @click="saveQuoteStyle"
              :disabled="quoteSaving"
              class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand text-white transition-colors disabled:opacity-50 touch-manipulation"
            >{{ quoteSaving ? 'Saving…' : 'Save Quote Style' }}</button>
            <span v-if="quoteSaveMsg" class="text-sm" :class="quoteSaveOk ? 'text-green-500' : 'text-red-500'">{{ quoteSaveMsg }}</span>
          </div>
        </div>
        
      </div>
    </div>

    <!-- ── Tab: Tags ────────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'tags'">
      <h3 class="text-lg font-medium text-theme-text mb-1">Tag Colors</h3>
      <p class="text-sm text-theme-text-muted mb-4">
        Customise how tag chips look across the app — in notes, sidebars, and search results.
      </p>

      <!-- Global enable / disable toggle -->
      <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
        <div>
          <p class="text-sm font-medium text-theme-text">Enable custom tag colors</p>
          <p class="text-xs text-theme-text-muted mt-0.5">
            When disabled, all tags use the default color below.
          </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
          <input type="checkbox" v-model="tagColorsEnabled" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <!-- Default color (always shown) -->
      <div class="flex flex-wrap items-center gap-3 p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-theme-text">Default tag color</p>
          <p class="text-xs text-theme-text-muted mt-0.5">
            Used for all tags when custom colors are disabled, and as the fallback for unassigned tags.
          </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <input
            type="color"
            v-model="tagDefaultColor"
            class="w-9 h-9 rounded cursor-pointer border border-theme-border bg-transparent"
            title="Pick default color"
          />
          <input
            v-model="tagDefaultColor"
            class="w-24 text-xs font-mono bg-theme-background-elevated border border-theme-border
                   rounded px-2 py-1.5 outline-none focus:border-theme-brand text-theme-text uppercase"
            placeholder="#006633"
          />
          <!-- Live preview chip -->
          <span :style="tagColorPreviewStyle(tagDefaultColor)">
            <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current" style="display:inline-block">
              <path d="M21.41,11.58L12.41,2.58C12.05,2.22 11.55,2 11,2H4C2.9,2 2,2.9 2,4V11C2,11.55 2.22,12.05 2.59,12.42L11.59,21.42C11.95,21.78 12.45,22 13,22C13.55,22 14.05,21.78 14.41,21.41L21.41,14.41C21.78,14.05 22,13.55 22,13C22,12.45 21.77,11.95 21.41,11.58M5.5,7C4.67,7 4,6.33 4,5.5C4,4.67 4.67,4 5.5,4C6.33,4 7,4.67 7,5.5C7,6.33 6.33,7 5.5,7Z"/>
            </svg>
            example
          </span>
        </div>
      </div>

      <!-- Per-tag overrides (only when custom colors enabled) -->
      <div v-if="tagColorsEnabled">
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm font-medium text-theme-text">Per-tag color overrides</p>
          <button
            @click="addTagColorRow()"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs
                   bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text touch-manipulation"
          >
            <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current">
              <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
            Add row
          </button>
        </div>

        <!-- Scrollable locked frame for color rows -->
        <div class="border border-theme-border rounded-lg overflow-hidden mb-3">
          <div class="overflow-y-auto" style="max-height: 370px;">

            <!-- Empty state -->
            <div v-if="editableTagColors.length === 0"
                 class="px-4 py-6 text-center text-xs text-theme-text-very-muted">
              No custom tag colors yet. Click "Add row" or click a tag name below.
            </div>

            <!-- Tag color rows -->
            <div
              v-for="(row, i) in editableTagColors"
              :key="row._key"
              class="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-theme-border last:border-b-0
                     bg-theme-background hover:bg-theme-background-elevated/50 transition-colors"
            >
              <!-- Tag name input: # [parent] / [child] for nested tag support -->
              <div class="flex items-center gap-1 min-w-0">
                <span class="text-sm text-theme-text-very-muted shrink-0 select-none">#</span>
                <input
                  :value="row.tag.includes('/') ? row.tag.split('/')[0] : row.tag"
                  @input="(e) => {
                    const parent = e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '');
                    const child = row.tag.includes('/') ? row.tag.split('/').slice(1).join('/') : '';
                    row.tag = child ? parent + '/' + child : parent;
                  }"
                  placeholder="parent"
                  title="Parent tag name"
                  class="w-24 text-sm bg-theme-background-elevated border border-theme-border
                         rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text"
                />
                <span class="text-theme-text-very-muted shrink-0 select-none text-sm">/</span>
                <input
                  :value="row.tag.includes('/') ? row.tag.split('/').slice(1).join('/') : ''"
                  @input="(e) => {
                    const child = e.target.value.toLowerCase().replace(/[^a-z0-9_/-]/g, '');
                    const parent = row.tag.includes('/') ? row.tag.split('/')[0] : row.tag;
                    row.tag = child ? (parent || 'tag') + '/' + child : parent;
                  }"
                  placeholder="child"
                  title="Child tag name (optional — leave empty for top-level tag)"
                  class="w-24 text-sm bg-theme-background-elevated border border-theme-border
                         rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text"
                />
              </div>

              <!-- Color picker -->
              <input
                type="color"
                v-model="row.color"
                class="w-8 h-8 rounded cursor-pointer border border-theme-border bg-transparent shrink-0"
              />
              <input
                v-model="row.color"
                class="w-20 text-xs font-mono bg-theme-background-elevated border border-theme-border
                       rounded px-2 py-1 outline-none focus:border-theme-brand text-theme-text uppercase"
              />

              <!-- Live preview chip -->
              <span :style="tagColorPreviewStyle(row.color)" class="shrink-0">
                <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current" style="display:inline-block">
                  <path d="M21.41,11.58L12.41,2.58C12.05,2.22 11.55,2 11,2H4C2.9,2 2,2.9 2,4V11C2,11.55 2.22,12.05 2.59,12.42L11.59,21.42C11.95,21.78 12.45,22 13,22C13.55,22 14.05,21.78 14.41,21.41L21.41,14.41C21.78,14.05 22,13.55 22,13C22,12.45 21.77,11.95 21.41,11.58M5.5,7C4.67,7 4,6.33 4,5.5C4,4.67 4.67,4 5.5,4C6.33,4 7,4.67 7,5.5C7,6.33 6.33,7 5.5,7Z"/>
                </svg>
                {{ (row.tag || "example").split("/").join(" › ") }}
              </span>

              <!-- Enabled toggle -->
              <label class="relative inline-flex items-center cursor-pointer shrink-0 ml-auto" title="Enable this tag color">
                <input type="checkbox" v-model="row.enabled" class="sr-only peer" />
                <div class="w-9 h-5 bg-theme-border rounded-full peer
                            peer-checked:bg-theme-brand transition-colors
                            after:content-[''] after:absolute after:top-0.5 after:left-0.5
                            after:bg-white after:rounded-full after:h-4 after:w-4
                            after:transition-transform peer-checked:after:translate-x-4"></div>
              </label>

              <!-- Delete -->
              <button
                @click="removeTagColorRow(i)"
                class="text-theme-text-muted hover:text-red-500 transition-colors p-1 rounded shrink-0 touch-manipulation"
                title="Remove"
              >
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                  <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Your tags frame -->
        <div v-if="allTagsList.length > 0" class="border border-theme-border rounded-lg overflow-hidden mb-3">
          <div class="px-3 py-2 bg-theme-background-elevated border-b border-theme-border">
            <span class="text-xs font-medium text-theme-text-very-muted">Your tags — click to add a color override:</span>
          </div>
          <div class="overflow-y-auto" style="max-height: 120px;">
            <div class="px-3 py-2 flex flex-wrap gap-1">
              <button
                v-for="item in allTagsList"
                :key="item.tag"
                @click="addTagFromList(item.tag)"
                class="text-xs px-1.5 py-0.5 rounded-full border border-theme-border
                       bg-theme-background hover:bg-theme-background-elevated active:bg-theme-background-elevated
                       transition-colors text-theme-text-muted touch-manipulation"
                :title="`Add override for #${item.tag} (${item.count} notes)`"
              >
                #{{ item.tag }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Save button -->
      <div class="flex items-center gap-3 mt-2">
        <button
          @click="saveTagColors"
          :disabled="tagColorsSaving"
          class="px-3 py-1.5 rounded text-sm bg-theme-brand/90 hover:bg-theme-brand
                 text-white transition-colors disabled:opacity-50 touch-manipulation"
        >{{ tagColorsSaving ? "Saving…" : "Save Tag Colors" }}</button>
        <span
          v-if="tagColorsSaveMsg"
          class="text-sm"
          :class="tagColorsSaveOk ? 'text-green-500' : 'text-red-500'"
        >{{ tagColorsSaveMsg }}</span>
      </div>
    </div>

    <!-- ── Tab: Task Icons ────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'taskicons'">
      <h3 class="text-lg font-medium text-theme-text mb-1">Custom Task Icons</h3>
      <p class="text-sm text-theme-text-muted mb-4">
        Customize the colors for Obsidian-style task markers.
        Use <code class="bg-theme-background-elevated px-1 rounded text-xs">- [?] Question text</code> in your notes.
      </p>

      <!-- Global enable / disable toggle -->
      <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background mb-4">
        <div>
          <p class="text-sm font-medium text-theme-text">Enable custom task icons</p>
          <p class="text-xs text-theme-text-muted mt-0.5">Render task markers as icons instead of plain text in the note viewer.</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
          <input type="checkbox" v-model="taskIconsEnabled" class="sr-only peer" />
          <div class="w-11 h-6 bg-theme-border rounded-full peer
                      peer-checked:bg-theme-brand transition-colors
                      after:content-[''] after:absolute after:top-0.5 after:left-0.5
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-transform peer-checked:after:translate-x-5"></div>
        </label>
      </div>

      <!-- Icon color list — responsive: stacked cards on mobile, grid on sm+ -->
      <div
        class="border border-theme-border rounded-lg overflow-hidden mb-3"
        :class="!taskIconsEnabled ? 'opacity-50 pointer-events-none' : ''"
      >
        <!-- Column header — hidden on mobile, shown on sm+ -->
        <div class="hidden sm:grid px-3 py-2 bg-theme-background-elevated border-b border-theme-border
                    grid-cols-[1.75rem_7rem_1fr_9rem_1.75rem] gap-3 items-center sticky top-0 z-10">
          <span class="text-xs text-theme-text-very-muted font-medium">Icon</span>
          <span class="text-xs text-theme-text-very-muted font-medium">Syntax</span>
          <span class="text-xs text-theme-text-very-muted font-medium">Label</span>
          <span class="text-xs text-theme-text-very-muted font-medium">Color</span>
          <span></span>
        </div>

        <div class="overflow-y-auto" style="max-height: 380px;">
          <!-- Single loop — desktop grid layout shown on sm+, mobile card shown below sm -->
          <div
            v-for="row in taskIconColors"
            :key="row.marker"
            class="border-b border-theme-border last:border-b-0 bg-theme-background hover:bg-theme-background-elevated/40 transition-colors"
          >
            <!-- Desktop layout (sm and up) -->
            <div class="hidden sm:grid grid-cols-[1.75rem_7rem_1fr_9rem_1.75rem] gap-3 items-center px-3 py-2">
              <span class="flex items-center justify-center">
                <svg viewBox="0 0 24 24" width="18" height="18" :fill="row.color">
                  <path :d="row.iconPath" />
                </svg>
              </span>
              <code class="text-xs font-mono bg-theme-background-elevated px-2 py-0.5 rounded text-theme-text-muted whitespace-nowrap">
                - [{{ row.marker }}] text
              </code>
              <span class="text-sm text-theme-text capitalize">{{ row.label }}</span>
              <div class="flex items-center gap-1.5">
                <input
                  type="color"
                  v-model="row.color"
                  class="w-7 h-7 rounded cursor-pointer border border-theme-border bg-transparent shrink-0"
                  :title="'Color for [' + row.marker + ']'"
                />
                <input
                  v-model="row.color"
                  class="w-20 text-xs font-mono bg-theme-background-elevated border border-theme-border
                         rounded px-1.5 py-1 outline-none focus:border-theme-brand text-theme-text uppercase"
                  @input="row.color = normalizeHex($event.target.value)"
                />
              </div>
              <button
                @click="resetTaskIconColor(row.marker)"
                class="text-theme-text-very-muted hover:text-theme-text-muted transition-colors p-0.5 rounded touch-manipulation"
                title="Reset to default color"
              >
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                  <path d="M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"/>
                </svg>
              </button>
            </div>

            <!-- Mobile layout (below sm) -->
            <div class="flex sm:hidden items-center gap-3 px-3 py-2.5">
              <svg viewBox="0 0 24 24" width="20" height="20" :fill="row.color" class="shrink-0">
                <path :d="row.iconPath" />
              </svg>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-theme-text capitalize">{{ row.label }}</p>
                <code class="text-xs font-mono text-theme-text-muted">- [{{ row.marker }}] text</code>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <input
                  type="color"
                  v-model="row.color"
                  class="w-8 h-8 rounded cursor-pointer border border-theme-border bg-transparent"
                  :title="'Color for [' + row.marker + ']'"
                />
                <input
                  v-model="row.color"
                  class="w-20 text-xs font-mono bg-theme-background-elevated border border-theme-border
                         rounded px-1.5 py-1 outline-none focus:border-theme-brand text-theme-text uppercase"
                  @input="row.color = normalizeHex($event.target.value)"
                />
              </div>
              <button
                @click="resetTaskIconColor(row.marker)"
                class="text-theme-text-very-muted hover:text-theme-text-muted transition-colors p-1 rounded shrink-0 touch-manipulation"
                title="Reset to default color"
              >
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current">
                  <path d="M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Usage reference -->
      <div class="mb-4 p-3 rounded-lg bg-theme-background-elevated border border-theme-border">
        <p class="text-xs font-medium text-theme-text-muted mb-2">Quick reference — use these in your notes:</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-1.5">
          <div v-for="row in taskIconColors.slice(0, 9)" :key="'ref-' + row.marker" class="flex items-center gap-2 min-w-0">
            <svg viewBox="0 0 24 24" width="13" height="13" :fill="taskIconsEnabled ? row.color : 'currentColor'" class="shrink-0 text-theme-text-very-muted">
              <path :d="row.iconPath" />
            </svg>
            <code class="text-xs text-theme-text-muted font-mono shrink-0">- [{{ row.marker }}]</code>
            <span class="text-xs text-theme-text-very-muted capitalize truncate">{{ row.label }}</span>
          </div>
        </div>
        <p class="text-xs text-theme-text-very-muted mt-2 italic">
          … and {{ taskIconColors.length - 9 }} more. All markers are Obsidian-compatible.
        </p>
      </div>

      <!-- Actions row -->
      <div class="flex flex-wrap items-center gap-3">
        <button
          @click="saveTaskIconSettings"
          class="px-4 py-2 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
                 text-white transition-colors touch-manipulation"
        :disabled="taskIconsSaving">{{ taskIconsSaving ? 'Saving…' : 'Save task icons' }}</button>
        <button
          @click="resetAllTaskIconColors"
          class="px-3 py-1.5 rounded text-sm border border-theme-border
                 bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors text-theme-text-muted touch-manipulation"
        >Reset all colors</button>
        <span v-if="taskIconsSaveMsg" class="text-sm" :class="taskIconsSaveOk ? 'text-green-500' : 'text-red-500'">
          {{ taskIconsSaveMsg }}
        </span>
      </div>
    </div>

    <!-- ── Tab: Preferences ───────────────────────────────────────────────── -->
    <div v-if="activeTab === 'prefs'">
      <div class="space-y-3 max-w-md">
      <h3 class="text-lg font-medium text-theme-text mb-1">Account Preferences</h3>
      <p class="text-sm text-theme-text-muted mb-4">Customize your personal settings.</p>
        <!-- Display name -->
        <div>
          <label class="block text-sm font-medium text-theme-text mb-1">Display name</label>
          <input
            v-model="prefs.displayName"
            placeholder="Your name"
            class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-2
                   outline-none focus:border-theme-brand text-theme-text"
          />
          <p class="text-xs text-theme-text-very-muted mt-1">Shown in the app header (planned for a future update).</p>
        </div>

        <!-- Avatar -->
        <div>
          <label class="block text-sm font-medium text-theme-text mb-2">Avatar</label>
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-full bg-theme-background-elevated border border-theme-border
                        flex items-center justify-center overflow-hidden shrink-0">
              <img v-if="avatarUrl" :src="avatarUrl" class="w-full h-full object-cover" alt="Avatar"/>
              <svg v-else viewBox="0 0 24 24" class="w-8 h-8 fill-current text-theme-text-very-muted">
                <path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/>
              </svg>
            </div>
            <div class="flex flex-col gap-2">
              <label class="flex items-center gap-2 px-3 py-2 rounded text-sm border border-theme-border
                            bg-theme-background-elevated hover:bg-theme-border active:bg-theme-border transition-colors cursor-pointer text-theme-text touch-manipulation">
                <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z"/></svg>
                Upload image
                <input type="file" accept="image/*" class="hidden" @change="uploadAvatar"/>
              </label>
              <button
                v-if="prefs.avatarFilename"
                @click="removeAvatar"
                class="text-xs text-theme-text-muted hover:text-red-500 transition-colors text-left touch-manipulation"
              >Remove avatar</button>
            </div>
          </div>
        </div>

        <!-- Default sort -->
        <div>
          <label class="block text-sm font-medium text-theme-text mb-1">Default note sort</label>
          <select
            v-model="prefs.notesDefaultSort"
            class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-2
                   outline-none focus:border-theme-brand text-theme-text"
          >
            <option value="">App default</option>
            <option value="lastModified">Last modified</option>
            <option value="title">Title A–Z</option>
            <option value="score">Relevance</option>
          </select>
        </div>

        <!-- Preview toggle -->
        <div>
          <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background">
            <div>
              <p class="text-sm font-medium text-theme-text">Note preview on hover</p>
              <p class="text-xs text-theme-text-muted mt-0.5">
                Show preview popup when clicking the <span class="inline-flex items-center gap-0.5"><svg viewBox="0 0 24 24" class="w-3 h-3 fill-current"><path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,4.5C17,4.5 21.27,7.61 23,12C21.27,16.39 17,19.5 12,19.5C7,19.5 2.73,16.39 1,12C2.73,7.61 7,4.5 12,4.5M3.18,12C4.83,15.36 8.24,17.5 12,17.5C15.76,17.5 19.17,15.36 20.82,12C19.17,8.64 15.76,6.5 12,6.5C8.24,6.5 4.83,8.64 3.18,12Z"/></svg></span> eye button next to notes.
              </p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
              <input type="checkbox" v-model="previewEnabled" class="sr-only peer" @change="savePreviewSetting" />
              <div class="w-11 h-6 bg-theme-border rounded-full peer
                          peer-checked:bg-theme-brand transition-colors
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-5 after:w-5
                          after:transition-transform peer-checked:after:translate-x-5"></div>
            </label>
          </div>
        </div>

        <!-- Button labels toggle -->
        <div class="flex items-center justify-between p-3 rounded-lg border border-theme-border bg-theme-background">
          <div>
            <p class="text-sm font-medium text-theme-text">Show button labels</p>
            <p class="text-xs text-theme-text-muted mt-0.5">
              When off, navigation buttons show icons only — ideal for smaller screens.
            </p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
            <input type="checkbox" v-model="prefs.showButtonLabels" class="sr-only peer" />
            <div class="w-11 h-6 bg-theme-border rounded-full peer
                        peer-checked:bg-theme-brand transition-colors
                        after:content-[''] after:absolute after:top-0.5 after:left-0.5
                        after:bg-white after:rounded-full after:h-5 after:w-5
                        after:transition-transform peer-checked:after:translate-x-5"></div>
          </label>
        </div>

        <!-- Save -->
        <div class="flex items-center gap-3 pt-2">
          <button
            @click="savePrefs"
            :disabled="prefsSaving"
            class="px-4 py-2 rounded text-sm font-medium bg-theme-brand/90 hover:bg-theme-brand
                   text-white transition-colors disabled:opacity-50 touch-manipulation"
          >{{ prefsSaving ? 'Saving…' : 'Save preferences' }}</button>
          <span v-if="prefsSaveMsg" class="text-sm" :class="prefsSaveOk ? 'text-green-500' : 'text-red-500'">
            {{ prefsSaveMsg }}
          </span>
        </div>
      </div>
    </div>

    <!-- ── Icon picker modal ──────────────────────────────────────────────── -->
    <div
      v-if="iconPickerOpen"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="iconPickerOpen = false"
    >
      <div class="bg-theme-background rounded-t-2xl sm:rounded-xl border border-theme-border shadow-xl
                  w-full sm:w-[480px] max-h-[85vh] sm:max-h-[70vh] flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-theme-border shrink-0">
          <span class="font-semibold text-theme-text">Choose icon</span>
          <button @click="iconPickerOpen = false"
                  class="text-theme-text-muted hover:text-theme-text p-1 touch-manipulation">
            <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
          </button>
        </div>
        <div class="px-3 py-2 border-b border-theme-border shrink-0">
          <input v-model="iconSearch" placeholder="Search icons…"
            class="w-full text-sm bg-theme-background-elevated border border-theme-border rounded px-3 py-1.5
                   outline-none focus:border-theme-brand text-theme-text placeholder-theme-text-very-muted"/>
        </div>
        <div class="overflow-y-auto p-3 grid grid-cols-6 sm:grid-cols-8 gap-1">
          <button
            v-for="icon in filteredIcons"
            :key="icon.name"
            @click="pickIcon(icon)"
            class="flex flex-col items-center justify-center p-2 rounded hover:bg-theme-background-elevated
                   active:bg-theme-background-elevated transition-colors group touch-manipulation"
            :title="icon.name"
          >
            <svg viewBox="0 0 24 24" class="w-6 h-6 sm:w-5 sm:h-5 fill-current text-theme-text-muted group-hover:text-theme-text">
              <path :d="icon.path"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { 
  getCallouts, saveCallouts as apiSaveCallouts, 
  getPrefs, savePrefs as apiSavePrefs, 
  createAttachment, 
  getHeaderColors, saveHeaderColors,
  getHighlightColors, saveHighlightColors, getDefaultHighlight, saveDefaultHighlight,
  getTableStyle, saveTableStyle as apiSaveTableStyle,
  getQuoteStyle, saveQuoteStyle as apiSaveQuoteStyle,
  getTagColors as apiGetTagColors, saveTagColors as apiSaveTagColors,
  getTags,
} from "../api.js";
import { loadCallouts, hexToRgb } from "../calloutStore.js";
import {
  loadHeaderColors, loadHighlightColors, loadTableStyle, loadQuoteStyle,
} from "../appearanceStore.js";
import { loadTagColors } from "../tagColorStore.js";
import { useGlobalStore } from "../globalStore.js";
const globalStore = useGlobalStore();
import { ICON_LIBRARY, searchIcons } from "../IconLibrary.js";
import { TASK_ICONS } from "../taskIcons.js";
import { getTaskIcons, saveTaskIcons as apiSaveTaskIcons } from "../api.js";
import { loadTaskIcons } from "../taskIconStore.js";

// ── Tabs ──────────────────────────────────────────────────────────────────────
const tabs = [
  { id: "callouts",   label: "Callouts" },
  { id: "appearance", label: "Appearance" },
  { id: "advanced",   label: "Advanced" },
  { id: "tags",       label: "Tags" },
  { id: "taskicons",  label: "Task Icons" },
  { id: "prefs",      label: "Preferences" },
];
const activeTab = ref("callouts");

// ── Callouts ──────────────────────────────────────────────────────────────────
const editableCallouts = ref([]);
let _keyCounter = 0;
const calloutsaving = ref(false);
const calloutSaveMsg = ref("");
const calloutSaveOk = ref(true);

function previewStyle(c) {
  const rgb = hexToRgb(c.color || "#82D0D8");
  return {
    backgroundColor: `rgba(${rgb}, 0.12)`,
    color: c.color || "#82D0D8",
    borderLeft: `4px solid ${c.color || "#82D0D8"}`,
  };
}

function normalizeHex(val) {
  if (!val.startsWith("#")) val = "#" + val;
  return val.length <= 7 ? val : val.slice(0, 7);
}

function addCallout() {
  editableCallouts.value.push({
    _key: _keyCounter++,
    type: "custom",
    label: "Custom",
    color: "#82D0D8",
    icon: ICON_LIBRARY[0].path,
    builtin: false,
  });
}

function removeCallout(i) {
  editableCallouts.value.splice(i, 1);
}

async function saveCallouts() {
  calloutsaving.value = true;
  calloutSaveMsg.value = "";
  try {
    const payload = editableCallouts.value.map(({ _key, ...rest }) => rest);
    await apiSaveCallouts(payload);
    await loadCallouts(true);
    calloutSaveOk.value = true;
    calloutSaveMsg.value = "Saved ✓";
  } catch {
    calloutSaveOk.value = false;
    calloutSaveMsg.value = "Save failed";
  } finally {
    calloutsaving.value = false;
    setTimeout(() => { calloutSaveMsg.value = ""; }, 3000);
  }
}

// ── Header Colors ────────────────────────────────────────────────────────────
const editableHeaders = ref([]);
const headersSaving = ref(false);
const headersSaveMsg = ref("");
const headersSaveOk = ref(true);

// Global header colors toggle: true when at least one header is enabled.
// Setting it to false disables all; setting to true re-enables all.
const headersEnabled = computed({
  get() {
    return editableHeaders.value.some(h => h.enabled);
  },
  set(val) {
    editableHeaders.value.forEach(h => { h.enabled = val; });
  },
});

async function loadHeaders() {
  try {
    const data = await getHeaderColors();
    editableHeaders.value = data;
  } catch {
    editableHeaders.value = [
      { level: 1, color: "#ed7ea3", enabled: true },
      { level: 2, color: "#A3BE8C", enabled: true },
      { level: 3, color: "#66CCCC", enabled: true },
      { level: 4, color: "#95d5ea", enabled: true },
      { level: 5, color: "#999999", enabled: true },
      { level: 6, color: "#666666", enabled: true },
    ];
  }
}

async function saveHeaders() {
  headersSaving.value = true;
  headersSaveMsg.value = "";
  try {
    await saveHeaderColors(editableHeaders.value);
    await loadHeaderColors(true);
    headersSaveOk.value = true;
    headersSaveMsg.value = "Saved ✓";
  } catch {
    headersSaveOk.value = false;
    headersSaveMsg.value = "Save failed";
  } finally {
    headersSaving.value = false;
    setTimeout(() => { headersSaveMsg.value = ""; }, 3000);
  }
}

// ── Highlight Colors ─────────────────────────────────────────────────────────
const editableHighlights = ref([]);
const defaultHighlightName = ref("");
const defaultHighlightColor = ref("#ffffcc");
const highlightsSaving = ref(false);
const highlightsSaveMsg = ref("");
const highlightsSaveOk = ref(true);
let highlightKeyCounter = 100;

async function loadHighlights() {
  try {
    const data = await getHighlightColors();
    editableHighlights.value = data.map(h => ({ ...h, _key: h.isDefault ? h.name : highlightKeyCounter++ }));
    const defaultName = await getDefaultHighlight();
    defaultHighlightName.value = defaultName;
    const found = data.find(h => h.name === defaultName);
    defaultHighlightColor.value = found ? found.color : "#ffffcc";
  } catch {
    editableHighlights.value = [
      { name: "Red", color: "#ffcccc", enabled: true, isDefault: true, _key: "Red" },
      { name: "Yellow", color: "#ffffcc", enabled: true, isDefault: true, _key: "Yellow" },
      { name: "Green", color: "#ccffcc", enabled: true, isDefault: true, _key: "Green" },
      { name: "Blue", color: "#ccccff", enabled: true, isDefault: true, _key: "Blue" },
      { name: "Orange", color: "#ffddcc", enabled: true, isDefault: true, _key: "Orange" },
    ];
    defaultHighlightName.value = "Yellow";
    defaultHighlightColor.value = "#ffffcc";
  }
}

function addHighlightColor() {
  editableHighlights.value.push({
    _key: highlightKeyCounter++,
    name: "Custom",
    color: "#dddddd",
    enabled: true,
    isDefault: false,
  });
}

function removeHighlightColor(idx) {
  editableHighlights.value.splice(idx, 1);
}

function setDefaultHighlight(name) {
  defaultHighlightName.value = name;
  const found = editableHighlights.value.find(h => h.name === name);
  if (found) {
    defaultHighlightColor.value = found.color;
  }
}

async function saveHighlights() {
  highlightsSaving.value = true;
  highlightsSaveMsg.value = "";
  try {
    const payload = editableHighlights.value.map(({ _key, ...rest }) => rest);
    await saveHighlightColors(payload);
    await saveDefaultHighlight(defaultHighlightName.value);
    await loadHighlightColors(true);
    highlightsSaveOk.value = true;
    highlightsSaveMsg.value = "Saved ✓";
  } catch {
    highlightsSaveOk.value = false;
    highlightsSaveMsg.value = "Save failed";
  } finally {
    highlightsSaving.value = false;
    setTimeout(() => { highlightsSaveMsg.value = ""; }, 3000);
  }
}

// ── Table Style ──────────────────────────────────────────────────────────────
const tableStyle = ref({
  header_color: "#085294",
  zebra_striping: true,
  enabled: true,
});
const tableSaving = ref(false);
const tableSaveMsg = ref("");
const tableSaveOk = ref(true);

async function loadTableStyleSettings() {
  try {
    const data = await getTableStyle();
    tableStyle.value = data;
  } catch {
    // Keep defaults
  }
}

async function saveTableStyle() {
  tableSaving.value = true;
  tableSaveMsg.value = "";
  try {
    await apiSaveTableStyle(tableStyle.value);
    await loadTableStyle(true);
    tableSaveOk.value = true;
    tableSaveMsg.value = "Saved ✓";
  } catch {
    tableSaveOk.value = false;
    tableSaveMsg.value = "Save failed";
  } finally {
    tableSaving.value = false;
    setTimeout(() => { tableSaveMsg.value = ""; }, 3000);
  }
}

// ── Quote Style ──────────────────────────────────────────────────────────────
const quoteStyle = ref({
  border_color: "#006633",
  background_color: "#f9f9f9",
  dark_background_color: "rgba(0, 102, 51, 0.17)",
  enabled: true,
});

// ── Quote dark background: separate hex + opacity for the UI ─────────────────
// dark_background_color is stored as "rgba(r, g, b, a)" for CSS compatibility.
// The UI decomposes it into a 6-char hex + 0–100 opacity for the color picker.

function parseDarkBg() {
  const val = quoteStyle.value.dark_background_color || "rgba(0,102,51,0.17)";
  const m = val.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (m) {
    const r = parseInt(m[1]).toString(16).padStart(2, "0");
    const g = parseInt(m[2]).toString(16).padStart(2, "0");
    const b = parseInt(m[3]).toString(16).padStart(2, "0");
    const a = m[4] !== undefined ? Math.round(parseFloat(m[4]) * 100) : 100;
    return { hex: `#${r}${g}${b}`, opacity: a };
  }
  // Fallback: treat as 6-char hex with full opacity
  return { hex: val.startsWith("#") ? val.slice(0, 7) : "#006633", opacity: 17 };
}

function buildDarkBg(hex, opacityPct) {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  const a = Math.round(opacityPct) / 100;
  return `rgba(${r}, ${g}, ${b}, ${a.toFixed(2)})`;
}

const darkBgHex = computed({
  get() { return parseDarkBg().hex; },
  set(hex) {
    const { opacity } = parseDarkBg();
    quoteStyle.value.dark_background_color = buildDarkBg(hex, opacity);
  },
});
const darkBgOpacity = computed({
  get() { return parseDarkBg().opacity; },
  set(pct) {
    const { hex } = parseDarkBg();
    quoteStyle.value.dark_background_color = buildDarkBg(hex, pct);
  },
});
const quoteSaving = ref(false);
const quoteSaveMsg = ref("");
const quoteSaveOk = ref(true);

async function loadQuoteStyleSettings() {
  try {
    const data = await getQuoteStyle();
    quoteStyle.value = data;
  } catch {
    // Keep defaults
  }
}

async function saveQuoteStyle() {
  quoteSaving.value = true;
  quoteSaveMsg.value = "";
  try {
    await apiSaveQuoteStyle(quoteStyle.value);
    await loadQuoteStyle(true);
    quoteSaveOk.value = true;
    quoteSaveMsg.value = "Saved ✓";
  } catch {
    quoteSaveOk.value = false;
    quoteSaveMsg.value = "Save failed";
  } finally {
    quoteSaving.value = false;
    setTimeout(() => { quoteSaveMsg.value = ""; }, 3000);
  }
}

// ── Preferences ───────────────────────────────────────────────────────────────
const prefs = ref({ displayName: "", avatarFilename: null, notesDefaultSort: "", notesDefaultView: "", showButtonLabels: true });
const prefsSaving = ref(false);

// Keep globalStore in sync so buttons react instantly (no save needed for live preview)
watch(() => prefs.value.showButtonLabels, (val) => {
  globalStore.showButtonLabels = val;
}, { immediate: true });
const prefsSaveMsg = ref("");
const prefsSaveOk = ref(true);

const avatarUrl = computed(() => {
  if (!prefs.value.avatarFilename) return null;
  return `attachments/${prefs.value.avatarFilename}`;
});

async function uploadAvatar(e) {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const result = await createAttachment(file);
    prefs.value.avatarFilename = result.filename;
  } catch {
    alert("Upload failed");
  }
}

function removeAvatar() {
  prefs.value.avatarFilename = null;
}

async function savePrefs() {
  prefsSaving.value = true;
  prefsSaveMsg.value = "";
  try {
    const p = prefs.value;
    // Use explicit null coercion: only convert empty-string to null so the
    // backend treats it as "clear this field". Do NOT use `|| null` because
    // that converts any falsy value (including a valid "0" or false) to null
    // and — more critically — it means a display_name that was never set
    // arrives as null and overwrites a previously-saved name on re-save.
    const toNull = (v) => (v === "" || v === undefined) ? null : v;
    await apiSavePrefs({
      display_name:        toNull(p.displayName),
      avatar_filename:     toNull(p.avatarFilename),
      notes_default_sort:  toNull(p.notesDefaultSort),
      notes_default_view:  toNull(p.notesDefaultView),
      show_button_labels:  p.showButtonLabels,
    });
    prefsSaveOk.value = true;
    prefsSaveMsg.value = "Saved ✓";
  } catch {
    prefsSaveOk.value = false;
    prefsSaveMsg.value = "Save failed";
  } finally {
    prefsSaving.value = false;
    setTimeout(() => { prefsSaveMsg.value = ""; }, 3000);
  }
}

// Preview toggle state
const previewEnabled = ref(true);

function loadPreviewSetting() {
  const stored = localStorage.getItem("fn_preview_enabled");
  if (stored === null) {
    previewEnabled.value = true;
  } else {
    previewEnabled.value = stored === "true";
  }
}

function savePreviewSetting() {
  localStorage.setItem("fn_preview_enabled", String(previewEnabled.value));
}

// ── Icon picker ─────────────────────────────────────────────────────────────
const iconPickerOpen = ref(false);
const iconSearch = ref("");
let pickerTargetIndex = -1;

// Use the imported searchIcons function
const filteredIcons = computed(() => searchIcons(iconSearch.value));

function openIconPicker(index) {
  pickerTargetIndex = index;
  iconSearch.value = "";
  iconPickerOpen.value = true;
}

function pickIcon(icon) {
  if (pickerTargetIndex >= 0 && editableCallouts.value[pickerTargetIndex]) {
    editableCallouts.value[pickerTargetIndex].icon = icon.path;
  }
  iconPickerOpen.value = false;
}

// ── Tag Colors ───────────────────────────────────────────────────────────────
const tagColorsEnabled = ref(false);
const tagDefaultColor = ref("#006633");
const editableTagColors = ref([]); // [{ _key, tag, color, enabled }]
let _tagKeyCounter = 0;
const tagColorsSaving = ref(false);
const tagColorsSaveMsg = ref("");
const tagColorsSaveOk = ref(true);
// All tags fetched from the notes index (for the list)
const allTagsList = ref([]); // [{ tag, count }]
const tagColorsLoading = ref(false);

async function loadTagColorSettings() {
  tagColorsLoading.value = true;
  try {
    const data = await apiGetTagColors();
    tagColorsEnabled.value = data.custom_colors_enabled ?? false;
    tagDefaultColor.value = data.default_color ?? "#006633";
    editableTagColors.value = (data.tag_colors || []).map(t => ({
      ...t,
      _key: _tagKeyCounter++,
    }));
  } catch {
    tagColorsEnabled.value = false;
    tagDefaultColor.value = "#006633";
    editableTagColors.value = [];
  } finally {
    tagColorsLoading.value = false;
  }
}

async function loadAllTagsList() {
  try {
    const data = await getTags();
    // data is { tag: count } dict — filter out "pin" internal tag
    allTagsList.value = Object.entries(data)
      .filter(([t]) => t !== "pin")
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => a.tag.localeCompare(b.tag));
  } catch {
    allTagsList.value = [];
  }
}

function tagColorPreviewStyle(color) {
  // Mirror the exact chip style used across the app
  const hex = color || tagDefaultColor.value || "#006633";
  return {
    backgroundColor: hexToLightBg(hex),
    color: hex,
    border: `1px solid ${hex}44`,
    borderRadius: "9999px",
    padding: "0 0.5rem",
    fontSize: "0.8rem",
    fontWeight: "500",
    display: "inline-flex",
    alignItems: "center",
    gap: "0.25rem",
    lineHeight: "1.6",
  };
}

/** Convert hex to a 92%-lightness tint for chip backgrounds (mirrors tagColorLight). */
function hexToLightBg(hex) {
  try {
    const clean = hex.replace("#", "");
    const r = parseInt(clean.substring(0, 2), 16) / 255;
    const g = parseInt(clean.substring(2, 4), 16) / 255;
    const b = parseInt(clean.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    const d = max - min;
    let h = 0, s = 0;
    if (d) {
      s = (max + min) > 1 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
        case g: h = ((b - r) / d + 2) / 6; break;
        case b: h = ((r - g) / d + 4) / 6; break;
      }
    }
    return `hsl(${Math.round(h * 360)}, ${Math.round(s * 100)}%, 92%)`;
  } catch {
    return "#f0f0f0";
  }
}

function addTagColorRow(tag = "", color = "") {
  editableTagColors.value.push({
    _key: _tagKeyCounter++,
    tag: tag,
    color: color || tagDefaultColor.value || "#006633",
    enabled: true,
  });
}

function removeTagColorRow(i) {
  editableTagColors.value.splice(i, 1);
}

/** Add a row pre-filled for an existing tag (from the tag list). */
function addTagFromList(tag) {
  // Avoid duplicates
  const exists = editableTagColors.value.some(
    t => t.tag.toLowerCase() === tag.toLowerCase()
  );
  if (!exists) {
    addTagColorRow(tag);
  }
}

async function saveTagColors() {
  tagColorsSaving.value = true;
  tagColorsSaveMsg.value = "";
  try {
    const payload = {
      custom_colors_enabled: tagColorsEnabled.value,
      default_color: tagDefaultColor.value,
      tag_colors: editableTagColors.value
        .filter(t => t.tag.trim())
        .map(({ _key, ...rest }) => ({ ...rest, tag: rest.tag.trim() })),
    };
    await apiSaveTagColors(payload);
    await loadTagColors(true); // refresh shared store so chips update instantly
    tagColorsSaveOk.value = true;
    tagColorsSaveMsg.value = "Saved ✓";
  } catch {
    tagColorsSaveOk.value = false;
    tagColorsSaveMsg.value = "Save failed";
  } finally {
    tagColorsSaving.value = false;
    setTimeout(() => { tagColorsSaveMsg.value = ""; }, 3000);
  }
}


// ── Task Icons ────────────────────────────────────────────────────────────────
const taskIconsEnabled = ref(true);
const taskIconColors = ref(
  TASK_ICONS.map(icon => ({ marker: icon.marker, label: icon.label, iconPath: icon.iconPath, color: "#6B7280" }))
);
const taskIconsSaving = ref(false);
const taskIconsSaveMsg = ref("");
const taskIconsSaveOk = ref(true);

async function loadTaskIconSettings() {
  try {
    const data = await getTaskIcons();
    taskIconsEnabled.value = data.enabled ?? true;
    // Merge server colors into the full TASK_ICONS list so new markers get defaults
    taskIconColors.value = TASK_ICONS.map(icon => {
      const stored = (data.colors || []).find(c => c.marker === icon.marker);
      return {
        marker: icon.marker,
        label: icon.label,
        iconPath: icon.iconPath,
        color: stored?.color ?? "#6B7280",
      };
    });
  } catch {
    // keep defaults — server may not have any saved settings yet
  }
}

async function saveTaskIconSettings() {
  taskIconsSaving.value = true;
  taskIconsSaveMsg.value = "";
  try {
    const payload = {
      enabled: taskIconsEnabled.value,
      colors: taskIconColors.value.map(({ marker, color }) => ({ marker, color })),
    };
    await apiSaveTaskIcons(payload);
    // Refresh the shared store so ToastViewer picks up the new colors immediately
    await loadTaskIcons(true);
    taskIconsSaveOk.value = true;
    taskIconsSaveMsg.value = "Saved ✓";
  } catch {
    taskIconsSaveOk.value = false;
    taskIconsSaveMsg.value = "Save failed";
  } finally {
    taskIconsSaving.value = false;
    setTimeout(() => { taskIconsSaveMsg.value = ""; }, 3000);
  }
}

function resetTaskIconColor(marker) {
  const row = taskIconColors.value.find(r => r.marker === marker);
  if (row) row.color = "#6B7280";
}

function resetAllTaskIconColors() {
  taskIconColors.value.forEach(r => { r.color = "#6B7280"; });
}

// ── Load all data on mount ────────────────────────────────────────────────────
// ── Reactive dark-mode detection ─────────────────────────────────────────────
// Tracks body.dark class so previews auto-switch between themes.
const isDark = ref(document.body.classList.contains("dark"));
let _themeObserver = null;

onMounted(async () => {
  // Watch body class for dark/light theme switches
  _themeObserver = new MutationObserver(() => {
    isDark.value = document.body.classList.contains("dark");
  });
  _themeObserver.observe(document.body, { attributes: true, attributeFilter: ["class"] });

  loadPreviewSetting();
  loadTaskIconSettings();
  
  try {
    const data = await getCallouts();
    editableCallouts.value = data.map(c => ({ ...c, _key: _keyCounter++ }));
  } catch {
    editableCallouts.value = [];
  }
  await loadHeaders();
  await loadHighlights();
  await loadTableStyleSettings();
  await loadQuoteStyleSettings();
  try {
    const p = await getPrefs();
    prefs.value = {
      // Keep null as null — do NOT coerce to "" here.
      // The input placeholder handles the empty display; toNull() in savePrefs()
      // converts "" → null on save, so round-tripping null → "" → null works.
      // Coercing null → "" here then saving "" → null is fine, BUT coercing
      // a real saved value like "userA" → "userA" and then saving "userA" → "userA"
      // must also work — and it does. The only broken case was `|| null` in the
      // old savePrefs converting "" to null even when the field was intentionally blank.
      displayName:       p.display_name ?? "",
      avatarFilename:    p.avatar_filename ?? null,
      notesDefaultSort:  p.notes_default_sort ?? "",
      notesDefaultView:  p.notes_default_view ?? "",
      showButtonLabels:  p.show_button_labels !== false,
    };
  } catch {
    // defaults already set
  }
  await loadTagColorSettings();
  await loadAllTagsList();
});

onUnmounted(() => {
  if (_themeObserver) _themeObserver.disconnect();
});
</script>

<style scoped>
/* Hide scrollbar on tab bar while keeping it scrollable */
.scrollbar-none {
  scrollbar-width: none;
}
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
</style>