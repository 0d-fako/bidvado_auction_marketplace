class BidException(Exception):
    def __init__(self, message="Bid error"):
        self.message = message
        super().__init__(message)

class InvalidBidException(BidException):
    def __init__(self, message="Invalid bid amount"):
        super().__init__(message)

class AuctionClosedException(BidException):
    def __init__(self, message="Cannot bid on closed auction"):
        super().__init__(message)