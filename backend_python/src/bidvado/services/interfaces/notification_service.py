from abc import ABC, abstractmethod
from typing import List

from ...dtos.notification_dto import NotificationResponse, NotificationListResponse
from ...data.models.enum.enums import NotificationType


class INotificationService(ABC):
    @abstractmethod
    def create_notification(self, user_id: str, auction_id: str,
                           type: NotificationType, message: str) -> NotificationResponse:
        pass

    @abstractmethod
    def get_user_notifications(self, user_id: str, page: int = 1,
                              page_size: int = 10) -> NotificationListResponse:
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        pass

    @abstractmethod
    def mark_all_as_read(self, user_id: str) -> int:
        pass

    @abstractmethod
    def notify_outbid(self, auction_id: str, previous_bidder_id: str, new_bid_amount: float) -> bool:
        pass

    @abstractmethod
    def notify_auction_ended(self, auction_id: str) -> List[str]:
        pass