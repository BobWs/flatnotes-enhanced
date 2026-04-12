from typing import List, Optional
import re

from pydantic import Field, field_validator
from typing_extensions import Annotated

from helpers import CustomBaseModel, strip_whitespace

# Characters that are invalid in note paths.
# Forward-slash is intentionally excluded so folder paths like "work/todo" work.
INVALID_NOTE_PATH_CHARS = re.compile(r'[<>:"\\|?*]')


def is_valid_note_path(value: str) -> str:
    """Raise ValueError if value contains characters invalid for note paths."""
    if INVALID_NOTE_PATH_CHARS.search(value):
        raise ValueError(
            'Note path cannot include any of the following characters: <>:"\\|?*'
        )
    if ".." in value.split("/"):
        raise ValueError("Note path must not contain '..'")
    return value


class NoteBase(CustomBaseModel):
    title: str


class NoteCreate(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        v = strip_whitespace(v)
        return is_valid_note_path(v)


class Note(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)
    last_modified: float
    # ISO 8601 timestamps from sidecar .meta.json file.
    # None for notes that predate this feature (created before upgrade).
    created: Optional[str] = Field(None)
    updated: Optional[str] = Field(None)


class NoteUpdate(CustomBaseModel):
    new_title: Optional[str] = Field(None)
    new_content: Optional[str] = Field(None)

    @field_validator("new_title")
    @classmethod
    def validate_new_title(cls, v):
        if v is None:
            return v
        v = strip_whitespace(v)
        return is_valid_note_path(v)


class SearchResult(CustomBaseModel):
    title: str
    last_modified: float

    score: Optional[float] = Field(None)
    title_highlights: Optional[str] = Field(None)
    content_highlights: Optional[str] = Field(None)
    tag_matches: Optional[List[str]] = Field(None)
