class BaseSecurityError(Exception):
    """Base class for all security-related errors."""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "A security error occurred."
        super().__init__(message)


class TokenExpiredError(BaseSecurityError):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token has expired.") -> None:
        super().__init__(message)


class InvalidTokenError(BaseSecurityError):
    """Raised when a token is invalid."""

    def __init__(self, message: str = "Invalid token.") -> None:
        super().__init__(message)


class UserNotActiveError(BaseSecurityError):
    """Raised when user account is not active."""

    def __init__(self, message: str = "User account is not active.") -> None:
        super().__init__(message)


class InvalidCredentialsError(BaseSecurityError):
    """Raised when user credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials.") -> None:
        super().__init__(message)


class TokenNotFoundError(BaseSecurityError):
    """Raised when a token is not found in storage."""

    def __init__(self, message: str = "Token not found.") -> None:
        super().__init__(message)


class BaseEmailError(Exception):
    """Base class for all exceptions raised by email notification module."""
    pass
