# Changelog

All notable changes to Flatnotes-Enhanced are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Multi-user support (stretch goal)
- Automatic database backup (more flexible scheduling)

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