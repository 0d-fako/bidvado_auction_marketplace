from dataclasses import dataclass
from datetime import datetime
from ..data.models.enum.enums import NotificationType

@dataclass
class NotificationResponse:
    id: str
    auction_id: str
    type: NotificationType
    user_id: str
    message: str
    created_at: datetime
    is_read: bool = False

@dataclass
class NotificationListResponse:
    notifications: list[NotificationResponse]
    unread_count: int