class AuctionException(Exception):
    def __init__(self, message="Auction error"):
        self.message = message
        super().__init__(message)

class AuctionNotFoundException(AuctionException):
    def __init__(self, message="Auction not found"):
        super().__init__(message)

class UnauthorizedException(AuctionException):
    def __init__(self, message="Unauthorized action"):
        super().__init__(message)

class InvalidAuctionStateException(AuctionException):
    def __init__(self, message="Invalid auction state for this operation"):
        super().__init__(message)