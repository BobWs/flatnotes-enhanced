"""
user_settings.py — backend for user-configurable settings.

Uses SQLite database for storage with JSON file fallback.
"""
import json
import os
from typing import List, Optional

from pydantic import Field
from helpers import CustomBaseModel, get_env
from logger import logger

from database import db_manager, UserSettings, CalloutConfig, User


# ── Pydantic models ───────────────────────────────────────────────────────────

class CalloutDefinition(CustomBaseModel):
    type: str
    label: str
    color: str
    icon: str
    builtin: bool = False


class HeaderColorDefinition(CustomBaseModel):
    level: int
    color: str
    enabled: bool = True


class HighlightColorDefinition(CustomBaseModel):
    name: str
    color: str
    enabled: bool = True
    isDefault: bool = False


class TableStyleDefinition(CustomBaseModel):
    header_color: str = Field(default="#085294")
    zebra_striping: bool = Field(default=True)
    enabled: bool = Field(default=True)


class QuoteStyleDefinition(CustomBaseModel):
    border_color: str = Field(default="#006633")
    background_color: str = Field(default="#f9f9f9")
    dark_background_color: str = Field(default="rgba(0, 102, 51, 0.17)")
    enabled: bool = Field(default=True)


class TagColorDefinition(CustomBaseModel):
    tag: str
    color: str
    enabled: bool = True


class TagColorSettings(CustomBaseModel):
    custom_colors_enabled: bool = Field(default=False)
    default_color: str = Field(default="#006633")
    tag_colors: List[TagColorDefinition] = Field(default_factory=list)


class TaskIconColorDefinition(CustomBaseModel):
    """Color override for a single task icon marker."""
    marker: str          # e.g. "?", "!", "*"
    color: str           # hex e.g. "#6B7280"


class TaskIconSettings(CustomBaseModel):
    """Task icon feature settings."""
    enabled: bool = Field(default=True)
    colors: List[TaskIconColorDefinition] = Field(default_factory=list)


class UserPrefs(CustomBaseModel):
    display_name: Optional[str] = Field(None)
    avatar_filename: Optional[str] = Field(None)
    notes_default_sort: Optional[str] = Field(None)
    notes_default_view: Optional[str] = Field(None)
    header_colors: List[HeaderColorDefinition] = Field(default_factory=list)
    highlight_colors: List[HighlightColorDefinition] = Field(default_factory=list)
    default_highlight: Optional[str] = Field(None)
    table_style: TableStyleDefinition = Field(default_factory=TableStyleDefinition)
    quote_style: QuoteStyleDefinition = Field(default_factory=QuoteStyleDefinition)
    tag_colors: TagColorSettings = Field(default_factory=TagColorSettings)


class UserPrefsUpdate(CustomBaseModel):
    """Payload for PUT /api/settings/prefs — excludes tag_colors and task_icons."""
    display_name: Optional[str] = Field(None)
    avatar_filename: Optional[str] = Field(None)
    notes_default_sort: Optional[str] = Field(None)
    notes_default_view: Optional[str] = Field(None)
    header_colors: Optional[List[HeaderColorDefinition]] = Field(None)
    highlight_colors: Optional[List[HighlightColorDefinition]] = Field(None)
    default_highlight: Optional[str] = Field(None)
    table_style: Optional[TableStyleDefinition] = Field(None)
    quote_style: Optional[QuoteStyleDefinition] = Field(None)


# ── Built-in defaults ─────────────────────────────────────────────────────────

BUILTIN_CALLOUTS: List[CalloutDefinition] = [
    CalloutDefinition(type="note",    label="Note",    color="#82D0D8",
        icon="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2Z", builtin=True),
    CalloutDefinition(type="info",    label="Info",    color="#337AB7",
        icon="M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z", builtin=True),
    CalloutDefinition(type="warning", label="Warning", color="#E69800",
        icon="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z", builtin=True),
    CalloutDefinition(type="danger",  label="Danger",  color="#DC3545",
        icon="M12,2C17.53,2 22,6.47 22,12C22,17.53 17.53,22 12,22C6.47,22 2,17.53 2,12C2,6.47 6.47,12 12,2M15.59,7L12,10.59L8.41,7L7,8.41L10.59,12L7,15.59L8.41,17L12,13.41L15.59,17L17,15.59L13.41,12L17,8.41L15.59,7Z", builtin=True),
    CalloutDefinition(type="success", label="Success", color="#28A745",
        icon="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,16.5L18,9.5L16.59,8.09L11,13.67L7.41,10.09L6,11.5L11,16.5Z", builtin=True),
]

