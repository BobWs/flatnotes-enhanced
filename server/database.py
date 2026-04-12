"""
database.py — SQLite database setup and models for user settings.

Robustness guarantees
─────────────────────
• Every session opened is closed in a `finally` block — no leaks.
• Schema migration is idempotent: `create_all` handles missing tables;
  `_migrate_schema` handles missing columns on existing tables.
• JSON-to-DB migration is split into two independent transactions
  (settings, callouts) so a failure in one never rolls back the other.
• Each callout INSERT is individually guarded with an existence check,
  so re-running on an already-populated database is always safe
  (no UNIQUE constraint errors).
• `_ensure_default_user` looks up by username, not just "first row",
  so it survives schema changes that cleared the users table.
• `get_default_user_id` always closes its session in a finally block.
"""
import json
import os
import shutil
from typing import Optional

from sqlalchemy import (
    create_engine, text,
    Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func

from helpers import get_env
from logger import logger

Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────────

class User(Base):
    """User account (single-user now, multi-user ready)."""
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True)
    username   = Column(String, unique=True, nullable=False, default="default")
    email      = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active  = Column(Boolean, default=True)
    is_admin   = Column(Boolean, default=False)

    settings = relationship("UserSettings", back_populates="user", uselist=False)
    callouts = relationship("CalloutConfig", back_populates="user")


class UserSettings(Base):
    """User preferences (theme, editor, styling, colours)."""
    __tablename__ = "user_settings"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Basic
    display_name       = Column(String,  nullable=True)
    avatar_filename    = Column(String,  nullable=True)
    notes_default_sort = Column(String,  nullable=True)
    notes_default_view = Column(String,  nullable=True)

    # Appearance
    theme       = Column(String,  default="light")
    font_size   = Column(String,  default="medium")
    font_family = Column(String,  default="Poppins")

    # Editor
    default_editor_mode = Column(String,  default="wysiwyg")
    line_numbers        = Column(Boolean, default=False)
    auto_save           = Column(Boolean, default=True)

    # JSON columns
    header_colors     = Column(JSON, default=list)
    highlight_colors  = Column(JSON, default=list)
    default_highlight = Column(String, default="Yellow")
    table_style       = Column(JSON, default=dict)
    quote_style       = Column(JSON, default=dict)
    tag_colors        = Column(JSON, default=dict)
    task_icons        = Column(JSON, default=dict)   # ← NEW
    extra             = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="settings")


class CalloutConfig(Base):
    """User-defined callout configurations."""
    __tablename__ = "callout_configs"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    callout_type = Column(String,  nullable=False)
    label        = Column(String,  nullable=False)
    color        = Column(String,  nullable=False)
    icon         = Column(String,  nullable=False)
    builtin      = Column(Boolean, default=False)
    is_enabled   = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="callouts")

    __table_args__ = (
        UniqueConstraint("user_id", "callout_type", name="unique_user_callout"),
    )


# ── DatabaseManager ───────────────────────────────────────────────────────────

