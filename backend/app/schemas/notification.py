from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    is_read: bool
    event_key: Optional[str] = None
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationRead]
    unread_count: int