DEFAULT_HEADER_COLORS: List[HeaderColorDefinition] = [
    HeaderColorDefinition(level=1, color="#ed7ea3", enabled=True),
    HeaderColorDefinition(level=2, color="#A3BE8C", enabled=True),
    HeaderColorDefinition(level=3, color="#66CCCC", enabled=True),
    HeaderColorDefinition(level=4, color="#95d5ea", enabled=True),
    HeaderColorDefinition(level=5, color="#999999", enabled=True),
    HeaderColorDefinition(level=6, color="#666666", enabled=True),
]

DEFAULT_HIGHLIGHT_COLORS: List[HighlightColorDefinition] = [
    HighlightColorDefinition(name="Red",     color="#ffcccc", enabled=True, isDefault=True),
    HighlightColorDefinition(name="Yellow",  color="#ffffcc", enabled=True, isDefault=True),
    HighlightColorDefinition(name="Green",   color="#ccffcc", enabled=True, isDefault=True),
    HighlightColorDefinition(name="Blue",    color="#ccccff", enabled=True, isDefault=True),
    HighlightColorDefinition(name="Orange",  color="#ffddcc", enabled=True, isDefault=True),
]


# ── JSON file paths (for fallback) ───────────────────────────────────────────

def _storage_path() -> str:
    return get_env("FLATNOTES_PATH", mandatory=True)

def _flatnotes_dir() -> str:
    path = os.path.join(_storage_path(), ".flatnotes")
    os.makedirs(path, exist_ok=True)
    return path

def _callouts_path() -> str:
    return os.path.join(_flatnotes_dir(), "callouts.json")

def _prefs_path() -> str:
    return os.path.join(_flatnotes_dir(), "user_prefs.json")

def _tag_colors_path() -> str:
    return os.path.join(_flatnotes_dir(), "tag_colors.json")

def _task_icons_path() -> str:
    return os.path.join(_flatnotes_dir(), "task_icons.json")


def _resolve_json_path(primary: str) -> str:
    if os.path.exists(primary):
        return primary
    bak = primary + ".bak"
    if os.path.exists(bak):
        logger.info(f"Primary JSON not found, using backup: {bak}")
        return bak
    return primary


# ── Database helpers ──────────────────────────────────────────────────────────

def _get_user_id() -> int:
    return db_manager.get_default_user_id()


def _dict_to_header_colors(data: list) -> List[HeaderColorDefinition]:
    if not data:
        return DEFAULT_HEADER_COLORS
    try:
        return [HeaderColorDefinition(**item) for item in data]
    except Exception:
        return DEFAULT_HEADER_COLORS


def _dict_to_highlight_colors(data: list) -> List[HighlightColorDefinition]:
    if not data:
        return DEFAULT_HIGHLIGHT_COLORS
    try:
        return [HighlightColorDefinition(**item) for item in data]
    except Exception:
        return DEFAULT_HIGHLIGHT_COLORS


def _dict_to_table_style(data: dict) -> TableStyleDefinition:
    if not data:
        return TableStyleDefinition()
    try:
        return TableStyleDefinition(**data)
    except Exception:
        return TableStyleDefinition()


def _dict_to_quote_style(data: dict) -> QuoteStyleDefinition:
    if not data:
        return QuoteStyleDefinition()
    try:
        return QuoteStyleDefinition(**data)
    except Exception:
        return QuoteStyleDefinition()


def _dict_to_tag_colors(data: dict) -> TagColorSettings:
    if not data:
        return TagColorSettings()
    try:
        return TagColorSettings(**data)
    except Exception:
        return TagColorSettings()


def _dict_to_task_icons(data: dict) -> TaskIconSettings:
    if not data:
        return TaskIconSettings()
    try:
        return TaskIconSettings(**data)
    except Exception:
        return TaskIconSettings()


# ── Callout CRUD (Database-first) ─────────────────────────────────────────────

