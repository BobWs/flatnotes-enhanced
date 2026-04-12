from typing import List, Optional
from helpers import CustomBaseModel


class AttachmentCreateResponse(CustomBaseModel):
    filename: str
    url: str


class AttachmentInfo(CustomBaseModel):
    filename: str
    url: str
    size_bytes: int
    is_image: bool
    is_pdf: bool
    is_document: bool = False   # NEW
    used_in: List[str]