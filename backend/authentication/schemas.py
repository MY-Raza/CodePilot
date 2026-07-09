import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from backend.authentication.security import WeakPasswordError, validate_password_strength
from backend.database.models.user import UserRole


class UserCreate(BaseModel):
    """Internal representation of the data required to create a user.

    Attributes:
        username: Desired unique username.
        email: Unique email address.
        password: Plaintext password (validated for strength, never stored).
        first_name: Optional given name.
        last_name: Optional family name.
    """

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        """Reject passwords that fail the shared strength policy.

        Args:
            value: The candidate plaintext password.

        Returns:
            The validated password, unchanged.

        Raises:
            ValueError: If the password fails strength requirements.
        """
        try:
            validate_password_strength(value)
        except WeakPasswordError as exc:
            raise ValueError(str(exc)) from exc
        return value


class RegisterRequest(UserCreate):
    """Public-facing registration request payload.

    Intentionally kept distinct from `UserCreate` so the API contract can
    evolve independently (e.g. adding a captcha token or terms-of-service
    acceptance flag) without altering the internal service-layer DTO.
    """


class UserLogin(BaseModel):
    """Credentials used to authenticate an existing user.

    Attributes:
        email: The account's registered email address.
        password: The account's plaintext password.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public-facing representation of a user. Never includes credentials.

    Attributes:
        id: The user's unique identifier.
        username: The user's unique username.
        email: The user's email address.
        first_name: Optional given name.
        last_name: Optional family name.
        avatar_url: Optional profile image URL.
        role: The user's authorization role.
        is_active: Whether the account can currently authenticate.
        is_verified: Whether the user's email has been verified.
        created_at: Timestamp the account was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


class Token(BaseModel):
    """A pair of issued JWT tokens.

    Attributes:
        access_token: Short-lived token used to authenticate requests.
        refresh_token: Long-lived token used to obtain new access tokens.
        token_type: The token scheme, always "bearer".
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(Token):
    """Response returned upon successful login.

    Attributes:
        user: The authenticated user's public profile.
    """

    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded claims of a JWT issued by this application.

    Attributes:
        sub: The subject claim — the authenticated user's ID, as a string.
        type: The token type, either "access" or "refresh".
        role: The user's role at the time of token issuance, if present.
        exp: Expiration time, as a Unix timestamp.
        iat: Issued-at time, as a Unix timestamp.
        jti: Unique token identifier.
    """

    model_config = ConfigDict(extra="ignore")

    sub: str
    type: str
    role: str | None = None
    exp: int
    iat: int | None = None
    jti: str | None = None


class RefreshTokenRequest(BaseModel):
    """Request body for the token refresh endpoint.

    Attributes:
        refresh_token: A valid, unexpired refresh token.
    """

    refresh_token: str