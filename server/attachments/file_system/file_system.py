import os
import re
import shutil
import urllib.parse
from datetime import datetime
from typing import List

from fastapi import UploadFile
from fastapi.responses import FileResponse

from helpers import get_env, is_valid_filename

from ..base import BaseAttachments
from ..models import AttachmentCreateResponse, AttachmentInfo

# Extensions treated as images (shown with inline preview in the UI)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif", ".tiff", ".tif"}
PDF_EXTENSIONS = {".pdf"}
DOCUMENT_EXTENSIONS = {
    # Office / word processors
    ".docx", ".doc", ".odt",
    # Spreadsheets
    ".xls", ".xlsx", ".ods", ".csv",
    # Presentations
    ".pptx", ".ppt", ".odp",
    # Apple iWork
    ".numbers", ".pages", ".key",
    # Plain text / markup
    ".txt", ".rtf", ".md", ".markdown",
    ".json", ".yaml", ".yml", ".xml", ".html", ".htm",
    # Archives
    ".zip", ".gz", ".tar", ".7z", ".rar", ".bz2", ".xz",
    # Code
    ".js", ".ts", ".py", ".sh", ".rb", ".php",
    # Audio
    ".mp3", ".m4a", ".ogg", ".wav", ".flac", ".aac",
    # Video
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    # Fonts
    ".ttf", ".otf", ".woff",
}


class FileSystemAttachments(BaseAttachments):
    def __init__(self):
        self.base_path = get_env("FLATNOTES_PATH", mandatory=True)
        if not os.path.exists(self.base_path):
            raise NotADirectoryError(
                f"'{self.base_path}' is not a valid directory."
            )
        self.storage_path = os.path.join(self.base_path, "attachments")
        os.makedirs(self.storage_path, exist_ok=True)

    def create(self, file: UploadFile) -> AttachmentCreateResponse:
        """Create a new attachment."""
        is_valid_filename(file.filename)
        try:
            self._save_file(file)
        except FileExistsError:
            file.filename = self._datetime_suffix_filename(file.filename)
            self._save_file(file)
        return AttachmentCreateResponse(
            filename=file.filename, url=self._url_for_filename(file.filename)
        )

    def get(self, filename: str) -> FileResponse:
        """Get a specific attachment, using case-insensitive lookup.

        Strategy: try an exact match first (fast path, covers the common case).
        If that misses, scan the directory for a case-insensitive match so that
        a note linking to ``Photo.PNG`` still resolves when the file on disk is
        ``photo.png``.  The file is served under its original on-disk name;
        nothing is renamed.
        """
        is_valid_filename(filename)
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.isfile(filepath):
            # Slow path: case-insensitive scan
            lower = filename.lower()
            try:
                match = next(
                    e.name for e in os.scandir(self.storage_path)
                    if e.is_file() and e.name.lower() == lower
                )
                filepath = os.path.join(self.storage_path, match)
            except StopIteration:
                raise FileNotFoundError(f"'{filename}' not found.")
        return FileResponse(filepath)

    def list_all(self) -> List[AttachmentInfo]:
        """Return info for every attachment file, including which notes use it.

        Cross-references are found by scanning all .md files for the attachment
        filename. We search for the URL pattern "attachments/<filename>" which
        is what the editor inserts when an image is uploaded.
        """
        if not os.path.isdir(self.storage_path):
            return []

        # Build a lookup: {filename_lower: [note_title, ...]} by scanning .md files.
        # Keys are stored lowercased so that a reference to "Photo.PNG" in a note
        # matches a file named "photo.png" on disk (and vice-versa).
        usage_map: dict[str, list[str]] = {}
        notes_path = self.base_path
        for root, dirs, files in os.walk(notes_path):
            # Skip system/storage directories that should never contribute to usage.
            # NOTE: _archive is intentionally NOT excluded — archived notes still
            # own their attachments and should prevent them from appearing "unused".
            # _trash IS excluded — deleted notes no longer count as active references.
            dirs[:] = [
                d for d in dirs
                if d not in ("attachments", ".flatnotes", ".metadata", "_trash")
            ]
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except OSError:
                    continue
                # Derive the note title from its path relative to base_path
                rel = os.path.relpath(fpath, notes_path)
                note_title = rel[:-3].replace(os.sep, "/")  # strip .md
                # Find all attachment references: "attachments/<filename>"
                referenced = re.findall(r"attachments/([^\s\)\]\"']+)", content)
                for ref in referenced:
                    decoded = urllib.parse.unquote(ref).lower()   # normalise case
                    usage_map.setdefault(decoded, [])
                    if note_title not in usage_map[decoded]:
                        usage_map[decoded].append(note_title)

        # Build the result list from the actual files on disk
        results: List[AttachmentInfo] = []
        for entry in sorted(os.scandir(self.storage_path), key=lambda e: e.name):
            if not entry.is_file():
                continue
            stat = entry.stat()
            ext = os.path.splitext(entry.name)[1].lower()
            results.append(AttachmentInfo(
                filename=entry.name,
                url=self._url_for_filename(entry.name),
                size_bytes=stat.st_size,
                is_image=ext in IMAGE_EXTENSIONS,
                is_pdf=ext in PDF_EXTENSIONS,
                is_document = ext in DOCUMENT_EXTENSIONS,
                used_in=usage_map.get(entry.name.lower(), []),  # case-insensitive lookup
            ))
        return results

    def delete(self, filename: str) -> None:
        """Permanently delete an attachment file from disk.

        Uses case-insensitive lookup so that the delete API works even when the
        caller's casing differs from the on-disk filename.
        """
        is_valid_filename(filename)
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.isfile(filepath):
            # Case-insensitive fallback
            lower = filename.lower()
            try:
                match = next(
                    e.name for e in os.scandir(self.storage_path)
                    if e.is_file() and e.name.lower() == lower
                )
                filepath = os.path.join(self.storage_path, match)
            except StopIteration:
                raise FileNotFoundError(f"'{filename}' not found.")
        os.remove(filepath)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _save_file(self, file: UploadFile):
        filepath = os.path.join(self.storage_path, file.filename)
        with open(filepath, "xb") as f:
            shutil.copyfileobj(file.file, f)

    def _datetime_suffix_filename(self, filename: str) -> str:
        """Add a timestamp suffix to avoid filename collisions."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        name, ext = os.path.splitext(filename)
        return f"{name}_{timestamp}{ext}"

    def _url_for_filename(self, filename: str) -> str:
        """Return the relative URL for the given filename."""
        return f"attachments/{urllib.parse.quote(filename)}"