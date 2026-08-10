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
import re
import hashlib
import secrets
import shutil
from datetime import datetime, timezone
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

try:
    from passlib.context import CryptContext as _CryptContext
    from passlib.exc import MissingBackendError
    
    # Try bcrypt first, fallback to pbkdf2_sha256 if it fails
    _pwd_context = None
    _HAS_BCRYPT = False
    
    try:
        # Test with a simple hash
        test_ctx = _CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)
        test_ctx.hash("test")
        _pwd_context = test_ctx
        _HAS_BCRYPT = True
    except Exception as e:
        print(f"bcrypt unavailable ({e}), using pbkdf2_sha256")
        _pwd_context = _CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    
    def _hash_password(pw: str) -> str:
        # bcrypt has a 72-byte limit
        if _HAS_BCRYPT:
            pw_bytes = pw.encode('utf-8')
            if len(pw_bytes) > 72:
                pw = pw_bytes[:72].decode('utf-8', errors='ignore')
        return _pwd_context.hash(pw)
    
    def _verify_password(pw: str, hashed: str) -> bool:
        try:
            # bcrypt has a 72-byte limit
            if hashed.startswith(('$2a$', '$2b$', '$2y$')):
                pw_bytes = pw.encode('utf-8')
                if len(pw_bytes) > 72:
                    pw = pw_bytes[:72].decode('utf-8', errors='ignore')
            return _pwd_context.verify(pw, hashed)
        except Exception:
            # Ultimate fallback
            return hashlib.sha256(pw.encode()).hexdigest() == hashed
except Exception:
    import hashlib as _hashlib
    def _hash_password(pw: str) -> str:
        return _hashlib.sha256(pw.encode()).hexdigest()
    def _verify_password(pw: str, hashed: str) -> bool:
        return _hashlib.sha256(pw.encode()).hexdigest() == hashed

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
    task_icons        = Column(JSON, default=dict)
    saved_searches    = Column(JSON, default=dict)   # ← saved searches blob {enabled, searches:[]}
    extra             = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="settings")


