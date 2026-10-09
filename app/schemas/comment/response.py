from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentAuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    rating: int | None
    package_id: int | None
    hotel_id: int | None
    created_at: datetime
    user: CommentAuthorOut
