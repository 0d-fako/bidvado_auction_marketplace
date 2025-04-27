class AuthException(Exception):
    def __init__(self, message="Authentication error"):
        self.message = message
        super().__init__(message)

class InvalidCredentialsException(AuthException):
    def __init__(self, message="Invalid username or password"):
        super().__init__(message)

class UserAlreadyExistsException(AuthException):
    def __init__(self, message="User with this email already exists"):
        super().__init__(message)

class InvalidTokenException(AuthException):
    def __init__(self, message="Invalid authentication token"):
        super().__init__(message)

class ExpiredTokenException(AuthException):
    def __init__(self, message="Token has expired"):
        super().__init__(message)

class NoSuchUserException(AuthException):
    def __init__(self, message="User does not exist"):
        super().__init__(message)

class InvalidActionException(AuthException):
    def __init__(self, message="Invalid action"):
        super().__init__(message)

class TokenVerificationException(AuthException):
    def __init__(self, message="Token verification error"):
        super().__init__(message)

class UserCreationException(AuthException):
    def __init__(self, message="Unable to create new user"):
        super().__init__(message)

class UnauthorizedAccessException(AuthException):
    def __init__(self, message="You do not have permission to perform this action"):
        super().__init__(message)