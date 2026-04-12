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
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}
PDF_EXTENSIONS = {".pdf"}
DOCUMENT_EXTENSIONS = {".docx", ".doc", ".xls", ".xlsx", ".numbers", ".pages", ".txt", ".rtf"}   # NEW


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
        """Get a specific attachment."""
        is_valid_filename(filename)
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.isfile(filepath):
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

        # Build a lookup: {filename: [note_title, ...]} by scanning .md files
        usage_map: dict[str, list[str]] = {}
        notes_path = self.base_path
        for root, dirs, files in os.walk(notes_path):
            # Skip system directories and the attachments folder itself
            dirs[:] = [
                d for d in dirs
                if d not in ("attachments", ".flatnotes", ".metadata",
                             "_trash", "_archive")
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
                    decoded = urllib.parse.unquote(ref)
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
                used_in=usage_map.get(entry.name, []),
            ))
        return results

    def delete(self, filename: str) -> None:
        """Permanently delete an attachment file from disk."""
        is_valid_filename(filename)
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.isfile(filepath):
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
