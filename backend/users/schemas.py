import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from backend.authentication.security import WeakPasswordError, validate_password_strength
from backend.database.models.user import UserRole


class UserProfileResponse(BaseModel):
    """Public-facing profile of the authenticated user.

    Never includes `hashed_password`, soft-delete bookkeeping, or other
    internal/audit fields.

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
        updated_at: Timestamp the account was last updated.
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
    updated_at: datetime


class UserSummary(BaseModel):
    """Lightweight public representation of a user for embedding elsewhere.

    Intended for contexts like "created by" / "assigned to" fields on
    other resources, where the full profile would be excessive.

    Attributes:
        id: The user's unique identifier.
        username: The user's unique username.
        avatar_url: Optional profile image URL.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    avatar_url: str | None = None


class UserUpdateRequest(BaseModel):
    """Partial update payload for a user's profile.

    All fields are optional; only fields explicitly provided by the
    client are applied (`exclude_unset=True` semantics), so omitted
    fields are left untouched rather than reset to their defaults.

    Attributes:
        first_name: New given name, if changing.
        last_name: New family name, if changing.
        username: New unique username, if changing.
        email: New unique email address, if changing.
        avatar_url: New profile image URL, if changing.
    """

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, max_length=512)


class ChangePasswordRequest(BaseModel):
    """Payload for changing the authenticated user's password.

    Attributes:
        current_password: The user's existing plaintext password, used to
            re-authenticate the request before applying the change.
        new_password: The desired new plaintext password. Validated for
            strength before being hashed and persisted.
    """

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def new_password_must_be_strong(cls, value: str) -> str:
        """Reject new passwords that fail the shared strength policy.

        Args:
            value: The candidate new plaintext password.

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


class PasswordChangeResponse(BaseModel):
    """Confirmation returned after a successful password change.

    Attributes:
        message: Human-readable confirmation message.
    """

    message: str = "Password updated successfully."


class DeleteAccountResponse(BaseModel):
    """Confirmation returned after a successful account soft-deletion.

    Attributes:
        message: Human-readable confirmation message.
        deleted_at: Timestamp the account was marked as deleted.
    """

    message: str = "Account deleted successfully."
    deleted_at: datetime