import glob
import os
import re
import shutil
import time
from datetime import datetime
from typing import List, Literal, Set, Tuple

import whoosh
from whoosh import writing
from whoosh.analysis import CharsetFilter, StemmingAnalyzer
from whoosh.fields import DATETIME, ID, KEYWORD, TEXT, SchemaClass
from whoosh.highlight import ContextFragmenter, WholeFragmenter
from whoosh.index import Index, LockError
from whoosh.qparser import MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh.query import Every
from whoosh.searching import Hit
from whoosh.support.charset import accent_map

from helpers import get_env, is_valid_filename
from logger import logger

from ..base import BaseNotes
from ..models import Note, NoteCreate, NoteUpdate, SearchResult

MARKDOWN_EXT = ".md"
META_EXT = ".meta.json"  # sidecar metadata file (timestamps)
METADATA_DIR = '.metadata'
INDEX_SCHEMA_VERSION = "9"  # bumped: nested tag regex now supports /hierarchy
ARCHIVE_DIR = "_archive"
TRASH_DIR = "_trash"

StemmingFoldingAnalyzer = StemmingAnalyzer() | CharsetFilter(accent_map)


class IndexSchema(SchemaClass):
    filename = ID(unique=True, stored=True)
    last_modified = DATETIME(stored=True, sortable=True)
    title = TEXT(
        field_boost=2.0, analyzer=StemmingFoldingAnalyzer, sortable=True
    )
    content = TEXT(analyzer=StemmingFoldingAnalyzer)
    tags = KEYWORD(stored=True, lowercase=True, field_boost=2.0)
    folder = ID(stored=True)          # NEW: relative folder path
    archived = ID(stored=True)        # "1" if archived
    in_trash = ID(stored=True)         # "1" if in _trash