def get_callouts() -> List[CalloutDefinition]:
    callouts = {c.type: c for c in BUILTIN_CALLOUTS}

    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            user_callouts = db.query(CalloutConfig).filter(
                (CalloutConfig.user_id == user_id) | (CalloutConfig.user_id.is_(None))
            ).all()
            for c in user_callouts:
                callouts[c.callout_type] = CalloutDefinition(
                    type=c.callout_type, label=c.label,
                    color=c.color, icon=c.icon, builtin=c.builtin
                )
            return list(callouts.values())
        except Exception as e:
            logger.error(f"Database error in get_callouts: {e}")
        finally:
            db.close()

    user_callouts = []
    path = _resolve_json_path(_callouts_path())
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            user_callouts = [CalloutDefinition(**c) for c in raw]
        except Exception as e:
            logger.error(f"Failed to load callouts.json: {e}")

    for c in user_callouts:
        callouts[c.type] = c
    return list(callouts.values())


def save_callouts(callouts: List[CalloutDefinition]) -> None:
    user_only = [c for c in callouts if not c.builtin]

    if db_manager.enabled:
        db = db_manager.get_session()
        if db is not None:
            try:
                user_id = _get_user_id()
                incoming_types = {c.type for c in user_only}

                db.query(CalloutConfig).filter(
                    CalloutConfig.user_id == user_id,
                    CalloutConfig.callout_type.notin_(incoming_types),
                ).delete(synchronize_session="fetch")

                for c in user_only:
                    existing = db.query(CalloutConfig).filter(
                        CalloutConfig.user_id      == user_id,
                        CalloutConfig.callout_type == c.type,
                    ).first()
                    if existing:
                        existing.label   = c.label
                        existing.color   = c.color
                        existing.icon    = c.icon
                        existing.builtin = False
                    else:
                        db.add(CalloutConfig(
                            user_id=user_id, callout_type=c.type,
                            label=c.label, color=c.color, icon=c.icon,
                            builtin=False, is_enabled=True,
                        ))

                db.commit()
                logger.info(f"Saved {len(user_only)} callouts to database")
                return
            except Exception as exc:
                logger.error(f"Database error in save_callouts: {exc}")
                db.rollback()
            finally:
                db.close()

    with open(_callouts_path(), "w", encoding="utf-8") as f:
        json.dump([c.dict() for c in user_only], f, indent=2)
    logger.info(f"Saved {len(user_only)} callouts to JSON")


# ── User preferences (Database-first) ─────────────────────────────────────────

def get_prefs() -> UserPrefs:
    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if settings:
                return UserPrefs(
                    display_name=settings.display_name,
                    avatar_filename=settings.avatar_filename,
                    notes_default_sort=settings.notes_default_sort,
                    notes_default_view=settings.notes_default_view,
                    header_colors=_dict_to_header_colors(settings.header_colors),
                    highlight_colors=_dict_to_highlight_colors(settings.highlight_colors),
                    default_highlight=settings.default_highlight,
                    table_style=_dict_to_table_style(settings.table_style),
                    quote_style=_dict_to_quote_style(settings.quote_style),
                    tag_colors=_dict_to_tag_colors(settings.tag_colors or {}),
                )
        except Exception as e:
            logger.error(f"Database error in get_prefs: {e}")
        finally:
            db.close()

    path = _resolve_json_path(_prefs_path())
    prefs = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                prefs = UserPrefs(**json.load(f))
        except Exception as e:
            logger.error(f"Failed to load user_prefs.json: {e}")

    if prefs is None:
        prefs = UserPrefs()
    if not prefs.header_colors:
        prefs.header_colors = DEFAULT_HEADER_COLORS
    if not prefs.highlight_colors:
        prefs.highlight_colors = DEFAULT_HIGHLIGHT_COLORS
    return prefs


