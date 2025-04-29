class NotificationException(Exception):
    def __init__(self, message):
        super().__init__(message)


class NoSuchNotificationException(NotificationException):
    def __init__(self, message):
        super().__init__(message)