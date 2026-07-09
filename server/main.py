import os
from datetime import datetime, timezone
from typing import List, Literal

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import json
from pathlib import Path

def get_module_version() -> str:
    """Read version from package.json in the app root"""
    try:
        # Path: /app/server/main.py -> go up twice to /app/package.json
        package_json_path = Path(__file__).parent.parent / "package.json"
        with open(package_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("version", "unknown")
    except Exception as e:
        print(f"Warning: Could not read version from package.json: {e}")
        return "unknown"

MODULE_VERSION = get_module_version()


def format_bytes(n: int) -> str:
    """Return a human-readable byte size string (e.g. '2.1 MB')."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

# ── Version update check (Docker Hub primary → GitHub fallback) ───────────────
#
# Docker Hub tags API is unauthenticated, public, and has generous rate limits
# (metadata reads are not counted against pull quotas).  GitHub's unauthenticated
# API is limited to 60 req/hour per IP — shared across the whole host, so
# Synology/NAS users hit it quickly.  We therefore try Docker Hub first and only
# fall back to GitHub if Docker Hub fails.
#
# Both sources share the same 6-hour in-process cache so only one outbound HTTP
# request is made per server lifetime per TTL window.
import re as _re
import urllib.request as _urllib_request

_DOCKERHUB_TAGS_API = (
    "https://hub.docker.com/v2/repositories/dockerbobw/flatnotes-enhanced"
    "/tags?page_size=25&ordering=last_updated"
)
_GITHUB_RELEASES_API = (
    "https://api.github.com/repos/BobWs/flatnotes-enhanced/releases/latest"
)
_GITHUB_RELEASE_URL = "https://github.com/BobWs/flatnotes-enhanced/releases/latest"
_CACHE_TTL_HOURS    = 6

_update_cache: dict = {
    "latest_version": None,
    "release_url":    None,
    "published_at":   None,
    "checked_at":     None,
    "error":          None,
    "source":         None,   # "dockerhub" | "github" | None
}

# Semver pattern — only tags like "1.6.3" or "v1.6.3" (no arch suffixes etc.)
_SEMVER_RE = _re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def _semver_tuple(v: str):
    """Parse a version string into a comparable int tuple, or raise ValueError."""
    m = _SEMVER_RE.match(v.strip())
    if not m:
        raise ValueError(f"Not a semver tag: {v!r}")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _is_newer(latest: str, current: str) -> bool:
    """Return True if *latest* is strictly greater than *current*.

    Returns False on any parsing error so the UI never shows a false positive.
    """
    try:
        return _semver_tuple(latest) > _semver_tuple(current)
    except Exception:
        return False


def _fetch_url(url: str, extra_headers: dict | None = None) -> dict:
    """Fetch *url* and return parsed JSON.  Raises on HTTP error or timeout."""
    headers = {"User-Agent": f"flatnotes-enhanced/{MODULE_VERSION}"}
    if extra_headers:
        headers.update(extra_headers)
    req = _urllib_request.Request(url, headers=headers)
    with _urllib_request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def _latest_from_dockerhub() -> tuple[str, str | None]:
    """Return (version_string, release_url_or_None) from Docker Hub tags.

    Filters tags to semver-shaped ones only, picks the highest by tuple comparison.
    Raises on any failure so the caller can fall back.
    """
    data = _fetch_url(_DOCKERHUB_TAGS_API)
    results = data.get("results", [])
    candidates = []
    for tag in results:
        name = tag.get("name", "")
        try:
            tup = _semver_tuple(name)
            candidates.append((tup, name.lstrip("v")))
        except ValueError:
            pass  # skip "latest", "arm64", etc.

    if not candidates:
        raise ValueError("No semver tags found on Docker Hub")

    candidates.sort(reverse=True)
    best_version = candidates[0][1]
    # Link to the GitHub release page — Docker Hub doesn't have release notes
    return best_version, _GITHUB_RELEASE_URL


def _latest_from_github() -> tuple[str, str | None]:
    """Return (version_string, release_url_or_None) from GitHub Releases API.

    Raises on any failure (including rate-limit 403) so the caller can handle it.
    """
    data = _fetch_url(
        _GITHUB_RELEASES_API,
        extra_headers={"Accept": "application/vnd.github+json"},
    )
    # GitHub returns {"message": "API rate limit exceeded…"} with a 200-ish body
    # when rate-limited via some CDN paths, so check for that explicitly.
    if "message" in data and "rate limit" in data["message"].lower():
        raise RuntimeError(f"GitHub rate limit: {data['message']}")

    tag = data.get("tag_name", "").lstrip("v")
    if not tag:
        raise ValueError("GitHub response contained no tag_name")
    url = data.get("html_url") or _GITHUB_RELEASE_URL
    return tag, url


def get_latest_release() -> None:
    """Populate _update_cache with the latest available version.

    Strategy (never raises):
      1. Docker Hub tags API  — primary, generous rate limits
      2. GitHub Releases API  — fallback, 60 req/hr per IP
      3. Both fail            — cache["error"] is set, latest_version stays None

    A 6-hour TTL means at most one outbound request per TTL window regardless
    of how many users hit the status endpoint.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # ── TTL check ─────────────────────────────────────────────────────────────
    if _update_cache["checked_at"] is not None:
        try:
            last      = datetime.fromisoformat(_update_cache["checked_at"])
            age_hours = (now - last).total_seconds() / 3600
            if age_hours < _CACHE_TTL_HOURS:
                return          # still fresh — serve from cache
        except Exception:
            pass                # bad timestamp; fall through and re-fetch

    errors = []

    # ── 1. Docker Hub (primary) ───────────────────────────────────────────────
    try:
        version, url = _latest_from_dockerhub()
        _update_cache.update(
            latest_version=version,
            release_url=url,
            error=None,
            source="dockerhub",
        )
        _update_cache["checked_at"] = now.isoformat()
        return
    except Exception as exc:
        errors.append(f"DockerHub: {exc}")

    # ── 2. GitHub Releases (fallback) ─────────────────────────────────────────
    try:
        version, url = _latest_from_github()
        _update_cache.update(
            latest_version=version,
            release_url=url,
            error=None,
            source="github",
        )
        _update_cache["checked_at"] = now.isoformat()
        return
    except Exception as exc:
        errors.append(f"GitHub: {exc}")

    # ── Both failed ───────────────────────────────────────────────────────────
    _update_cache["error"]      = "; ".join(errors)
    _update_cache["source"]     = None
    _update_cache["checked_at"] = now.isoformat()
    # Leave latest_version / release_url unchanged so a previous good result
    # survives a transient network blip within the same server process.

import api_messages
from attachments.base import BaseAttachments
from attachments.models import AttachmentCreateResponse, AttachmentInfo
from auth.base import BaseAuth
from auth.models import Login, Token
from global_config import AuthType, GlobalConfig, GlobalConfigResponseModel
from helpers import replace_base_href
from notes.base import BaseNotes
from notes.models import Note, NoteCreate, NoteUpdate, SearchResult
from user_settings import (
    CalloutDefinition,
    UserPrefs,
    UserPrefsUpdate,
    get_callouts, save_callouts,
    get_prefs, save_prefs,
    HeaderColorDefinition, HighlightColorDefinition,
    TableStyleDefinition, QuoteStyleDefinition,
    get_header_colors, get_highlight_colors, get_default_highlight,
    get_tag_colors, save_tag_colors, TagColorSettings,
    get_table_style, get_quote_style,
    get_task_icons, save_task_icons, TaskIconSettings,
    save_maintenance_setting, get_maintenance_setting,
    get_saved_searches, save_saved_searches, SavedSearchSettings,
)
from typing import List as TypingList

from database import db_manager

# ── Startup backup (once per calendar day) ────────────────────────────────────
if db_manager.enabled:
    try:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        existing = db_manager.list_backups()
        has_today = any(b["created_at"][:10].replace("-", "") == today for b in existing)
        if not has_today:
            db_manager.create_backup("startup")
    except Exception as _be:
        pass  # non-fatal

global_config = GlobalConfig()
auth: BaseAuth = global_config.load_auth()
note_storage: BaseNotes = global_config.load_note_storage()
attachment_storage: BaseAttachments = global_config.load_attachment_storage()

_trash_days = global_config.trash_auto_delete_days
if _trash_days and _trash_days > 0:
    try:
        purged = note_storage.empty_old_trash(_trash_days)
        if purged:
            from logger import logger as _log
            _log.info(f"Auto-purged {len(purged)} note(s) from trash older than {_trash_days} days")
    except Exception as _e:
        pass
auth_deps = [Depends(auth.authenticate)] if auth else []
router = APIRouter()
app = FastAPI(
    docs_url=global_config.path_prefix + "/docs",
    openapi_url=global_config.path_prefix + "/openapi.json",
)
replace_base_href("client/dist/index.html", global_config.path_prefix)


# region UI
@router.get("/", include_in_schema=False)
@router.get("/login", include_in_schema=False)
@router.get("/search", include_in_schema=False)
@router.get("/new", include_in_schema=False)
@router.get("/trash", include_in_schema=False)
@router.get("/settings", include_in_schema=False)
@router.get("/attachments", include_in_schema=False)
@router.get("/note/{title:path}", include_in_schema=False)
def root(title: str = ""):
    with open("client/dist/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)
# endregion


# region Auth
if global_config.auth_type not in [AuthType.NONE, AuthType.READ_ONLY]:

    @router.post("/api/token", response_model=Token)
    def token(data: Login):
        try:
            return auth.login(data)
        except ValueError:
            raise HTTPException(status_code=401, detail=api_messages.login_failed)


@router.get("/api/totp-setup")
def totp_setup():
    if global_config.auth_type != AuthType.TOTP:
        raise HTTPException(status_code=404, detail="TOTP not enabled")
    data = auth.get_totp_setup_data()
    return data


@router.get("/api/auth-check", dependencies=auth_deps)
def auth_check() -> str:
    return "OK"
# endregion


# region Notes
@router.get("/api/notes/{title:path}", dependencies=auth_deps, response_model=Note)
def get_note(title: str):
    try:
        return note_storage.get(title)
    except ValueError:
        raise HTTPException(status_code=400, detail=api_messages.invalid_note_title)
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


if global_config.auth_type != AuthType.READ_ONLY:

    @router.post("/api/notes", dependencies=auth_deps, response_model=Note)
    def post_note(note: NoteCreate):
        try:
            return note_storage.create(note)
        except ValueError:
            raise HTTPException(status_code=400, detail=api_messages.invalid_note_title)
        except FileExistsError:
            raise HTTPException(status_code=409, detail=api_messages.note_exists)

    @router.patch("/api/notes/{title:path}", dependencies=auth_deps, response_model=Note)
    def patch_note(title: str, data: NoteUpdate):
        try:
            return note_storage.update(title, data)
        except ValueError:
            raise HTTPException(status_code=400, detail=api_messages.invalid_note_title)
        except FileExistsError:
            raise HTTPException(status_code=409, detail=api_messages.note_exists)
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)

    @router.delete("/api/notes/{title:path}", dependencies=auth_deps, response_model=None)
    def delete_note(title: str):
        try:
            note_storage.delete(title)
        except ValueError:
            raise HTTPException(status_code=400, detail=api_messages.invalid_note_title)
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)

    @router.post("/api/notes/{title:path}/archive", dependencies=auth_deps, response_model=Note)
    def archive_note(title: str):
        try:
            return note_storage.archive(title)
        except ValueError:
            raise HTTPException(400, api_messages.invalid_note_title)
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)
        except FileExistsError:
            raise HTTPException(409, api_messages.note_exists)

    @router.post("/api/notes/{title:path}/unarchive", dependencies=auth_deps, response_model=Note)
    def unarchive_note(title: str):
        try:
            return note_storage.unarchive(title)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)
        except FileExistsError:
            raise HTTPException(409, api_messages.note_exists)

    @router.post("/api/notes/{title:path}/pin", dependencies=auth_deps, response_model=Note)
    def pin_note(title: str):
        try:
            return note_storage.pin(title)
        except ValueError:
            raise HTTPException(400, api_messages.invalid_note_title)
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)

    @router.post("/api/notes/{title:path}/unpin", dependencies=auth_deps, response_model=Note)
    def unpin_note(title: str):
        try:
            return note_storage.unpin(title)
        except ValueError:
            raise HTTPException(400, api_messages.invalid_note_title)
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)

    @router.post("/api/trash/{title:path}/restore", dependencies=auth_deps, response_model=Note)
    def restore_note(title: str):
        if not title.startswith("_trash/"):
            title = f"_trash/{title}"
        try:
            return note_storage.restore_from_trash(title)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)
        except FileExistsError:
            raise HTTPException(409, api_messages.note_exists)

    @router.delete("/api/trash/{title:path}", dependencies=auth_deps, response_model=None)
    def permanent_delete_note(title: str):
        if not title.startswith("_trash/"):
            title = f"_trash/{title}"
        try:
            note_storage.permanently_delete(title)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)
