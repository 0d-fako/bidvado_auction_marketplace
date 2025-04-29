from typing import List
# from datetime import datetime

from .interfaces.notification_service import INotificationService
from ..data.repositories.notification_repository import NotificationRepository
from ..data.repositories.auction_repository import AuctionRepository
from ..data.repositories.user_repository import UserRepository
from ..data.repositories.bid_repository import BidRepository
from ..dtos.notification_dto import NotificationResponse, NotificationListResponse
from ..data.models.enum.enums import NotificationType
from ..exceptions.auction_exceptions import AuctionNotFoundException
from ..websockets.websocket_handler import WebSocketHandler


class NotificationService(INotificationService):
    def __init__(
            self,
            notification_repository: NotificationRepository,
            auction_repository: AuctionRepository,
            user_repository: UserRepository,
            bid_repository: BidRepository,
            websocket_handler: WebSocketHandler
    ):
        self.notification_repository = notification_repository
        self.auction_repository = auction_repository
        self.user_repository = user_repository
        self.bid_repository = bid_repository
        self.websocket_handler = websocket_handler

    def create_notification(
            self,
            user_id: str,
            auction_id: str,
            type: NotificationType,
            message: str
    ) -> NotificationResponse:

        notification_id = self.notification_repository.create(
            user_id=user_id,
            message=message,
            type=type,
            auction_id=auction_id
        )


        notification = self.notification_repository.find_by_id(notification_id)


        notification_dto = self._map_to_dto(notification)

        self._send_notification(notification_dto)

        return notification_dto

    def get_user_notifications(
            self,
            user_id: str,
            page: int = 1,
            page_size: int = 10
    ) -> NotificationListResponse:

        notifications = self.notification_repository.find_by_user(
            user_id=user_id,
            page=page,
            page_size=page_size
        )


        unread_count = self.notification_repository.count_unread(user_id)


        notification_dtos = [self._map_to_dto(notification) for notification in notifications]

        return NotificationListResponse(
            notifications=notification_dtos,
            unread_count=unread_count
        )

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:

        notification = self.notification_repository.find_by_id(notification_id)
        if not notification:
            return False

        if str(notification.user.id) != user_id:
            return False


        updated_notification = self.notification_repository.mark_as_read(notification_id)
        if not updated_notification:
            return False

        unread_count = self.notification_repository.count_unread(user_id)
        self._send_unread_count(user_id, unread_count)
        return True

    def mark_all_as_read(self, user_id: str) -> int:

        notifications = self.notification_repository.find_by_user(user_id)

        count = 0
        for notification in notifications:
            if not notification.is_read:
                if self.notification_repository.mark_as_read(str(notification.id)):
                    count += 1

        if count > 0:
            self._send_unread_count(user_id, 0)

        return count

    def notify_outbid(self, auction_id: str, previous_bidder_id: str, new_bid_amount: float) -> bool:
        try:

            auction = self.auction_repository.find_by_id(auction_id)
            if not auction:
                return False

            message = f"You have been outbid on '{auction.title}'. The new highest bid is ${new_bid_amount:.2f}"


            self.create_notification(
                user_id=previous_bidder_id,
                auction_id=auction_id,
                type=NotificationType.OUTBID,
                message=message
            )

            return True
        except Exception as e:
            print(f"Error sending outbid notification: {str(e)}")
            return False

    def notify_auction_ended(self, auction_id: str) -> List[str]:
        notification_ids = []

        try:
            auction = self.auction_repository.find_by_id(auction_id)
            if not auction:
                raise AuctionNotFoundException("Auction not found")


            auctioneer_id = str(auction.auctioneer.id)
            auctioneer_message = f"Your auction '{auction.title}' has ended."

            highest_bid = self.bid_repository.find_highest_bid(auction_id)

            if highest_bid:
                winner_id = str(highest_bid.bidder.id)
                winning_amount = float(highest_bid.amount)

                auctioneer_message += f" It was won by {highest_bid.bidder.username} with a bid of ${winning_amount:.2f}"

                winner_notification = self.create_notification(
                    user_id=winner_id,
                    auction_id=auction_id,
                    type=NotificationType.AUCTION_WON,
                    message=f"Congratulations! You won the auction '{auction.title}' with a bid of ${winning_amount:.2f}"
                )
                notification_ids.append(winner_notification.id)
            else:

                auctioneer_message += " It ended with no bids."

            auctioneer_notification = self.create_notification(
                user_id=auctioneer_id,
                auction_id=auction_id,
                type=NotificationType.AUCTION_ENDED,
                message=auctioneer_message
            )
            notification_ids.append(auctioneer_notification.id)

            return notification_ids
        except Exception as e:
            print(f"Error sending auction ended notifications: {str(e)}")
            return notification_ids

    def _map_to_dto(self, notification) -> NotificationResponse:
        return NotificationResponse(
            id=str(notification.id),
            auction_id=str(notification.auction.id) if notification.auction else None,
            type=notification.type,
            user_id=str(notification.user.id),
            message=notification.message,
            created_at=notification.created_at,
            is_read=notification.is_read
        )

    def _send_notification(self, notification: NotificationResponse):
        if self.websocket_handler:
            self.websocket_handler.emit_to_user(
                user_id=notification.user_id,
                event="notification",
                data=notification.__dict__
            )

    def _send_unread_count(self, user_id: str, count: int):
        if self.websocket_handler:
            self.websocket_handler.emit_to_user(
                user_id=user_id,
                event="notification_count",
                data={"count": count}
            )