class DatabaseManager:
    """Manages database connection and provides session management."""

    # Columns expected in `user_settings` → DDL type string.
    # Used by _migrate_schema to backfill columns missing from older DB files.
    _EXPECTED_COLUMNS = {
        "user_settings": {
            "id":                   "INTEGER",
            "user_id":              "INTEGER",
            "display_name":         "VARCHAR",
            "avatar_filename":      "VARCHAR",
            "notes_default_sort":   "VARCHAR",
            "notes_default_view":   "VARCHAR",
            "theme":                "VARCHAR",
            "font_size":            "VARCHAR",
            "font_family":          "VARCHAR",
            "default_editor_mode":  "VARCHAR",
            "line_numbers":         "BOOLEAN",
            "auto_save":            "BOOLEAN",
            "header_colors":        "JSON",
            "highlight_colors":     "JSON",
            "default_highlight":    "VARCHAR",
            "table_style":          "JSON",
            "quote_style":          "JSON",
            "tag_colors":           "JSON",
            "task_icons":           "JSON",   # ← NEW
            "extra":                "JSON",
            "created_at":           "DATETIME",
            "updated_at":           "DATETIME",
        },
    }

    def __init__(self) -> None:
        _notes_path  = os.getenv("FLATNOTES_PATH", "/data")
        _default_db  = os.path.join(_notes_path, ".flatnotes", "flatnotes.db")
        self.db_path      = os.getenv("DATABASE_PATH", _default_db)
        self.enabled      = os.getenv("ENABLE_DATABASE", "true").lower() == "true"
        self.engine       = None
        self.SessionLocal = None

        if self.enabled:
            self._init_database()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_database(self) -> None:
        """Initialise connection, create/migrate schema, seed default data."""
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                connect_args={"check_same_thread": False},
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            )

            # Create tables that don't yet exist (never drops, never alters).
            Base.metadata.create_all(bind=self.engine)

            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            # Backfill columns added after the initial schema was deployed.
            self._migrate_schema()

            # Ensure the default user row exists (idempotent).
            self._ensure_default_user()

            # Import legacy JSON files — each step is its own transaction.
            self._migrate_settings_if_needed()
            self._migrate_callouts_if_needed()

            logger.info(f"Database initialized at {self.db_path}")

        except Exception as exc:
            logger.error(f"Failed to initialize database: {exc}")
            logger.warning("Falling back to JSON file storage")
            self.enabled      = False
            self.engine       = None
            self.SessionLocal = None

    def _migrate_schema(self) -> None:
        """Add columns that are defined in the ORM but missing from the live DB."""
        if self.engine is None:
            return

        with self.engine.connect() as conn:
            for table, columns in self._EXPECTED_COLUMNS.items():
                result   = conn.execute(text(f"PRAGMA table_info({table})"))
                existing = {row[1] for row in result}

                for col_name, col_type in columns.items():
                    if col_name not in existing:
                        try:
                            conn.execute(
                                text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                            )
                            conn.commit()
                            logger.info(f"Schema migration: added {table}.{col_name}")
                        except Exception as exc:
                            logger.warning(
                                f"Schema migration: could not add {table}.{col_name}: {exc}"
                            )

    def _ensure_default_user(self) -> None:
        """Create the default user if it doesn't already exist."""
        db = self.get_session()
        if db is None:
            return
        try:
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                user = User(username="default", is_admin=True, is_active=True)
                db.add(user)
                db.commit()
                logger.info("Created default user")
        except Exception as exc:
            logger.error(f"Failed to create default user: {exc}")
            db.rollback()
        finally:
            db.close()

    # ── JSON migration helpers ─────────────────────────────────────────────────

    def _pick_json(self, flatnotes_dir: str, name: str) -> str:
        primary = os.path.join(flatnotes_dir, name)
        bak     = primary + ".bak"
        if os.path.exists(primary):
            return primary
        if os.path.exists(bak):
            logger.info(f"Migration: primary file missing, using backup: {bak}")
            return bak
        return primary

    def _migrate_settings_if_needed(self) -> None:
        """Import user_prefs.json + tag_colors.json + task_icons.json → user_settings row."""
        db = self.get_session()
        if db is None:
            return
        try:
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                return

            if db.query(UserSettings).filter(UserSettings.user_id == user.id).first():
                return

            storage_path  = get_env("FLATNOTES_PATH", mandatory=True)
            flatnotes_dir = os.path.join(storage_path, ".flatnotes")

            prefs_path       = self._pick_json(flatnotes_dir, "user_prefs.json")
            tag_colors_path  = self._pick_json(flatnotes_dir, "tag_colors.json")
            task_icons_path  = self._pick_json(flatnotes_dir, "task_icons.json")

            prefs_data       = {}
            tag_colors_data  = {}
            task_icons_data  = {}

            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, "r", encoding="utf-8") as fh:
                        prefs_data = json.load(fh)
                    logger.info(f"Loaded preferences from {prefs_path}")
                except Exception as exc:
                    logger.error(f"Failed to read user_prefs.json: {exc}")

            tag_colors_data = prefs_data.get("tag_colors", {})
            if not tag_colors_data and os.path.exists(tag_colors_path):
                try:
                    with open(tag_colors_path, "r", encoding="utf-8") as fh:
                        tag_colors_data = json.load(fh)
                    logger.info(f"Loaded tag colours from {tag_colors_path}")
                except Exception as exc:
                    logger.error(f"Failed to read tag_colors.json: {exc}")

            if os.path.exists(task_icons_path):
                try:
                    with open(task_icons_path, "r", encoding="utf-8") as fh:
                        task_icons_data = json.load(fh)
                    logger.info(f"Loaded task icons from {task_icons_path}")
                except Exception as exc:
                    logger.error(f"Failed to read task_icons.json: {exc}")

            settings = UserSettings(
                user_id=user.id,
                display_name=prefs_data.get("display_name"),
                avatar_filename=prefs_data.get("avatar_filename"),
                notes_default_sort=prefs_data.get("notes_default_sort"),
                notes_default_view=prefs_data.get("notes_default_view"),
                header_colors=prefs_data.get("header_colors", []),
                highlight_colors=prefs_data.get("highlight_colors", []),
                default_highlight=prefs_data.get("default_highlight", "Yellow"),
                table_style=prefs_data.get("table_style", {}),
                quote_style=prefs_data.get("quote_style", {}),
                tag_colors=tag_colors_data,
                task_icons=task_icons_data,
            )
            db.add(settings)
            db.commit()
            logger.info("Migrated user preferences from JSON to database")

            for json_path in (prefs_path, tag_colors_path, task_icons_path):
                if os.path.exists(json_path):
                    try:
                        shutil.copy2(json_path, json_path + ".bak")
                    except Exception as exc:
                        logger.warning(f"Could not back up {json_path}: {exc}")

        except Exception as exc:
            logger.error(f"Settings migration failed: {exc}")
            db.rollback()
        finally:
            db.close()

    def _migrate_callouts_if_needed(self) -> None:
        """Import callouts.json → callout_configs rows (idempotent)."""
        db = self.get_session()
        if db is None:
            return
        try:
            user = db.query(User).filter(User.username == "default").first()
            if not user:
                return

            storage_path  = get_env("FLATNOTES_PATH", mandatory=True)
            flatnotes_dir = os.path.join(storage_path, ".flatnotes")
            callouts_path = self._pick_json(flatnotes_dir, "callouts.json")

            if not os.path.exists(callouts_path):
                return

            try:
                with open(callouts_path, "r", encoding="utf-8") as fh:
                    callouts_data = json.load(fh)
                logger.info(f"Loaded callouts from {callouts_path}")
            except Exception as exc:
                logger.error(f"Failed to read callouts.json: {exc}")
                return

            inserted = 0
            skipped  = 0

            for callout in callouts_data:
                if callout.get("builtin", False):
                    skipped += 1
                    continue

                callout_type = callout.get("type")
                if not callout_type:
                    logger.warning("Skipping callout entry with missing 'type' field")
                    skipped += 1
                    continue

                exists = db.query(CalloutConfig).filter(
                    CalloutConfig.user_id      == user.id,
                    CalloutConfig.callout_type == callout_type,
                ).first()

                if exists:
                    skipped += 1
                    continue

                db.add(CalloutConfig(
                    user_id=user.id,
                    callout_type=callout_type,
                    label=callout.get("label", callout_type),
                    color=callout.get("color", "#82D0D8"),
                    icon=callout.get("icon", ""),
                    builtin=False,
                    is_enabled=True,
                ))
                inserted += 1

            db.commit()
            logger.info(f"Callout migration: {inserted} inserted, {skipped} skipped")

            try:
                shutil.copy2(callouts_path, callouts_path + ".bak")
            except Exception as exc:
                logger.warning(f"Could not back up {callouts_path}: {exc}")

        except Exception as exc:
            logger.error(f"Callout migration failed: {exc}")
            db.rollback()
        finally:
            db.close()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_session(self) -> Optional[Session]:
        if not self.enabled or self.SessionLocal is None:
            return None
        return self.SessionLocal()

    def get_default_user_id(self) -> int:
        if not self.enabled:
            return 1

        db = self.get_session()
        if db is None:
            return 1
        try:
            user = db.query(User).filter(User.username == "default").first()
            return user.id if user else 1
        except Exception:
            return 1
        finally:
            db.close()


# ── Global singleton ──────────────────────────────────────────────────────────
db_manager = DatabaseManager()