# endregion


@router.get("/api/templates", dependencies=auth_deps)
def get_templates():
    try:
        templates = note_storage.get_notes_in_folder("_templates")
        return [t.replace("_templates/", "") for t in templates]
    except Exception:
        return []


@router.delete("/api/archive/{title:path}", dependencies=auth_deps, response_model=None)
def permanent_delete_archived_note(title: str):
    if not title.startswith("_archive/"):
        title = f"_archive/{title}"
    try:
        note_storage.permanently_delete_archived(title)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


# region Search
@router.get("/api/search", dependencies=auth_deps, response_model=List[SearchResult])
def search(
    term: str,
    sort: Literal["score", "title", "lastModified"] = "score",
    order: Literal["asc", "desc"] = "desc",
    limit: int = None,
    include_archived: bool = False,
    include_trash: bool = False,
):
    if sort == "lastModified":
        sort = "last_modified"
    return note_storage.search(
        term, sort=sort, order=order, limit=limit,
        include_archived=include_archived,
        include_trash=include_trash,
    )


@router.get("/api/tags", dependencies=auth_deps)
def get_tags(include_archived: bool = False):
    return note_storage.get_tags(include_archived=include_archived)


@router.get("/api/folders", dependencies=auth_deps)
def get_folders():
    return note_storage.get_folders()
