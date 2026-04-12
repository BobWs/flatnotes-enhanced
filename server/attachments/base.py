from abc import ABC, abstractmethod
from typing import List

from fastapi import UploadFile
from fastapi.responses import FileResponse

from .models import AttachmentCreateResponse, AttachmentInfo


class BaseAttachments(ABC):
    @abstractmethod
    def create(self, file: UploadFile) -> AttachmentCreateResponse:
        """Create a new attachment."""
        pass

    @abstractmethod
    def get(self, filename: str) -> FileResponse:
        """Get a specific attachment."""
        pass

    @abstractmethod
    def list_all(self) -> List[AttachmentInfo]:
        """Return info for all attachments, including which notes use each."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> None:
        """Delete an attachment. Raises FileNotFoundError if not found."""
        pass
