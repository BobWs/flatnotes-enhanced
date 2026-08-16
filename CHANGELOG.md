# Changelog

All notable changes to Flatnotes-Enhanced are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Multi-user support (stretch goal)
- Automatic database backup (more flexible scheduling)

---

## [1.13.1] - 2026-08-16

### Changed
- **Frontend dependencies** – Updated to latest stable versions:
  - `vue` → `3.5.40`
  - `vue-router` → `5.2.0`
  - `pinia` → `4.0.2`
  - `vite` → `8.2.0`
  - `axios` → `1.19.0`
  - `@toast-ui/editor` → `3.2.2`
  - And many more dev dependencies
- **Backend dependencies** – Updated to latest stable versions:
  - `fastapi` → `0.141.1`
  - `uvicorn` → `0.52.1`
  - `sqlalchemy` → `2.0.49`
  - `bcrypt` → `4.2.0`
  - And more
- **Build tooling** – Migrated from `pipenv` to `uv` for Python dependency management
- **Dockerfile** – Updated base images to `node:24-alpine` and `python:3.13-slim-trixie`
- **Python runtime** – Updated from 3.11 to 3.13

### Security
- Updated dependencies to address known vulnerabilities
- Pinned `bcrypt` version to resolve compatibility issues

### Technical
- Added `.python-version` and `uv.lock` for reproducible builds
- Updated `.dockerignore` to include new build files (`pyproject.toml`, `uv.lock`, `.python-version`)
- Docker build now uses `uv sync --locked` for deterministic installations

### Upgrading
- **No action required** – this release is backward compatible with existing configurations and data

---

## [1.13.0] - 2026-08-10

### Added
- **Shared Notes** – Full token-based note sharing feature
  - Share any note via secure link with read-only or edit permissions
  - Optional expiry (7/30/90 days or never)
  - Optional password protection (bcrypt-hashed)
  - Multiple share links per note
  - Activity tracking: view count and last-accessed time per link
  - Share modal shows all active links for the current note
  - Bulk revoke all links for a note
- **Shared Links Admin Page** (`/shares`)
  - Dedicated page accessible from NavBar
  - Lists all active share links across all notes, grouped by note
  - View token preview, permission, password indicator, view count, last accessed, expiry
  - Revoke individual links or revoke all per note
  - Empty state and refresh button
- **Visual indicators in Note view**
  - Share button turns orange with "Shared" label when note has active links
  - "Shared: {date}" timestamp appears in note footer
  - Timestamp uses app's date format and locale settings
- **Security**
  - Share routes excluded from PWA cache (NetworkOnly strategy) – revoked links never work from cache
  - Tokens stored as SHA-256 hashes only – raw tokens never persisted
  - Password protection with bcrypt hashing

### Changed
- `NavBar.vue`: Added "Shared Links" menu item (between Attachements and Archive, hidden in Showcase Mode)
- `router.js`: Added `/shared/:token` and `/shares` routes; `"shares"` added to `SHOWCASE_BLOCKED_ROUTES`

### Technical
- New `SharedNote` ORM model in `database.py`
- New API endpoints: `POST /api/share`, `GET /api/share/note/{title}`, `GET /api/share/{token}`, `DELETE /api/share/{token}`, `GET /api/shared/{token}/note`, `PATCH /api/shared/{token}/note`, `GET /api/shares`, `DELETE /api/shares/{hash}`, `DELETE /api/share/note/{title}/all`
- New client components: `SharedNote.vue`, `ShareModal.vue`, `Shares.vue`
- `api.js`: Full set of share-related API functions

---

## [1.12.1] - 2026-08-02

### Security
- **Critical:** Removed public TOTP QR code from login screen – `/api/totp-setup` endpoint now requires authentication
- TOTP QR code is now accessible only via **Settings → Preferences** after logging in
- This patch is a prerequisite for the upcoming **Shared Notes** feature to prevent external visitors from accessing TOTP setup

### Changed
- Login screen no longer displays "Show QR code for authenticator setup" button
- `/api/totp-setup` endpoint now returns 401 (Unauthorized) to unauthenticated callers
- TOTP setup modal moved to Settings → Preferences (visible only when `FLATNOTES_AUTH_TYPE=totp`)

### Technical
- `server/main.py`: Added `dependencies=auth_deps` to `GET /api/totp-setup`
- `client/views/LogIn.vue`: Removed TOTP QR code button and modal import
- `client/views/SettingsPrefs.vue`: Added TOTP QR code button in the avatar action column

