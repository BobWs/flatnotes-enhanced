from abc import ABC, abstractmethod
from typing import Literal

from .models import Note, NoteCreate, NoteUpdate, SearchResult


class BaseNotes(ABC):
    @abstractmethod
    def create(self, data: NoteCreate) -> Note:
        """Create a new note."""
        pass

    @abstractmethod
    def get(self, title: str) -> Note:
        """Get a specific note."""
        pass

    @abstractmethod
    def update(self, title: str, new_data: NoteUpdate) -> Note:
        """Update a specific note."""
        pass

    @abstractmethod
    def delete(self, title: str) -> None:
        """Delete a specific note."""
        pass

    @abstractmethod
    def search(
        self,
        term: str,
        sort: Literal["score", "title", "last_modified"] = "score",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        include_archived: bool = False,
        include_trash: bool = False,
    ) -> list[SearchResult]:
        """Search for notes."""
        pass

    @abstractmethod
    def get_tags(self, include_archived: bool = False) -> dict[str, int]:
        """Get a dict of tag -> note count for all indexed tags."""
        pass

    @abstractmethod
    def get_folders(self) -> dict:
        """Get a dict of folder -> note count for all folders."""
        pass