from typing import TypeVar

from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel):
    success: bool
    message: str | None = None
    data: T | None = None

    class Config:
        arbitrary_types_allowed = True