---

## [1.12.0] - 2026-07-31

### Added
- **Hide Frontmatter in View & Preview** – Opt-in toggle to remove YAML/TOML metadata blocks from rendered notes
  - Supports both `---` (YAML) and `+++` (TOML) fence formats
  - Toggle in Settings → Preferences (default: OFF)
  - Strips frontmatter in both note view and preview popup
  - Preserves tags (`#pin`, `#archived`) placed above frontmatter
  - File on disk is never modified – purely a display filter
  - Preference stored in user settings database

### Technical
- New `client/frontmatter.js` – frontmatter detection and stripping utility
- New `client/frontmatterStore.js` – reactive singleton for preference state
- `stripFrontmatter` added to `UserPrefs` and `UserPrefsUpdate` models
- Applied to `ToastViewer.vue`, `NotePreview.vue`, and `ToastEditor.vue`
- JSON fallback path updated for database-less setups

### Known Limitation
- Collapsible frontmatter (Obsidian-style `▶ Frontmatter`) is not included in this release due to Toast UI Editor limitations. The hide toggle covers the primary use case for users syncing from external apps.

---

## [1.11.0] - 2026-07-22

### Added
- **Showcase Mode** – Public read-only presentation layer for sharing curated notes (`FLATNOTES_SEARCH_DISABLED=true`)
  - Disables search API (`/api/search` returns empty results)
  - Hides UI elements: search, new note, edit, delete, archive, trash, tags sidebar, bookmarks, templates, attachments, settings
  - Home page shows read-only banner instead of quick-access notes
  - Folder breadcrumbs render as plain text (no search navigation)
  - All other API endpoints remain functional (note retrieval, folder listing)
  - Direct note URLs (`/note/title`) still work

### Security
- Added warning that Showcase Mode is a UI restriction, not a security control
- Recommended to use with `FLATNOTES_AUTH_TYPE=read_only` for public instances

### Technical
- New environment variable: `FLATNOTES_SEARCH_DISABLED` (default: `false`)
- Backend: gated `/api/search` and `/api/tags` endpoints
- Backend: `search_disabled` field added to `/api/config` response
- Frontend: router `beforeEach` guard redirects blocked routes to home
- Frontend: hidden UI elements across NavBar, App, Note, FolderSidebar, and Home pages

### Known Limitation
- Showcase Mode does not protect API endpoints – use with `read_only` auth for public instances

---

## [1.10.0] - 2026-07-12

### Added
- **Saved Searches** – Save and reuse search queries with one click from the sidebar
  - Settings → Searches tab for managing saved searches (create, edit, delete, reorder)
  - Sidebar collapsible section below folders (opt-in via Preferences toggle)
  - Drag and drop to reorder saved searches
  - Active saved search highlighted in sidebar
- **Title Z–A Sort** – Sort by title in descending order (alphabetical Z to A)
  - Added to search results toolbar (toggle button)
  - Added to default note sort in Preferences
  - Added to saved search sort picker
  - Full round-trip support in FolderSidebar and saved search navigation
- **NavBar spacing reduction** – Bottom margin reduced from `48px` to `8px`, reclaiming `40px` of vertical space

### Changed
- Preferences tab redesigned into a balanced 5-row grid layout for cleaner organisation
- `constants.js` now includes `titleDesc: 3` as a sort option
- All sort dropdowns (search results, preferences, saved searches) include Title Z–A
- `SearchResults.vue` now displays a direction toggle button when Title sort is active

