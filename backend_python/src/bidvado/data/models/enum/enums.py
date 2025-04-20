from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    AUCTIONEER = "auctioneer"
    BIDDER = "bidder"


class AuctionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationType(Enum):
    OUTBID = "outbid"
    AUCTION_WON = "auction_won"
    AUCTION_ENDED = "auction_ended"
    APPROVAL_NEEDED = "approval_needed"
    BID_PLACED = "bid_placed"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"