class SharedNote(Base):
    """Per-note share tokens for Shared Notes feature."""
    __tablename__ = "shared_notes"

    id              = Column(String, primary_key=True)   # SHA-256 hash of raw token
    token_preview   = Column(String, nullable=False)     # first 6 chars of raw token
    note_title      = Column(String, nullable=False)
    permission      = Column(String, nullable=False)     # "read" | "write"
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    expires_at      = Column(DateTime(timezone=True), nullable=True)
    is_active       = Column(Boolean, default=True)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count    = Column(Integer, default=0)
    password_hash   = Column(String, nullable=True)   # bcrypt hash; None = no password


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
        "shared_notes": {
            "password_hash": "VARCHAR",
        },
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
            "saved_searches":       "JSON",
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

    # ── Backup / Restore ──────────────────────────────────────────────────────

    _BACKUP_FILENAME_RE = re.compile(
        r"^flatnotes_backup_([a-zA-Z0-9_-]+)_(\d{8}_\d{6})\.db$"
    )

    @property
    def BACKUP_DIR(self) -> str:
        return os.path.join(os.path.dirname(self.db_path), "backups")

    def _format_bytes(self, n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if abs(n) < 1024.0:
                return f"{n:.1f} {unit}"
            n /= 1024.0
        return f"{n:.1f} TB"

    def _get_retain_count(self) -> int:
        """Read backup_retain_count from UserSettings.extra, defaulting to 7."""
        db = self.get_session()
        if db is None:
            return 7
        try:
            settings = db.query(UserSettings).join(User).filter(
                User.username == "default"
            ).first()
            if settings and settings.extra:
                return int(settings.extra.get("backup_retain_count", 7))
        except Exception:
            pass
        finally:
            db.close()
        return 7

    def create_backup(self, label: str = "auto") -> dict:
        """Copy the current DB file to backups/ with a timestamped filename.

        Returns a dict with filename, path, size_bytes, and created_at.
        Prunes old backups afterwards to respect retain_count.
        Raises RuntimeError if the database is not enabled or the file is missing.
        """
        if not self.enabled:
            raise RuntimeError("Database is not enabled")
        if not os.path.exists(self.db_path):
            raise RuntimeError(f"Database file not found: {self.db_path}")

        # Sanitise label — alphanumerics, hyphens, underscores only
        safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", label)[:32] or "auto"

        os.makedirs(self.BACKUP_DIR, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"flatnotes_backup_{safe_label}_{ts}.db"
        dest_path = os.path.join(self.BACKUP_DIR, filename)

        shutil.copy2(self.db_path, dest_path)
        size = os.path.getsize(dest_path)
        logger.info(f"Backup created: {filename} ({self._format_bytes(size)})")

        self._prune_old_backups(self._get_retain_count())

        return {
            "filename":   filename,
            "path":       dest_path,
            "size_bytes": size,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _prune_old_backups(self, retain_count: int) -> None:
        """Delete oldest backups until only retain_count files remain."""
        if not os.path.isdir(self.BACKUP_DIR):
            return
        backups = [
            f for f in os.listdir(self.BACKUP_DIR)
            if self._BACKUP_FILENAME_RE.match(f)
        ]
        if len(backups) <= retain_count:
            return
        # Sort by mtime ascending (oldest first)
        backups.sort(key=lambda f: os.path.getmtime(os.path.join(self.BACKUP_DIR, f)))
        to_delete = backups[:len(backups) - retain_count]
        for fname in to_delete:
            try:
                os.remove(os.path.join(self.BACKUP_DIR, fname))
                logger.info(f"Pruned old backup: {fname}")
            except Exception as exc:
                logger.warning(f"Could not prune backup {fname}: {exc}")

    def list_backups(self) -> list:
        """Return backup metadata dicts sorted newest-first."""
        if not os.path.isdir(self.BACKUP_DIR):
            return []
        result = []
        for fname in os.listdir(self.BACKUP_DIR):
            m = self._BACKUP_FILENAME_RE.match(fname)
            if not m:
                continue
            fpath = os.path.join(self.BACKUP_DIR, fname)
            try:
                size = os.path.getsize(fpath)
                mtime = os.path.getmtime(fpath)
                result.append({
                    "filename":   fname,
                    "path":       fpath,
                    "size_bytes": size,
                    "size_human": self._format_bytes(size),
                    "created_at": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                    "label":      m.group(1),
                })
            except Exception:
                continue
        result.sort(key=lambda x: x["created_at"], reverse=True)
        return result

    def restore_backup(self, filename: str) -> dict:
        """Restore a backup file over the live database.

        Safety steps:
        1. Validate filename (no path traversal, must match pattern).
        2. Create a pre-restore safety backup of the current DB.
        3. Copy the chosen backup over the live DB.
        Returns {"success": True, "pre_restore_backup": safety_filename}.
        """
        if not self._BACKUP_FILENAME_RE.match(filename):
            raise ValueError(f"Invalid backup filename: {filename!r}")

        backup_path = os.path.join(self.BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {filename}")

        # Safety backup of current state
        safety = self.create_backup(label="pre_restore")
        safety_filename = safety["filename"]

        shutil.copy2(backup_path, self.db_path)
        logger.info(f"Restored backup {filename}; pre-restore safety saved as {safety_filename}")
        return {"success": True, "pre_restore_backup": safety_filename}

    # ── Shared Notes ──────────────────────────────────────────────────────────

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """Return SHA-256 hex digest of a raw share token."""
        return hashlib.sha256(raw_token.encode()).hexdigest()

    def create_share(
        self,
        note_title: str,
        permission: str,
        expires_at=None,
        password: str | None = None,
    ) -> dict:
        """Create a new share token for a note.

        Returns a dict containing the raw token (shown once only), preview,
        note_title, permission, expires_at, created_at, and has_password.
        Raises RuntimeError when the database is unavailable.
        """
        if not self.enabled:
            raise RuntimeError("Database is not enabled")

        raw_token     = secrets.token_urlsafe(16)
        token_hash    = self._hash_token(raw_token)
        token_preview = raw_token[:6]
        now           = datetime.now(timezone.utc)
        pw_hash       = _hash_password(password) if password else None

        db = self.get_session()
        try:
            share = SharedNote(
                id               = token_hash,
                token_preview    = token_preview,
                note_title       = note_title,
                permission       = permission,
                created_at       = now,
                expires_at       = expires_at,
                is_active        = True,
                last_accessed_at = None,
                access_count     = 0,
                password_hash    = pw_hash,
            )
            db.add(share)
            db.commit()
            logger.info(f"Share token created for '{note_title}' ({permission})")
            return {
                "token":         raw_token,       # returned once, never stored
                "token_preview": token_preview,
                "note_title":    note_title,
                "permission":    permission,
                "expires_at":    expires_at.isoformat() if expires_at else None,
                "created_at":    now.isoformat(),
                "has_password":  pw_hash is not None,
            }
        except Exception as exc:
            db.rollback()
            raise RuntimeError(f"Failed to create share: {exc}") from exc
        finally:
            db.close()

    def validate_share(self, raw_token: str, password: str | None = None) -> dict | None:
        """Validate a raw share token and return its metadata, or None if invalid.

        Password protection:
        - If the share has a password and none is supplied, returns
          {"requires_password": True} without any note data.
        - If the share has a password and the supplied one is wrong, returns None.
        - If the share has no password, the password argument is ignored.

        Also updates last_accessed_at and access_count on every successful hit.
        Returns None when the token is unknown, inactive, or expired.
        """
        if not self.enabled:
            return None

        token_hash = self._hash_token(raw_token)
        db         = self.get_session()
        try:
            share = db.query(SharedNote).filter(
                SharedNote.id        == token_hash,
                SharedNote.is_active == True,
            ).first()

            if not share:
                return None

            # Expiry check
            if share.expires_at is not None:
                now = datetime.now(timezone.utc)
                exp = share.expires_at
                if exp.tzinfo is None:
                    from datetime import timezone as _tz
                    exp = exp.replace(tzinfo=_tz.utc)
                if now > exp:
                    return None

            # Password check
            if share.password_hash:
                if password is None:
                    return {"requires_password": True}
                if not _verify_password(password, share.password_hash):
                    return None  # wrong password

            # Record access silently
            share.last_accessed_at = datetime.now(timezone.utc)
            share.access_count     = (share.access_count or 0) + 1
            db.commit()

            return {
                "token_preview":   share.token_preview,
                "note_title":      share.note_title,
                "permission":      share.permission,
                "expires_at":      share.expires_at.isoformat() if share.expires_at else None,
                "created_at":      share.created_at.isoformat() if share.created_at else None,
                "access_count":    share.access_count,
                "has_password":    share.password_hash is not None,
                "requires_password": False,
            }
        except Exception as exc:
            logger.error(f"Share validation error: {exc}")
            return None
        finally:
            db.close()

    def list_shares(self, note_title: str) -> list:
        """Return all active share tokens for a given note, newest first."""
        if not self.enabled:
            return []

        db = self.get_session()
        try:
            shares = db.query(SharedNote).filter(
                SharedNote.note_title == note_title,
                SharedNote.is_active  == True,
            ).order_by(SharedNote.created_at.desc()).all()

            return [
                {
                    "id":                s.id,
                    "token_preview":     s.token_preview,
                    "note_title":        s.note_title,
                    "permission":        s.permission,
                    "expires_at":        s.expires_at.isoformat() if s.expires_at else None,
                    "created_at":        s.created_at.isoformat() if s.created_at else None,
                    "last_accessed_at":  s.last_accessed_at.isoformat() if s.last_accessed_at else None,
                    "access_count":      s.access_count or 0,
                    "has_password":      s.password_hash is not None,
                }
                for s in shares
            ]
        except Exception as exc:
            logger.error(f"list_shares error: {exc}")
            return []
        finally:
            db.close()

    def revoke_share(self, raw_token: str) -> bool:
        """Hard-delete a share token. Returns True if deleted, False if not found."""
        if not self.enabled:
            return False

        token_hash = self._hash_token(raw_token)
        db         = self.get_session()
        try:
            rows = db.query(SharedNote).filter(SharedNote.id == token_hash).delete()
            db.commit()
            if rows:
                logger.info(f"Share token revoked: {token_hash[:12]}…")
            return rows > 0
        except Exception as exc:
            logger.error(f"revoke_share error: {exc}")
            db.rollback()
            return False
        finally:
            db.close()

    def list_all_shares(self) -> list:
        """Return all active share tokens across all notes, newest first."""
        if not self.enabled:
            return []

        db = self.get_session()
        try:
            shares = db.query(SharedNote).filter(
                SharedNote.is_active == True,
            ).order_by(SharedNote.created_at.desc()).all()

            return [
                {
                    "id":                s.id,
                    "token_preview":     s.token_preview,
                    "note_title":        s.note_title,
                    "permission":        s.permission,
                    "expires_at":        s.expires_at.isoformat() if s.expires_at else None,
                    "created_at":        s.created_at.isoformat() if s.created_at else None,
                    "last_accessed_at":  s.last_accessed_at.isoformat() if s.last_accessed_at else None,
                    "access_count":      s.access_count or 0,
                    "has_password":      s.password_hash is not None,
                }
                for s in shares
            ]
        except Exception as exc:
            logger.error(f"list_all_shares error: {exc}")
            return []
        finally:
            db.close()

    def revoke_share_by_hash(self, token_hash: str) -> bool:
        """Hard-delete a share token by its hash (the `id` column).

        Used by the admin /shares page where raw tokens are unavailable.
        Returns True if a row was deleted, False if not found.
        """
        if not self.enabled:
            return False

        db = self.get_session()
        try:
            rows = db.query(SharedNote).filter(SharedNote.id == token_hash).delete()
            db.commit()
            if rows:
                logger.info(f"Share revoked by hash: {token_hash[:12]}…")
            return rows > 0
        except Exception as exc:
            logger.error(f"revoke_share_by_hash error: {exc}")
            db.rollback()
            return False
        finally:
            db.close()

    def revoke_all_shares(self, note_title: str) -> int:
        """Hard-delete all active share tokens for a note.

        Returns the count of deleted rows.
        """
        if not self.enabled:
            return 0

        db = self.get_session()
        try:
            rows = db.query(SharedNote).filter(
                SharedNote.note_title == note_title,
                SharedNote.is_active  == True,
            ).delete()
            db.commit()
            if rows:
                logger.info(f"Revoked all {rows} shares for '{note_title}'")
            return rows
        except Exception as exc:
            logger.error(f"revoke_all_shares error: {exc}")
            db.rollback()
            return 0
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