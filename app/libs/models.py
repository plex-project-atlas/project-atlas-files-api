from pydantic import BaseModel, ByteSize
from datetime import datetime
from typing   import List
from pathlib  import Path


class TokenRequest(BaseModel):
    source_platform: str
    source_id:       str

class TokenResponse(BaseModel):
    token: str

class OpsPrefightCheckResult(BaseModel):
    result: bool
    detail: str | None = None

class File(BaseModel):
    name:      str
    path:      Path
    hash:      str      | None = None
    size:      ByteSize | None = None
    mod_date:  datetime | None = None
    mime_type: str      | None = None

class RenameRequest(File):
    new_name: str

class MoveRequest(File):
    new_path: str

class RenameResponse(RenameRequest):
    renamed: bool
    detail:  str | None = None

class MoveResponse(MoveRequest):
    moved:  bool
    detail: str  | None = None

class FileList(BaseModel):
    files: List[File]

class RenameRequestList(BaseModel):
    files: List[RenameRequest]

class MoveRequestList(BaseModel):
    files: List[MoveRequest]

class RenameResponseList(BaseModel):
    files: List[RenameResponse]

class MoveResponseList(BaseModel):
    files: List[MoveResponse]