# endregion


@router.get("/api/folders/{folder:path}/notes", dependencies=auth_deps)
def get_folder_notes(folder: str):
    return note_storage.get_notes_in_folder(folder)


# region Config
@router.get("/api/config", response_model=GlobalConfigResponseModel)
def get_config():
    return GlobalConfigResponseModel(
        auth_type=global_config.auth_type,
        quick_access_hide=global_config.quick_access_hide,
        quick_access_title=global_config.quick_access_title,
        quick_access_term=global_config.quick_access_term,
        quick_access_sort=global_config.quick_access_sort,
        quick_access_limit=global_config.quick_access_limit,
    )
# endregion


# region Attachments
@router.get("/api/attachments/{filename}", dependencies=auth_deps)
@router.get("/attachments/{filename}", dependencies=auth_deps, include_in_schema=False)
def get_attachment(filename: str):
    try:
        return attachment_storage.get(filename)
    except ValueError:
        raise HTTPException(status_code=400, detail=api_messages.invalid_attachment_filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=api_messages.attachment_not_found)


@router.get("/api/attachments", dependencies=auth_deps)
def list_attachments():
    return [a.dict() for a in attachment_storage.list_all()]


if global_config.auth_type != AuthType.READ_ONLY:

    @router.post("/api/attachments", dependencies=auth_deps, response_model=AttachmentCreateResponse)
    def post_attachment(file: UploadFile):
        try:
            return attachment_storage.create(file)
        except ValueError:
            raise HTTPException(status_code=400, detail=api_messages.invalid_attachment_filename)
        except FileExistsError:
            raise HTTPException(409, api_messages.attachment_exists)

    @router.delete("/api/attachments/{filename}", dependencies=auth_deps, response_model=None)
    def delete_attachment(filename: str):
        try:
            attachment_storage.delete(filename)
        except ValueError:
            raise HTTPException(400, api_messages.invalid_attachment_filename)
        except FileNotFoundError:
            raise HTTPException(404, api_messages.attachment_not_found)
