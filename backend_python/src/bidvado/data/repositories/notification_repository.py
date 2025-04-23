from datetime import datetime
from typing import Optional, List, Dict

from ..models.notification import Notification
from ..models.user import User
from ..models.auction import Auction
from ..models.enum.enums import NotificationType
from ...exceptions.auth_exceptions import NoSuchUserException
from ...exceptions.auction_exceptions import AuctionNotFoundException


class NotificationRepository:
    def create(self, user_id: str, message: str,
               type: NotificationType, auction_id: Optional[str] = None) -> str:
        user = User.objects(id=user_id).first()
        if not user:
            raise NoSuchUserException("User not found")

        auction = None
        if auction_id:
            auction = Auction.objects(id=auction_id).first()
            if not auction:
                raise AuctionNotFoundException("Auction not found")

        notification = Notification(
            user=user,
            auction=auction,
            type=type,
            message=message,
            created_at=datetime.now(),
            is_read=False
        ).save()

        return str(notification.id)

    def find_by_user(self, user_id: str, page: int = 1, page_size: int = 10) -> List[Notification]:
        user = User.objects(id=user_id).first()
        if not user:
            raise NoSuchUserException("User not found")

        skip = (page - 1) * page_size
        return list(Notification.objects(user=user).order_by('-created_at').skip(skip).limit(page_size))

    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        notification = Notification.objects(id=notification_id).first()
        if not notification:
            return None
        notification.is_read = True
        notification.save()
        return notification

    def count_unread(self, user_id: str) -> int:
        user = User.objects(id=user_id).first()
        if not user:
            raise NoSuchUserException("User not found")

        return Notification.objects(user=user, is_read=False).count()

    def delete(self, notification_id: str) -> bool:
        notification = Notification.objects(id=notification_id).first()
        if not notification:
            return False

        notification.delete()
        return True