### Fixed
- Saved searches now correctly preserve sort direction when saved and re-run
- Folder sidebar active search highlighting now works with Title Z–A sort
- `SearchResults.vue` sort menu now correctly displays the active sort label for all four options
- **Tag Pollution** – Hex colors, port numbers, and config comments no longer appear as tags in the sidebar
  - Tag regex now requires an alphabetical starting character (`[a-zA-Z]`) – no more `#125d0d`, `#14496`, `#07072026` as tags
  - Code-block stripping now handles single and triple backticks separately (````.*?```|`[^`]*` ``) – code comments stay inside code blocks
  - Frontend `noteTags` computed property now strips code blocks and enforces alphabetical tag starts

### Known Limitation
- Numbered tags (e.g., `#456789`) are no longer supported. A preference option may be added in a future release if there's demand.

### Technical
- New `saved_searches` JSON column in `user_settings` table (schema migration via `_EXPECTED_COLUMNS`)
- Backend: `GET /api/settings/saved-searches` and `PUT /api/settings/saved-searches` endpoints
- Frontend: `SavedSearchModal.vue` and `SettingsSavedSearches.vue` components
- Drag-and-drop reordering uses native HTML5 Drag and Drop API
- `FolderSidebar.vue` now includes collapsible saved searches section with drag-to-reorder

---

## [1.9.0] - 2026-06-25

### Added
- **Customisable Date Formatting** – Users can now select preferred locale (language/region) and date style (Short/Medium/Long) in Settings → Preferences
- Live preview of date format when changing settings
- Date formatting now applies to all date displays across the app (search results, note lists, archive, trash, bookmarks, templates, maintenance tab, etc.)
- Memoised `Intl.DateTimeFormat` formatter with automatic store integration – `formatDate()` and `formatDateIso()` helpers

### Changed
- **Backend** – Added `date_locale` and `date_style` to `UserPrefs` and `UserPrefsUpdate` models; `get_prefs()` and `save_prefs()` now handle the new fields
- **Database** – Schema migration adds `date_locale` and `date_style` columns to `user_settings` table (idempotent via `_migrate_schema()`)
- **Frontend** – All date displays now use the `formatDate()` helper instead of pre-computed strings
- **`classes.js`** – `lastModifiedAsString` and `formatTimestamp()` now delegate to `dateFormatter.js`
- **`SettingsPrefs.vue`** – New "Date Format" section with locale dropdown (16 options), style dropdown, and live preview
- **`Templates.vue`** – Fixed pre-existing bug: sorting now uses raw `lastModified` timestamp instead of parsing formatted string
- **`NotePreview.vue`** – `created`/`updated` variables now formatted via `formatDateIso()` before being passed to `ToastViewer`

### Technical
- New `client/dateFormatter.js` – Memoised formatter with cache invalidation on preference save
- `clearDateFormatterCache()` called on save so new preferences take effect immediately without page reload
- `dateLocale` defaults to `'system'` (browser default); `dateStyle` defaults to `'medium'`
- Default behaviour unchanged until user sets preferences

### Fixed
- Templates page sorting now correctly uses raw timestamps (was parsing formatted date strings, causing incorrect sort order with non-default locales)

---

## [1.8.0] - 2026-06-21

### Added
- **Progressive Web App (PWA) support** – Install Flatnotes-Enhanced as a standalone app
- **Offline read-only caching** – Access previously viewed notes when server is unreachable
- **Server reachability detection** – Active polling every 15 seconds to detect offline state
- **Offline banner** – Subtle amber banner appears when server is unreachable
- **Toggle in Settings → Preferences** – Enable/disable offline caching (opt-in, default off)

### Changed
- Service worker registers unconditionally (required for installability), but API caching only when enabled

### Technical
- Uses `vite-plugin-pwa` with `injectManifest` mode
- Workbox runtime caching: NetworkFirst for API (3s timeout), CacheFirst for static assets
- Cache limits: 200 API responses, 100 assets
- Caches clear immediately when feature is disabled

---

## [1.7.2] - 2026-06-11

### Added
- Non-ASCII character support for usernames and passwords (umlauts, accented characters)

### Fixed
- Login no longer fails when passwords contain characters like `ä`, `ö`, `ü`, `ß`, `é`, `è`, `ç`, `ñ`
- Backend no longer crashes with `TypeError` when non-ASCII characters are used in credentials

--- 

## [1.7.1] - 2026-05-31

### Fixed
- Backup list now shows clearer date timestamps with file size and helpful tooltips
- Version check now uses Docker Hub API (primary) with GitHub fallback – more reliable, no more false "Offline" due to rate limits

---

## [1.7.0] - 2026-05-30

### Added
- **Redesigned Archive Page** – Search, sort, and filter archived notes (matching Attachments page design)
- **New Maintenance Tab** – Trash manager, content summary, and system info in a clean two-column layout
- **Preferences Backup & Restore System** – Automatic daily backups, manual backups, and restore with safety confirmation
- **Live Version Check** – Automatic update detection from Docker Hub (primary) and GitHub (fallback)
- **Three new API endpoints**: `GET /api/maintenance/status`, `POST /api/maintenance/trash/empty`, `GET /api/maintenance/backups`, `POST /api/maintenance/backups`, `POST /api/maintenance/backups/restore`, `DELETE /api/maintenance/backups/{filename}`

### Changed
- **Settings Page Refactor** – Split monolithic `Settings.vue` (~1800 lines) into dedicated components for faster loading and easier maintenance
- `FLATNOTES_TRASH_DAYS` environment variable is now surfaced in the Maintenance tab UI

### Fixed
- Archive page now matches Attachments page design consistency

---

## [1.6.3] - 2026-05-25

### Fixed
- **Sidebar expand/collapse** – Expand All now expands all nested folder and tag levels; individual expand/collapse works before AND after using Expand/Collapse All
- **Header colors/font** – H1–H6 now correctly respect user preferences; disabling headers reverts to default theme color and Poppins font

---

## [1.6.2] - 2026-05-24

### Fixed
- **Consistent default sorting** – All "All Notes" entry points (hamburger menu, home page `...`, search page) now respect saved sort preference from Settings → Preferences → Default note sort
- "App Default" option in Settings now saves and persists correctly

---

## [1.6.1] - 2026-05-21

### Fixed
- **Title truncation in editor header** – Long note titles now properly truncate with ellipsis (`…`); folder breadcrumb no longer competes with action buttons for space

---

## [1.6.0] - 2026-05-18

### Added
- **Note Views** – Three width options: Normal (999px), Wide (1400px), Full Screen, configurable in Settings → Preferences

---

## [1.5.1] - 2026-05-14

### Fixed
- **Case-insensitive attachment linking** – `![image](attachments/Photo.png)` now works even if the actual file is named `photo.png`
- **Archive folder scanning** – Archived notes now correctly mark attachments as "in use" on the Attachments page

---

## [1.5.0] - 2026-05-10

### Added
- **Wikilink Popup Modal** – Insert wikilinks using a searchable modal with real-time filtering and keyboard navigation
- **Wikilink rendering** – `[[Note Title]]` now renders as clickable links in the viewer

---

## [1.4.2] - 2026-05-09

### Fixed
- **Note switching while editing** – Switching to a different note while the editor was open no longer causes title mismatches, duplicate note errors, or broken editor state

---

## [1.4.1] - 2026-05-08

### Added
- **Attachment System Overhaul** – 40+ file types supported with proper icons and colours
- **Attachments Page Redesign** – Search, filter by usage (All/In use/Unused), sort by name/category/size/usage, and category badges

---

## [1.4.0] - 2026-05-04

### Added
- **Custom Home Note** – Set any note as your personal start page (Settings → Preferences). Home button, logo, and `Ctrl+Alt+H` all open your chosen note.
- **Preferences Tab Redesign** – Two-column layout for cleaner organisation

---

## [1.3.0] - 2026-05-03

### Added
- **Multi-Instance Support** – Run two or more Flatnotes-Enhanced instances on the same server without session bleed or cache conflicts. Each domain gets its own isolated authentication token.

---

## [1.2.0] - 2026-05-02

### Added
- **Button Label Toggle** – Show/hide text labels next to navigation buttons (Settings → Preferences). Hover tooltips provide context when labels are off.

### Fixed
- Button label preference now correctly restored on page load
- Dropdown menu items now show hover tooltips

---

## [1.1.0] - 2026-04-29

### Added
- **Duplicate Notes** – Copy one or more notes to any folder; originals remain untouched. Smart naming resolves conflicts automatically.
- **Bulk Delete** – Soft-delete multiple notes at once from the sidebar selection mode

---

## [1.0.2] - 2026-04-26

### Added
- **ARM64 Support** – Multi-arch Docker images now support `linux/amd64` and `linux/arm64` (Raspberry Pi, Apple Silicon)

---

## [1.0.1] - 2026-04-25

### Fixed
- Code block background colour in note popup preview for light theme

---

## [1.0.0] - 2026-04-12

### Added
- Initial release of Flatnotes-Enhanced
- Dual sidebars (folders and tags)
- Folder management with nested folders
- Tag system with nested tags and custom colors
- Note popup preview with eye icon
- Enhanced editor (custom highlights, search/replace, smart autocomplete)
- File attachments with PDF preview
- Trash and archive system
- Bookmarks (pin notes with `#pin`)
- Templates from `_templates` folder
- TOTP 2FA support
- SQLite database for user preferences
- Multi-arch Docker builds