# endregion


# region Settings

@router.get("/api/settings/callouts", dependencies=auth_deps)
def api_get_callouts():
    return [c.dict() for c in get_callouts()]


@router.put("/api/settings/callouts", dependencies=auth_deps)
def api_save_callouts(callouts: TypingList[CalloutDefinition]):
    try:
        save_callouts(callouts)
    except Exception as e:
        raise HTTPException(500, str(e))
    return [c.dict() for c in get_callouts()]


@router.get("/api/settings/prefs", dependencies=auth_deps)
def api_get_prefs():
    return get_prefs().dict()


@router.put("/api/settings/prefs", dependencies=auth_deps)
def api_save_prefs(prefs: UserPrefsUpdate):
    try:
        save_prefs(prefs)
    except Exception as e:
        raise HTTPException(500, str(e))
    return get_prefs().dict()


# ── Header colors ─────────────────────────────────────────────────────────────

@router.get("/api/settings/header-colors", dependencies=auth_deps)
def api_get_header_colors():
    return [c.dict() for c in get_header_colors()]


@router.put("/api/settings/header-colors", dependencies=auth_deps)
def api_save_header_colors(colors: List[HeaderColorDefinition]):
    try:
        save_prefs(UserPrefsUpdate(header_colors=colors))
        return [c.dict() for c in get_header_colors()]
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Highlight colors ──────────────────────────────────────────────────────────