class FileSystemNotes(BaseNotes):
    TAGS_RE = re.compile(r"(?:(?<=^#)|(?<=\s#))[a-zA-Z][a-zA-Z0-9_/-]*(?=\s|$)")
    CODEBLOCK_RE = re.compile(r"```.*?```|`[^`]*`", re.DOTALL)
    TAGS_WITH_HASH_RE = re.compile(
        r"(?:(?<=^)|(?<=\s))#[a-zA-Z][a-zA-Z0-9_/-]*(?=\s|$)"
    )
    # Allow forward-slash in paths but not other reserved chars
    INVALID_PATH_CHARS_RE = re.compile(r'[<>:"\\|?*]')

    def __init__(self):
        self.storage_path = get_env("FLATNOTES_PATH", mandatory=True)
        if not os.path.exists(self.storage_path):
            raise NotADirectoryError(
                f"'{self.storage_path}' is not a valid directory."
            )
        self.index = self._load_index()
        self._migrate_metadata()
        self._sync_index_with_retry(optimize=True)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def create(self, data: NoteCreate) -> Note:
        """Create a new note (supports subdirectory paths like 'work/todo')."""
        self._validate_note_path(data.title)
        filepath = self._path_from_title(data.title)
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._write_file(filepath, data.content)
        # Write creation timestamp (set once, never changed)
        now = datetime.now().isoformat(timespec="seconds")
        self._write_meta(data.title, {"created": now, "updated": now})
        meta = self._read_meta(data.title)
        return Note(
            title=data.title,
            content=data.content,
            last_modified=os.path.getmtime(filepath),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    def get(self, title: str) -> Note:
        """Get a specific note."""
        self._validate_note_path(title)
        filepath = self._path_from_title(title)
        content = self._read_file(filepath)
        meta = self._read_meta(title)
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    def update(self, title: str, data: NoteUpdate) -> Note:
        """Update a specific note."""
        self._validate_note_path(title)
        filepath = self._path_from_title(title)
        # Read existing meta before any rename so we preserve 'created'
        meta = self._read_meta(title)
        if data.new_title is not None:
            self._validate_note_path(data.new_title)
            new_filepath = self._path_from_title(data.new_title)
            if filepath != new_filepath and os.path.isfile(new_filepath):
                raise FileExistsError(
                    f"Failed to rename. '{data.new_title}' already exists."
                )
            os.makedirs(os.path.dirname(new_filepath), exist_ok=True)
            os.rename(filepath, new_filepath)
            # Move sidecar metadata file alongside the renamed note
            old_meta_path = self._meta_path(title)
            if os.path.exists(old_meta_path):
                os.rename(old_meta_path, self._meta_path(data.new_title))
            self._cleanup_empty_dirs(os.path.dirname(filepath))
            title = data.new_title
            filepath = new_filepath
        if data.new_content is not None:
            self._write_file(filepath, data.new_content, overwrite=True)
            content = data.new_content
        else:
            content = self._read_file(filepath)
        # Update the 'updated' timestamp; preserve 'created'
        now = datetime.now().isoformat(timespec="seconds")
        meta["updated"] = now
        if "created" not in meta:
            # Back-fill 'created' for notes that predate this feature
            meta["created"] = now
        self._write_meta(title, meta)
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    def delete(self, title: str) -> None:
        """Soft-delete: move note to _trash/ instead of permanent deletion."""
        self._validate_note_path(title)
        # Guard: don't double-trash a note already in _trash
        if title.startswith(f"{TRASH_DIR}/"):
            raise ValueError("Note is already in trash.")
        src = self._path_from_title(title)
        trash_title = f"{TRASH_DIR}/{title}"
        dst = self._path_from_title(trash_title)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        # If a trashed copy already exists, suffix with timestamp to avoid collision
        if os.path.exists(dst):
            import time as _time
            stamp = int(_time.time())
            trash_title = f"{TRASH_DIR}/{title}_{stamp}"
            dst = self._path_from_title(trash_title)
        os.rename(src, dst)
        # Move sidecar metadata file with the note
        src_meta = self._meta_path(title)
        if os.path.exists(src_meta):
            dst_meta = self._meta_path(trash_title)
            os.makedirs(os.path.dirname(dst_meta), exist_ok=True)
            os.rename(src_meta, dst_meta)
        self._cleanup_empty_dirs(os.path.dirname(src))

    def restore_from_trash(self, title: str) -> "Note":
        """Move a note out of _trash/ back to its original path."""
        if not title.startswith(f"{TRASH_DIR}/"):
            raise ValueError("Note is not in trash.")
        original_title = title[len(TRASH_DIR) + 1:]
        import re as _re
        original_title = _re.sub(r"_\d{10}$", "", original_title)
        self._validate_note_path(original_title)
        src = self._path_from_title(title)
        dst = self._path_from_title(original_title)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            raise FileExistsError(f"Note '{original_title}' already exists.")
        meta = self._read_meta(title)
        os.rename(src, dst)
        # Move sidecar metadata back with the note
        src_meta = self._meta_path(title)
        if os.path.exists(src_meta):
            dst_meta = self._meta_path(original_title)
            os.makedirs(os.path.dirname(dst_meta), exist_ok=True)
            os.rename(src_meta, dst_meta)
            # Clean up the old metadata directory if empty
            src_meta_dir = os.path.dirname(src_meta)
            self._cleanup_empty_dirs(src_meta_dir)
        # Clean up empty directories upward from the note's original trash location
        self._cleanup_empty_dirs(os.path.dirname(src))
        content = self._read_file(dst)
        return Note(title=original_title, content=content,
                    last_modified=os.path.getmtime(dst),
                    created=meta.get("created"),
                    updated=meta.get("updated"))

    def permanently_delete(self, title: str) -> None:
        """Permanently remove a note (must already be in _trash)."""
        if not title.startswith(f"{TRASH_DIR}/"):
            raise ValueError("Only notes in _trash can be permanently deleted.")
        self._validate_note_path(title)

        # Delete the note file
        filepath = self._path_from_title(title)
        os.remove(filepath)

        # Delete its metadata file
        meta_path = self._meta_path(title)
        if os.path.exists(meta_path):
            os.remove(meta_path)
            # Clean up empty .metadata directory
            meta_dir = os.path.dirname(meta_path)
            self._cleanup_empty_dirs(meta_dir)

        # Clean up empty directories upward from the note's folder
        self._cleanup_empty_dirs(os.path.dirname(filepath))

    def permanently_delete_archived(self, title: str) -> None:
        """Permanently remove an archived note (must already be in _archive)."""
        if not title.startswith(f"{ARCHIVE_DIR}/"):
            raise ValueError("Only notes in _archive can be permanently deleted.")
        self._validate_note_path(title)

        # Delete the note file
        filepath = self._path_from_title(title)
        os.remove(filepath)

        # Delete its metadata file
        meta_path = self._meta_path(title)
        if os.path.exists(meta_path):
            os.remove(meta_path)
            # Clean up empty .metadata directory
            meta_dir = os.path.dirname(meta_path)
            self._cleanup_empty_dirs(meta_dir)

        # Clean up empty directories upward from the note's folder
        self._cleanup_empty_dirs(os.path.dirname(filepath))

    def empty_old_trash(self, days: int) -> list:
        """Permanently delete trash items older than `days` days.
        Returns list of deleted titles."""
        import time as _time
        cutoff = _time.time() - days * 86400
        deleted = []
        trash_path = os.path.join(self.storage_path, TRASH_DIR)
        if not os.path.isdir(trash_path):
            return deleted
        for dirpath, _, filenames in os.walk(trash_path):
            for fname in filenames:
                if not fname.endswith(MARKDOWN_EXT):
                    continue
                fpath = os.path.join(dirpath, fname)
                if os.path.getmtime(fpath) < cutoff:
                    # Delete the note file
                    os.remove(fpath)
                    # Compute title to find metadata
                    rel = os.path.relpath(fpath, self.storage_path)
                    title = self._strip_ext(rel.replace(os.sep, "/"))
                    meta_path = self._meta_path(title)
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                        meta_dir = os.path.dirname(meta_path)
                        self._cleanup_empty_dirs(meta_dir)
                    deleted.append(title)
                    logger.info(f"Auto-purged from trash: {fname}")
        # After walking, clean up any empty directories in trash
        self._cleanup_empty_dirs(trash_path)
        return deleted

    def _is_trashed(self, title: str) -> bool:
        return title.startswith(f"{TRASH_DIR}/") or title == TRASH_DIR

    def archive(self, title: str) -> Note:
        """Move a note into the _archive/ subfolder and add #archived tag."""
        self._validate_note_path(title)
        src = self._path_from_title(title)
        archive_title = f"{ARCHIVE_DIR}/{title}"
        dst = self._path_from_title(archive_title)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            raise FileExistsError(f"Archived note '{archive_title}' already exists.")
        # Add #archived tag to content before moving
        note_content = self._read_file(src)
        note_content = self._add_tag(note_content, "archived")
        self._write_file(src, note_content, overwrite=True)
        meta = self._read_meta(title)
        os.rename(src, dst)
        # Move sidecar metadata with the note
        src_meta = self._meta_path(title)
        if os.path.exists(src_meta):
            dst_meta = self._meta_path(archive_title)
            os.makedirs(os.path.dirname(dst_meta), exist_ok=True)
            os.rename(src_meta, dst_meta)
        self._cleanup_empty_dirs(os.path.dirname(src))
        return Note(
            title=archive_title,
            content=note_content,
            last_modified=os.path.getmtime(dst),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    def unarchive(self, title: str) -> Note:
        """Move a note out of _archive/ and remove the #archived tag."""
        if not title.startswith(f"{ARCHIVE_DIR}/"):
            raise ValueError("Note is not archived.")
        original_title = title[len(ARCHIVE_DIR) + 1:]
        self._validate_note_path(original_title)
        src = self._path_from_title(title)
        dst = self._path_from_title(original_title)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            raise FileExistsError(f"Note '{original_title}' already exists.")
        # Remove #archived tag from content before moving
        note_content = self._read_file(src)
        note_content = self._remove_tag(note_content, "archived")
        self._write_file(src, note_content, overwrite=True)
        meta = self._read_meta(title)
        os.rename(src, dst)
        # Move sidecar metadata back with the note
        src_meta = self._meta_path(title)
        if os.path.exists(src_meta):
            dst_meta = self._meta_path(original_title)
            os.makedirs(os.path.dirname(dst_meta), exist_ok=True)
            os.rename(src_meta, dst_meta)
        self._cleanup_empty_dirs(os.path.dirname(src))
        return Note(
            title=original_title,
            content=note_content,
            last_modified=os.path.getmtime(dst),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    # ========== PIN METHODS ==========
    def pin(self, title: str) -> Note:
        """Add #pin tag to the note (at the top)."""
        self._validate_note_path(title)
        filepath = self._path_from_title(title)
        note_content = self._read_file(filepath)
        # Add #pin tag if not already present
        if "#pin" not in note_content:
            note_content = "#pin\n" + note_content
            self._write_file(filepath, note_content, overwrite=True)
        # Update timestamp
        now = datetime.now().isoformat(timespec="seconds")
        meta = self._read_meta(title)
        meta["updated"] = now
        self._write_meta(title, meta)
        return Note(
            title=title,
            content=note_content,
            last_modified=os.path.getmtime(filepath),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    def unpin(self, title: str) -> Note:
        """Remove #pin tag from the note (if at top)."""
        self._validate_note_path(title)
        filepath = self._path_from_title(title)
        note_content = self._read_file(filepath)
        # Remove #pin tag from the very beginning (optionally with newline)
        if note_content.startswith("#pin\n"):
            note_content = note_content[5:]  # remove "#pin\n"
        elif note_content.startswith("#pin"):
            note_content = note_content[4:]  # remove "#pin" (no newline, rare)
        # If there's a newline after removal, ensure we don't have double newlines
        note_content = note_content.lstrip('\n')
        self._write_file(filepath, note_content, overwrite=True)
        # Update timestamp
        now = datetime.now().isoformat(timespec="seconds")
        meta = self._read_meta(title)
        meta["updated"] = now
        self._write_meta(title, meta)
        return Note(
            title=title,
            content=note_content,
            last_modified=os.path.getmtime(filepath),
            created=meta.get("created"),
            updated=meta.get("updated"),
        )

    def search(
        self,
        term: str,
        sort: Literal["score", "title", "last_modified"] = "score",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        include_archived: bool = False,
        include_trash: bool = False,
    ) -> Tuple[SearchResult, ...]:
        """Search the index for the given term."""
        self._sync_index_with_retry()
        term = self._pre_process_search_term(term)
        with self.index.searcher() as searcher:
            if term == "*":
                query = Every()
            else:
                parser = MultifieldParser(
                    self._fieldnames_for_term(term), self.index.schema
                )
                parser.add_plugin(DateParserPlugin())
                query = parser.parse(term)

            # Filter out archived and trashed notes unless explicitly requested
            from whoosh.query import Term, AndNot, Or
            hide_terms = []
            if not include_archived:
                hide_terms.append(Term("archived", "1"))
            if not include_trash:
                hide_terms.append(Term("in_trash", "1"))
            if hide_terms:
                hide_q = Or(hide_terms) if len(hide_terms) > 1 else hide_terms[0]
                query = AndNot(query, hide_q)

            sort = sort if sort in ["title", "last_modified"] else None
            reverse = order == "desc"
            if sort is None:
                reverse = not reverse

            results = searcher.search(
                query,
                sortedby=sort,
                reverse=reverse,
                limit=limit,
                terms=True,
            )
            return tuple(self._search_result_from_hit(hit) for hit in results)

    def get_tags(self, include_archived: bool = False) -> dict:
        """Return a dict of {tag: note_count} for all indexed tags.

        Counts exact-match tags from the index. For nested tags like
        "bookmark/todo", also synthesizes parent counts so that "bookmark"
        reflects the sum of all its children (plus its own direct uses).

        Example: if three notes have #bookmark/todo and one has #bookmark,
        the result is: {"bookmark": 4, "bookmark/todo": 3}
        """
        self._sync_index_with_retry()
        exact_counts = {}
        with self.index.searcher() as searcher:
            for fields in searcher.all_stored_fields():
                if not include_archived and fields.get("archived") == "1":
                    continue
                if fields.get("in_trash") == "1":
                    continue
                tag_string = fields.get("tags", "")
                if tag_string:
                    for tag in tag_string.split():
                        exact_counts[tag] = exact_counts.get(tag, 0) + 1

        # Synthesize parent counts: "a/b/c" contributes to "a/b" and "a".
        # Always add child note counts to ancestor, even if ancestor also exists
        # directly (e.g. if both #bookmark and #bookmark/todo are used, bookmark
        # gets 1 direct count + the child counts added on top).
        tag_counts = dict(exact_counts)
        for tag, count in exact_counts.items():
            if "/" in tag:
                parts = tag.split("/")
                for depth in range(1, len(parts)):
                    ancestor = "/".join(parts[:depth])
                    tag_counts[ancestor] = tag_counts.get(ancestor, 0) + count

        return tag_counts

    def get_folders(self) -> dict:
        """Return a dict of {folder_path: note_count} for all folders.

        Counts direct notes in each folder. Also synthesises parent counts so
        that a folder shows the total of all notes in it and its subfolders.
        Excludes _archive, _trash and _templates internal folders.
        """
        self._sync_index_with_retry()
        exact_counts = {}
        with self.index.reader() as reader:
            for fields in reader.all_stored_fields():
                folder = fields.get("folder", "")
                if not folder:
                    continue
                # Skip internal system folders
                parts = folder.split("/")
                if parts[0] in ("_archive", "_trash", "_templates"):
                    continue
                exact_counts[folder] = exact_counts.get(folder, 0) + 1

        # Synthesise parent counts
        folder_counts = dict(exact_counts)
        for folder, count in exact_counts.items():
            if "/" in folder:
                parts = folder.split("/")
                for depth in range(1, len(parts)):
                    ancestor = "/".join(parts[:depth])
                    folder_counts[ancestor] = folder_counts.get(ancestor, 0) + count

        return folder_counts

    def get_notes_in_folder(self, folder_path: str) -> List[str]:
        """Return a list of note titles (without extension) in the specified folder.
        
        Args:
            folder_path: Relative folder path (e.g., "work" or "work/project")
            
        Returns:
            Sorted list of note titles (alphabetical)
        """
        self._sync_index_with_retry()
        folder_prefix = folder_path + "/" if folder_path else ""
        titles = []
        
        with self.index.reader() as reader:
            for fields in reader.all_stored_fields():
                filename = fields.get("filename", "")
                if not filename.endswith(MARKDOWN_EXT):
                    continue
                
                title = self._strip_ext(filename)
                
                # Skip notes in system folders
                if title.startswith(f"{TRASH_DIR}/") or title.startswith(f"{ARCHIVE_DIR}/"):
                    continue
                
                # Check if note is in the requested folder
                if folder_path:
                    if title.startswith(folder_prefix) and "/" not in title[len(folder_prefix):]:
                        titles.append(title)
                else:
                    # Root folder (no slashes)
                    if "/" not in title:
                        titles.append(title)
        
        # Sort alphabetically
        titles.sort()
        return titles


    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    @property
    def _index_path(self):
        return os.path.join(self.storage_path, ".flatnotes")

    def _path_from_title(self, title: str) -> str:
        return os.path.join(self.storage_path, title + MARKDOWN_EXT)

    def _folder_from_title(self, title: str) -> str:
        """Return the folder component of a note title (empty string for root)."""
        parts = title.rsplit("/", 1)
        return parts[0] if len(parts) > 1 else ""

    def _is_archived(self, title: str) -> bool:
        return title.startswith(f"{ARCHIVE_DIR}/") or title == ARCHIVE_DIR

    def _get_by_filename(self, relative_filename: str) -> Note:
        """Get a note by its relative filename (from storage root)."""
        title = self._strip_ext(relative_filename)
        return self.get(title)

    def _load_index(self) -> Index:
        index_dir_exists = os.path.exists(self._index_path)
        if index_dir_exists and whoosh.index.exists_in(
            self._index_path, indexname=INDEX_SCHEMA_VERSION
        ):
            logger.info("Loading existing index")
            return whoosh.index.open_dir(
                self._index_path, indexname=INDEX_SCHEMA_VERSION
            )
        else:
            if index_dir_exists:
                logger.info("Deleting outdated index")
                self._clear_dir(self._index_path)
            else:
                os.mkdir(self._index_path)
            logger.info("Creating new index")
            return whoosh.index.create_in(
                self._index_path, IndexSchema, indexname=INDEX_SCHEMA_VERSION
            )

    @classmethod
    def _extract_tags(cls, content) -> Tuple[str, Set[str]]:
        content_ex_codeblock = re.sub(cls.CODEBLOCK_RE, "", content)
        _, tags = cls._re_extract(cls.TAGS_RE, content_ex_codeblock)
        content_ex_tags, _ = cls._re_extract(cls.TAGS_RE, content)
        try:
            tags = [tag.lower() for tag in tags]
            return (content_ex_tags, set(tags))
        except IndexError:
            return (content, set())

    def _add_note_to_index(
        self, writer: writing.IndexWriter, note: Note
    ) -> None:
        content_ex_tags, tag_set = self._extract_tags(note.content or "")
        tag_string = " ".join(tag_set)
        folder = self._folder_from_title(note.title)
        archived = "1" if self._is_archived(note.title) else "0"
        in_trash = "1" if self._is_trashed(note.title) else "0"
        # Use relative path as filename key
        writer.update_document(
            filename=note.title + MARKDOWN_EXT,
            last_modified=datetime.fromtimestamp(note.last_modified),
            title=note.title,
            content=content_ex_tags,
            tags=tag_string,
            folder=folder,
            archived=archived,
            in_trash=in_trash,
        )

    def _list_all_note_filenames(self) -> List[str]:
        """Return list of all .md filenames relative to storage_path (includes subdirs)."""
        results = []
        for dirpath, dirnames, filenames in os.walk(self.storage_path):
            # Skip hidden directories (like .flatnotes, .metadata)
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fname in filenames:
                if fname.endswith(MARKDOWN_EXT):
                    full = os.path.join(dirpath, fname)
                    rel = os.path.relpath(full, self.storage_path)
                    # Normalize to forward slashes
                    rel = rel.replace(os.sep, "/")
                    results.append(rel)
        return results

    def _sync_index(self, optimize: bool = False, clean: bool = False) -> None:
        indexed = set()
        writer = self.index.writer()
        if clean:
            writer.mergetype = writing.CLEAR
        with self.index.searcher() as searcher:
            for idx_note in searcher.all_stored_fields():
                idx_filename = idx_note["filename"]  # e.g. "work/todo.md"
                idx_filepath = os.path.join(
                    self.storage_path, idx_filename.replace("/", os.sep)
                )
                if not os.path.exists(idx_filepath):
                    writer.delete_by_term("filename", idx_filename)
                    logger.info(f"'{idx_filename}' removed from index")
                elif (
                    datetime.fromtimestamp(os.path.getmtime(idx_filepath))
                    != idx_note["last_modified"]
                ):
                    logger.info(f"'{idx_filename}' updated")
                    self._add_note_to_index(
                        writer, self._get_by_filename(idx_filename)
                    )
                    indexed.add(idx_filename)
                else:
                    indexed.add(idx_filename)
        for filename in self._list_all_note_filenames():
            if filename not in indexed:
                self._add_note_to_index(
                    writer, self._get_by_filename(filename)
                )
                logger.info(f"'{filename}' added to index")
        writer.commit(optimize=optimize)
        logger.info("Index synchronized")

    def _sync_index_with_retry(
        self,
        optimize: bool = False,
        clean: bool = False,
        max_retries: int = 8,
        retry_delay: float = 0.25,
    ) -> None:
        for _ in range(max_retries):
            try:
                self._sync_index(optimize=optimize, clean=clean)
                return
            except LockError:
                logger.warning(f"Index locked, retrying in {retry_delay}s")
                time.sleep(retry_delay)
        logger.error(f"Failed to sync index after {max_retries} retries")

    @classmethod
    def _pre_process_search_term(cls, term):
        term = term.strip()
        term = re.sub(
            cls.TAGS_WITH_HASH_RE,
            lambda tag: "tags:" + tag.group(0)[1:],
            term,
        )
        return term

    @staticmethod
    def _re_extract(pattern, string) -> Tuple[str, List[str]]:
        matches = []
        text = re.sub(pattern, lambda tag: matches.append(tag.group()), string)
        return (text, matches)

    @staticmethod
    def _strip_ext(filename):
        return os.path.splitext(filename)[0]

    @staticmethod
    def _clear_dir(path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

    def _cleanup_empty_dirs(self, dirpath: str) -> None:
        """Remove empty directories up to (but not including) storage_path."""
        while dirpath and dirpath != self.storage_path:
            try:
                if os.path.isdir(dirpath) and not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    dirpath = os.path.dirname(dirpath)
                else:
                    break
            except OSError:
                break

    def _validate_note_path(self, title: str) -> None:
        """Raise ValueError if title contains invalid characters.
        Unlike the original validator, forward-slash IS allowed for folders."""
        if self.INVALID_PATH_CHARS_RE.search(title):
            raise ValueError(
                "Note title contains invalid characters: <>:\"\\|?*"
            )
        # Prevent path traversal
        if ".." in title.split("/"):
            raise ValueError("Note title must not contain '..'")

    def _search_result_from_hit(self, hit: Hit):
        matched_fields = self._get_matched_fields(hit.matched_terms())

        title = self._strip_ext(hit["filename"])
        last_modified = hit["last_modified"].timestamp()

        score = hit.score if type(hit.score) is float else None

        if "title" in matched_fields:
            hit.results.fragmenter = WholeFragmenter()
            title_highlights = hit.highlights("title", text=title)
        else:
            title_highlights = None

        if "content" in matched_fields:
            hit.results.fragmenter = ContextFragmenter()
            content = self._read_file(self._path_from_title(title))
            content_ex_tags, _ = FileSystemNotes._extract_tags(content)
            content_highlights = hit.highlights(
                "content",
                text=content_ex_tags,
            )
        else:
            content_highlights = None

        tag_matches = (
            [field[1] for field in hit.matched_terms() if field[0] == "tags"]
            if "tags" in matched_fields
            else None
        )

        return SearchResult(
            title=title,
            last_modified=last_modified,
            score=score,
            title_highlights=title_highlights,
            content_highlights=content_highlights,
            tag_matches=tag_matches,
        )

    def _fieldnames_for_term(self, term: str) -> List[str]:
        fields = ["title", "content"]
        if '"' not in term:
            fields.append("tags")
        return fields

    @staticmethod
    def _get_matched_fields(matched_terms):
        return set([matched_term[0] for matched_term in matched_terms])

    @staticmethod
    def _read_file(filepath: str):
        logger.debug(f"Reading from '{filepath}'")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    @staticmethod
    def _add_tag(content: str, tag: str) -> str:
        """Prepend a #tag near the top of the note (after the first heading,
        or at the very top if no heading exists), skipping if already present."""
        import re as _re
        tag_token = f"#{tag}"
        if tag_token in content:
            return content
        lines = content.split("\n")
        # Find the first heading line (starts with #<space> or ##...)
        insert_after = -1
        for i, line in enumerate(lines):
            if _re.match(r"^#{1,6}\s", line):
                insert_after = i
                break
        if insert_after >= 0:
            # Insert tag on the line immediately after the heading
            lines.insert(insert_after + 1, tag_token)
            return "\n".join(lines)
        # No heading — prepend at top
        return tag_token + "\n" + content

    @staticmethod
    def _remove_tag(content: str, tag: str) -> str:
        """Remove all occurrences of #tag from the note content."""
        import re as _re
        tag_token = f"#{tag}"
        # Remove tag on its own line
        pattern = r"(?m)^[ \t]*" + _re.escape(tag_token) + r"[ \t]*$\n?"
        content = _re.sub(pattern, "", content)
        # Remove inline occurrences
        content = content.replace(" " + tag_token + " ", " ")
        content = content.replace(" " + tag_token, "")
        content = content.replace(tag_token + " ", "")
        return content.rstrip("\n").rstrip() + "\n" if content.strip() else content

    def _meta_path(self, title: str) -> str:
        """Return the sidecar .meta.json path for the given note title (now inside .metadata)."""
        folder = os.path.dirname(title)
        basename = os.path.basename(title)
        if folder:
            meta_dir = os.path.join(self.storage_path, folder, METADATA_DIR)
        else:
            meta_dir = os.path.join(self.storage_path, METADATA_DIR)
        return os.path.join(meta_dir, basename + META_EXT)

    def _read_meta(self, title: str) -> dict:
        """Read the sidecar metadata file for a note.
        Returns {} if the file does not exist (e.g. pre-existing notes)."""
        path = self._meta_path(title)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                import json as _json
                return _json.load(f)
        except Exception:
            return {}

    def _write_meta(self, title: str, meta: dict) -> None:
        """Write the sidecar metadata file for a note."""
        import json as _json
        path = self._meta_path(title)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(meta, f, indent=2)

    def _delete_meta(self, title: str) -> None:
        """Delete the sidecar metadata file if it exists."""
        path = self._meta_path(title)
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def _write_file(filepath: str, content: str, overwrite: bool = False):
        logger.debug(f"Writing to '{filepath}'")
        with open(filepath, "w" if overwrite else "x", encoding="utf-8") as f:
            f.write(content or "")

    # ---------- Migration ----------
    def _migrate_metadata(self):
        """Move legacy .meta.json files from alongside .md files into .metadata subfolders."""
        logger.info("Checking for legacy metadata files to migrate...")
        migrated_count = 0
        for dirpath, _, filenames in os.walk(self.storage_path):
            # Skip hidden directories (like .metadata itself)
            if os.path.basename(dirpath).startswith('.'):
                continue
            for fname in filenames:
                if not fname.endswith(MARKDOWN_EXT):
                    continue
                full_md = os.path.join(dirpath, fname)
                rel_md = os.path.relpath(full_md, self.storage_path)
                title = self._strip_ext(rel_md.replace(os.sep, '/'))
                old_meta = os.path.join(dirpath, self._strip_ext(fname) + META_EXT)
                if not os.path.exists(old_meta):
                    continue
                new_meta = self._meta_path(title)
                if os.path.exists(new_meta):
                    # If both exist, keep the new one and delete old to avoid conflicts
                    logger.warning(f"Both old and new metadata exist for {title}. Removing old.")
                    os.remove(old_meta)
                    continue
                os.makedirs(os.path.dirname(new_meta), exist_ok=True)
                shutil.move(old_meta, new_meta)
                migrated_count += 1
                logger.debug(f"Migrated {old_meta} -> {new_meta}")
        if migrated_count:
            logger.info(f"Migrated {migrated_count} legacy metadata files.")
        else:
            logger.info("No legacy metadata files found.")