def save_prefs(prefs: UserPrefsUpdate) -> None:
    """Save account/appearance preferences.
    Does NOT touch tag_colors or task_icons — those have their own endpoints.
    """
    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if not settings:
                settings = UserSettings(user_id=user_id)
                db.add(settings)

            if prefs.display_name is not None:
                settings.display_name = prefs.display_name
            if prefs.avatar_filename is not None:
                settings.avatar_filename = prefs.avatar_filename
            if prefs.notes_default_sort is not None:
                settings.notes_default_sort = prefs.notes_default_sort
            if prefs.notes_default_view is not None:
                settings.notes_default_view = prefs.notes_default_view

            if prefs.header_colors is not None:
                settings.header_colors = [c.dict() for c in prefs.header_colors]
            if prefs.highlight_colors is not None:
                settings.highlight_colors = [c.dict() for c in prefs.highlight_colors]
            if prefs.default_highlight is not None:
                settings.default_highlight = prefs.default_highlight
            if prefs.table_style is not None:
                settings.table_style = dict(prefs.table_style.dict())
            if prefs.quote_style is not None:
                settings.quote_style = dict(prefs.quote_style.dict())

            db.commit()
            logger.info("Saved preferences to database")
            return
        except Exception as e:
            logger.error(f"Database error in save_prefs: {e}")
            db.rollback()
        finally:
            db.close()

    existing = get_prefs()
    merged = UserPrefs(
        display_name=prefs.display_name if prefs.display_name is not None else existing.display_name,
        avatar_filename=prefs.avatar_filename if prefs.avatar_filename is not None else existing.avatar_filename,
        notes_default_sort=prefs.notes_default_sort if prefs.notes_default_sort is not None else existing.notes_default_sort,
        notes_default_view=prefs.notes_default_view if prefs.notes_default_view is not None else existing.notes_default_view,
        header_colors=prefs.header_colors if prefs.header_colors is not None else existing.header_colors,
        highlight_colors=prefs.highlight_colors if prefs.highlight_colors is not None else existing.highlight_colors,
        default_highlight=prefs.default_highlight if prefs.default_highlight is not None else existing.default_highlight,
        table_style=prefs.table_style if prefs.table_style is not None else existing.table_style,
        quote_style=prefs.quote_style if prefs.quote_style is not None else existing.quote_style,
        tag_colors=existing.tag_colors,
    )
    with open(_prefs_path(), "w", encoding="utf-8") as f:
        json.dump(merged.dict(), f, indent=2)
    logger.info("Saved preferences to JSON")


# ── Convenience functions ─────────────────────────────────────────────────────

def get_header_colors() -> List[HeaderColorDefinition]:
    return get_prefs().header_colors

def get_highlight_colors() -> List[HighlightColorDefinition]:
    return get_prefs().highlight_colors

def get_default_highlight() -> str:
    prefs = get_prefs()
    if prefs.default_highlight:
        return prefs.default_highlight
    for hc in prefs.highlight_colors:
        if hc.enabled:
            return hc.name
    return "Yellow"

def get_table_style() -> TableStyleDefinition:
    return get_prefs().table_style

def get_quote_style() -> QuoteStyleDefinition:
    return get_prefs().quote_style


def get_tag_colors() -> TagColorSettings:
    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if settings:
                return _dict_to_tag_colors(settings.tag_colors or {})
        except Exception as e:
            logger.error(f"Database error in get_tag_colors: {e}")
        finally:
            db.close()

    path = _resolve_json_path(_tag_colors_path())
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _dict_to_tag_colors(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load tag_colors.json: {e}")
    return TagColorSettings()


def save_tag_colors(tag_colors: TagColorSettings) -> None:
    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if not settings:
                settings = UserSettings(user_id=user_id)
                db.add(settings)
            settings.tag_colors = dict(tag_colors.dict())
            db.commit()
            logger.info("Saved tag colors to database")
            return
        except Exception as e:
            logger.error(f"Database error in save_tag_colors: {e}")
            db.rollback()
        finally:
            db.close()

    with open(_tag_colors_path(), "w", encoding="utf-8") as f:
        json.dump(tag_colors.dict(), f, indent=2)
    logger.info("Saved tag colors to JSON")


# ── Task Icons (Database-first) ───────────────────────────────────────────────

def get_task_icons() -> TaskIconSettings:
    """Return task icon settings — DB first, then JSON fallback."""
    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if settings:
                return _dict_to_task_icons(settings.task_icons or {})
        except Exception as e:
            logger.error(f"Database error in get_task_icons: {e}")
        finally:
            db.close()

    path = _resolve_json_path(_task_icons_path())
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _dict_to_task_icons(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load task_icons.json: {e}")
    return TaskIconSettings()


def save_task_icons(task_icons: TaskIconSettings) -> None:
    """Persist task icon settings — DB first, JSON fallback."""
    if db_manager.enabled:
        db = db_manager.get_session()
        try:
            user_id = _get_user_id()
            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if not settings:
                settings = UserSettings(user_id=user_id)
                db.add(settings)
            # Assign a fresh dict so SQLAlchemy marks the column dirty
            settings.task_icons = dict(task_icons.dict())
            db.commit()
            logger.info("Saved task icons to database")
            return
        except Exception as e:
            logger.error(f"Database error in save_task_icons: {e}")
            db.rollback()
        finally:
            db.close()

    with open(_task_icons_path(), "w", encoding="utf-8") as f:
        json.dump(task_icons.dict(), f, indent=2)
    logger.info("Saved task icons to JSON")
