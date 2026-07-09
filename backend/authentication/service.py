import uuid

from backend.authentication.jwt import TokenType, create_access_token, create_refresh_token, verify_token
from backend.authentication.repository import UserRepository
from backend.authentication.schemas import RegisterRequest, Token, UserLogin
from backend.authentication.security import hash_password, verify_password
from backend.database.models.user import User


class UserAlreadyExistsError(Exception):
    """Raised when registering with an email or username already in use."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials do not match a known user."""


class InactiveUserError(Exception):
    """Raised when an authentication action is attempted by an inactive user."""


class UserNotFoundError(Exception):
    """Raised when a token references a user ID that no longer exists."""


class AuthService:
    """Coordinates registration, login, and token refresh business logic."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service with a user repository.

        Args:
            repository: The data-access layer for user records.
        """
        self._repository = repository

    def register_user(self, registration: RegisterRequest) -> User:
        """Register a new user after validating uniqueness constraints.

        Args:
            registration: The validated registration request payload.

        Returns:
            The newly created `User`.

        Raises:
            UserAlreadyExistsError: If the email or username is already
                registered.
        """
        if self._repository.get_user_by_email(registration.email) is not None:
            raise UserAlreadyExistsError(
                "An account with this email already exists."
            )
        if self._repository.get_user_by_username(registration.username) is not None:
            raise UserAlreadyExistsError("This username is already taken.")

        hashed_password = hash_password(registration.password)
        return self._repository.create_user(registration, hashed_password)

    def authenticate_user(self, credentials: UserLogin) -> User:
        """Verify a user's login credentials.

        Args:
            credentials: The email/password pair supplied at login.

        Returns:
            The authenticated `User`.

        Raises:
            InvalidCredentialsError: If the email or password is incorrect.
            InactiveUserError: If the account has been deactivated.
        """
        user = self._repository.get_user_by_email(credentials.email)
        if user is None or not verify_password(credentials.password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password.")
        if not user.is_active:
            raise InactiveUserError("This account has been deactivated.")
        return user

    def issue_tokens(self, user: User) -> Token:
        """Issue a fresh access/refresh token pair for a user.

        Args:
            user: The user to issue tokens for.

        Returns:
            A `Token` containing the new access and refresh tokens.
        """
        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        refresh_token = create_refresh_token(subject=str(user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)

    def refresh_access_token(self, refresh_token: str) -> Token:
        """Exchange a valid refresh token for a new token pair.

        The refresh token is rotated (a new one is issued alongside the new
        access token) to limit the usable lifetime of any single refresh
        token if it were to leak.

        Args:
            refresh_token: The refresh token supplied by the client.

        Returns:
            A `Token` containing the new access and refresh tokens.

        Raises:
            TokenExpiredError: If the refresh token has expired.
            InvalidTokenError: If the refresh token is malformed, invalid,
                or not actually a refresh token.
            UserNotFoundError: If the token's subject no longer maps to a
                user.
            InactiveUserError: If the account has been deactivated.
        """
        payload = verify_token(refresh_token, expected_type=TokenType.REFRESH)

        user = self._repository.get_user_by_id(uuid.UUID(payload.sub))
        if user is None:
            raise UserNotFoundError(
                "The user associated with this token no longer exists."
            )
        if not user.is_active:
            raise InactiveUserError("This account has been deactivated.")

        return self.issue_tokens(user)