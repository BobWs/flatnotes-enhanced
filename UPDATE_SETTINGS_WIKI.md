# Update Instructions for Settings & Customization Wiki

This file contains the new Maintenance section to add to the Settings & Customization wiki page.

## New Section to Add After "Preferences Tab"

Add this section right after the "Preferences Tab" section in Settings-&-Customization.md

---

## 🔧 Maintenance Tab

The Maintenance tab provides system information, backup management, and trash cleanup tools to keep your Flatnotes-Enhanced instance running smoothly.

### Trash Manager

Manage notes in the trash and configure automatic cleanup.

#### Viewing Trash Status

- **In trash**: Shows how many notes are currently in your trash
- **Auto-delete**: Displays the automatic cleanup interval (e.g., "Every 7 days") or "Manual only" if not configured
- **Last cleaned**: When trash was last automatically cleaned

#### Configuring Auto-Delete

Auto-delete is configured via the `FLATNOTES_TRASH_DAYS` environment variable:

```bash
# Delete trash older than 7 days automatically
FLATNOTES_TRASH_DAYS=7

# Disable auto-delete (manual only)
# (Don't set the variable)
```

#### Emptying Trash Manually

1. Click **"Empty trash now"** button
2. Enter the number of days: 
   - **0** = Delete all notes in trash immediately
   - **7** = Delete only notes older than 7 days
3. Click **"Confirm"**
4. The operation is permanent

### Content Summary

Quick overview of your note collection:

| Metric | Description |
|--------|---|
| **Notes** | Total active notes (excluding archive/trash) |
| **Archive** | Notes in the _archive folder |
| **Trash** | Notes in the _trash folder |
| **Attachments** | Total file attachments in your system |

These numbers update when you click **"Refresh"**.

### About & System Info

Three-column information display:

**App Version**
- Current version of Flatnotes-Enhanced
- **Update status**:
  - **Offline** - Never checked for updates (no internet connection)
  - **Up to date** - You have the latest version
  - **Update available** - Newer version available
- View release notes link (when update available)
- Last checked timestamp (when up to date)

**Database**
- Size of your SQLite database
- Database file path
- Shows "Not configured" if database is disabled

**Project**
- Flatnotes-Enhanced project information
- Built with ❤️ by the community

---

## 💾 Preferences Backup & Restore

Automatically backup and restore your settings and preferences. **Notes are not affected** by backup/restore operations—they're stored as Markdown files.

### What Gets Backed Up?

✅ **Backed up:**
- All Settings (callouts, colors, headers, etc.)
- Preferences (display name, avatar, theme, etc.)
- Tag colors and customizations
- Task icon colors
- Home note configuration

❌ **NOT backed up:**
- Your notes (stored as .md files)
- Attachments (stored separately)
- Trash/Archive (not included in settings)

### Creating a Backup

**Automatic Backups:**
- Created every midnight automatically
- Created on server startup
- Oldest backups are automatically deleted (keep most recent 7 by default)

**Manual Backup:**
1. Click **"Backup now"** button
2. New backup is created immediately
3. Appears in the backup list below

### Backup Retention

Configure how many backups to keep:

1. Enter the number of backups to retain (1-30)
2. Setting saves automatically
3. Oldest backups are deleted when limit is exceeded

Default: **7 backups**

### Restoring from Backup

⚠️ **Warning**: Restore is permanent. A safety backup is created automatically before restoring.

1. Find the backup in the list
2. Click **"Restore"** button
3. Type **"RESTORE"** to confirm (safety measure)
4. Click **"Confirm Restore"**
5. Preferences are restored
6. **Reload the page** to apply restored preferences

### Backup File Format

Each backup contains:
- **Filename**: Auto-generated (e.g., `backup_20240115_143022.json`)
- **Size**: How much space the backup takes
- **Date**: When the backup was created
- **Label**: Type of backup:
  - **daily** - Automatic midnight backup
  - **startup** - Created on server startup
  - **manual** - Created by clicking "Backup now"

### Managing Backups

**Preview a Backup:**
- View the date and size in the list
- Click "Restore" to see what's inside (before confirming)

**Download a Backup:**
- Backups are stored server-side
- Can be exported manually if needed (advanced)

**Delete Old Backups:**
1. Click **"Delete"** on any backup
2. Confirm deletion
3. Backup is permanently removed

### Backup Best Practices

✅ **Do this:**
- Let automatic backups run (create daily backups)
- Keep 5-7 backups for safety
- Test restore on non-critical instances first
- Create manual backup before major changes

❌ **Avoid this:**
- Deleting all backups (keep at least 2-3)
- Restoring from unknown/old backups without testing
- Assuming backups include your notes (they don't)

### Troubleshooting Backups

**Backups Not Creating**
- Check server disk space (backups need room)
- Verify database is enabled in settings
- Check server logs for errors

**Restore Failed**
- Backup file may be corrupted
- Try another backup from the list
- Check that restore confirmation text was typed correctly

**Restored Settings Not Appearing**
- Must reload the page after restore
- Check browser console for errors
- Try restore again from a different backup

---

## Version Check

Flatnotes-Enhanced automatically checks for updates when the Maintenance page loads.

### Update Status

**Offline**
- Server can't reach GitHub (no internet connection)
- Click **"Refresh"** to check again

**Up to date**
- You have the latest version
- Shows when version was last checked

**Update available**
- Newer version is available on GitHub
- Click **"View release notes"** to see what's new
- Follow the upgrade instructions for your setup (Docker/Manual)

### Checking for Updates Manually

1. Click **"Refresh"** button at top-right of Maintenance page
2. System checks GitHub for latest version
3. Status updates with results

---

## Two-Column Layout

The Maintenance tab uses a responsive two-column design:

- **Desktop (wide screens)**: Side-by-side layout shows Trash Manager + Content Summary
- **Mobile (narrow screens)**: Stacks vertically for easier reading
- All sections responsive and touch-friendly

---

## See Also

- [Getting Started & Installation](Getting-Started-&-Installation) - Initial setup
- [Settings & Customization](Settings-&-Customization) - Other customization tabs
- [Note Management](Note-Management) - Trash and archive features