@router.get("/api/settings/highlight-colors", dependencies=auth_deps)
def api_get_highlight_colors():
    return [c.dict() for c in get_highlight_colors()]


@router.put("/api/settings/highlight-colors", dependencies=auth_deps)
def api_save_highlight_colors(colors: List[HighlightColorDefinition]):
    try:
        save_prefs(UserPrefsUpdate(highlight_colors=colors))
        return [c.dict() for c in get_highlight_colors()]
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Default highlight ─────────────────────────────────────────────────────────

@router.get("/api/settings/default-highlight", dependencies=auth_deps)
def api_get_default_highlight():
    return {"default": get_default_highlight()}


@router.put("/api/settings/default-highlight", dependencies=auth_deps)
def api_save_default_highlight(data: dict):
    try:
        save_prefs(UserPrefsUpdate(default_highlight=data.get("default")))
        return {"default": get_default_highlight()}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Table style ───────────────────────────────────────────────────────────────

@router.get("/api/settings/table-style", dependencies=auth_deps)
def api_get_table_style():
    return get_table_style().dict()


@router.put("/api/settings/table-style", dependencies=auth_deps)
def api_save_table_style(style: TableStyleDefinition):
    try:
        save_prefs(UserPrefsUpdate(table_style=style))
        return get_table_style().dict()
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Quote style ───────────────────────────────────────────────────────────────

@router.get("/api/settings/quote-style", dependencies=auth_deps)
def api_get_quote_style():
    return get_quote_style().dict()


@router.put("/api/settings/quote-style", dependencies=auth_deps)
def api_save_quote_style(style: QuoteStyleDefinition):
    try:
        save_prefs(UserPrefsUpdate(quote_style=style))
        return get_quote_style().dict()
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Tag colors ────────────────────────────────────────────────────────────────

@router.get("/api/settings/tag-colors", dependencies=auth_deps)
def api_get_tag_colors():
    return get_tag_colors().dict()


@router.put("/api/settings/tag-colors", dependencies=auth_deps)
def api_save_tag_colors(tag_colors: TagColorSettings):
    try:
        save_tag_colors(tag_colors)
        return get_tag_colors().dict()
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Task icons ────────────────────────────────────────────────────────────────

@router.get("/api/settings/task-icons", dependencies=auth_deps)
def api_get_task_icons():
    """Return task icon settings (enabled flag + per-marker colors)."""
    return get_task_icons().dict()


@router.put("/api/settings/task-icons", dependencies=auth_deps)
def api_save_task_icons(task_icons: TaskIconSettings):
    """Save task icon settings.

    Sole owner of the task_icons column — no other endpoint writes it.
    """
    try:
        save_task_icons(task_icons)
        return get_task_icons().dict()
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Saved Searches ────────────────────────────────────────────────────────────

@router.get("/api/settings/saved-searches", dependencies=auth_deps)
def api_get_saved_searches():
    """Return saved search settings (enabled flag + searches list)."""
    return get_saved_searches().dict()


@router.put("/api/settings/saved-searches", dependencies=auth_deps)
def api_save_saved_searches(saved_searches: SavedSearchSettings):
    """Save saved search settings (full list replace).

    Sole owner of the saved_searches column.
    """
    try:
        save_saved_searches(saved_searches)
        return get_saved_searches().dict()
    except Exception as e:
        raise HTTPException(500, str(e))


# endregion


# region Maintenance

@router.get("/api/maintenance/backups", dependencies=auth_deps)
def list_backups():
    """List all available preference backups, newest first."""
    return db_manager.list_backups()


@router.post("/api/maintenance/backups", dependencies=auth_deps)
def create_backup(body: dict = Body(default={})):
    """Create a manual backup of the settings database."""
    label = str(body.get("label", "manual"))[:32] or "manual"
    try:
        return db_manager.create_backup(label)
    except Exception as exc:
        raise HTTPException(500, f"Backup failed: {exc}")


@router.post("/api/maintenance/backups/restore", dependencies=auth_deps)
def restore_backup(body: dict = Body(default={})):
    """Restore a backup. Automatically creates a pre-restore safety backup first."""
    filename = body.get("filename", "")
    try:
        return db_manager.restore_backup(filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Restore failed: {exc}")


@router.delete("/api/maintenance/backups/{filename}", dependencies=auth_deps)
def delete_backup(filename: str):
    """Permanently delete a single backup file."""
    import re as _re
    if not _re.match(r"^flatnotes_backup_[a-zA-Z0-9_-]+_\d{8}_\d{6}\.db$", filename):
        raise HTTPException(400, "Invalid backup filename")
    path = os.path.join(db_manager.BACKUP_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Backup not found")
    try:
        os.remove(path)
        return {"success": True, "filename": filename}
    except Exception as exc:
        raise HTTPException(500, f"Delete failed: {exc}")


@router.get("/api/maintenance/status", dependencies=auth_deps)
def maintenance_status():
    """Return a summary of application state for the Maintenance tab."""
    # ── DB size ───────────────────────────────────────────────────────────────
    db_path = db_manager.db_path if db_manager.enabled else None
    try:
        db_size_bytes = os.path.getsize(db_path) if db_path and os.path.exists(db_path) else 0
    except Exception:
        db_size_bytes = 0

    # ── Note counts (single search, filter client-side) ───────────────────────
    try:
        all_results = note_storage.search(
            "*",
            sort="title",
            order="asc",
            limit=None,
            include_archived=True,
            include_trash=True,
        )
        note_count     = sum(1 for r in all_results if not r.title.startswith("_trash/") and not r.title.startswith("_archive/"))
        trash_count    = sum(1 for r in all_results if r.title.startswith("_trash/"))
        archive_count  = sum(1 for r in all_results if r.title.startswith("_archive/"))
    except Exception:
        note_count = trash_count = archive_count = 0

    # ── Attachment count ──────────────────────────────────────────────────────
    try:
        attachment_count = len(attachment_storage.list_all())
    except Exception:
        attachment_count = 0

    # ── Trash auto-delete config ──────────────────────────────────────────────
    trash_days = global_config.trash_auto_delete_days or None

    # ── Last cleanup timestamp ────────────────────────────────────────────────
    last_cleanup = get_maintenance_setting("last_trash_cleanup", None)

    # ── Update check (non-blocking; uses 6-hour cache) ────────────────────────
    get_latest_release()
    _lv = _update_cache["latest_version"]

    return {
        "version":               MODULE_VERSION,
        "db_path":               db_path,
        "db_size_bytes":         db_size_bytes,
        "db_size_human":         format_bytes(db_size_bytes),
        "note_count":            note_count,
        "trash_count":           trash_count,
        "archive_count":         archive_count,
        "attachment_count":      attachment_count,
        "trash_auto_delete_days": trash_days,
        "last_trash_cleanup":    last_cleanup,
        # update-check fields
        "latest_version":        _lv,
        "update_available":      _is_newer(_lv, MODULE_VERSION) if _lv else False,
        "release_url":           _update_cache["release_url"],
        "update_checked_at":     _update_cache["checked_at"],
        "update_check_error":    _update_cache["error"],
        "update_check_source":   _update_cache["source"],   # "dockerhub"|"github"|None
    }


@router.post("/api/maintenance/trash/empty", dependencies=auth_deps)
def maintenance_empty_trash(body: dict = Body(default={})):
    """Empty all or part of the trash.

    Body: {"days": <int>}
      days = 0  → delete ALL trash items regardless of age
      days > 0  → delete items older than *days* days (delegates to empty_old_trash)
    """
    days = int(body.get("days", 0))

    try:
        if days == 0:
            # Delete every note currently in _trash/
            all_results = note_storage.search(
                "*",
                sort="title",
                order="asc",
                limit=None,
                include_archived=False,
                include_trash=True,
            )
            trash_titles = [r.title for r in all_results if r.title.startswith("_trash/")]
            deleted = []
            for title in trash_titles:
                try:
                    note_storage.permanently_delete(title)
                    deleted.append(title)
                except Exception:
                    pass
        else:
            deleted = note_storage.empty_old_trash(days)
    except Exception as exc:
        raise HTTPException(500, f"Trash empty failed: {exc}")

    # Persist timestamp
    ts = datetime.now(timezone.utc).isoformat()
    save_maintenance_setting("last_trash_cleanup", ts)

    return {
        "deleted_count":  len(deleted),
        "deleted_titles": deleted,
        "timestamp":      ts,
    }

# endregion



@router.get("/health")
def healthcheck() -> str:
    return "OK"
# endregion

app.include_router(router, prefix=global_config.path_prefix)
app.mount(
    global_config.path_prefix,
    StaticFiles(directory="client/dist"),
    name="dist",
)