from fastapi import Depends

from backend.authentication.security import hash_password, verify_password
from backend.database.models.user import User
from backend.users.repository import UserRepository, get_user_repository
from backend.users.schemas import ChangePasswordRequest, UserUpdateRequest


class EmailAlreadyTakenError(Exception):
    """Raised when updating to an email address already used by another user."""


class UsernameAlreadyTakenError(Exception):
    """Raised when updating to a username already used by another user."""


class IncorrectCurrentPasswordError(Exception):
    """Raised when a password change request's current password is wrong."""


class InactiveAccountError(Exception):
    """Raised when an action is attempted against a deactivated account."""


class UserService:
    """Coordinates profile retrieval, updates, and account lifecycle logic."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service with a user repository.

        Args:
            repository: The data-access layer for user profile records.
        """
        self._repository = repository

    def get_current_profile(self, user: User) -> User:
        """Return the current user's profile.

        Args:
            user: The authenticated user, resolved from the request's
                bearer token.

        Returns:
            The user's profile.

        Raises:
            InactiveAccountError: If the account has been deactivated.
        """
        if not user.is_active:
            raise InactiveAccountError("This account has been deactivated.")
        return user

    def update_profile(self, user: User, update_request: UserUpdateRequest) -> User:
        """Apply a partial profile update after validating uniqueness rules.

        Only fields explicitly set on `update_request` are applied; unset
        fields are left untouched.

        Args:
            user: The authenticated user being updated.
            update_request: The partial update payload.

        Returns:
            The updated user profile.

        Raises:
            EmailAlreadyTakenError: If the requested email is already used
                by a different user.
            UsernameAlreadyTakenError: If the requested username is
                already used by a different user.
        """
        fields = update_request.model_dump(exclude_unset=True)

        new_email = fields.get("email")
        if new_email is not None and new_email != user.email:
            if self._repository.check_email_exists(new_email, exclude_user_id=user.id):
                raise EmailAlreadyTakenError(
                    "This email address is already in use by another account."
                )

        new_username = fields.get("username")
        if new_username is not None and new_username != user.username:
            if self._repository.check_username_exists(
                new_username, exclude_user_id=user.id
            ):
                raise UsernameAlreadyTakenError(
                    "This username is already taken."
                )

        if not fields:
            return user

        return self._repository.update_user(user, fields)

    def change_password(self, user: User, request: ChangePasswordRequest) -> None:
        """Verify the current password and persist a new one.

        Password strength for `new_password` is already enforced at the
        schema layer (`ChangePasswordRequest`); this method only handles
        the business rule of verifying the current password before
        allowing the change.

        Args:
            user: The authenticated user changing their password.
            request: The current/new password payload.

        Raises:
            IncorrectCurrentPasswordError: If `current_password` does not
                match the user's stored password hash.
        """
        if not verify_password(request.current_password, user.hashed_password):
            raise IncorrectCurrentPasswordError("The current password is incorrect.")

        new_hashed_password = hash_password(request.new_password)
        self._repository.update_password(user, new_hashed_password)

    def delete_account(self, user: User) -> User:
        """Soft-delete the authenticated user's account.

        The underlying database row is never removed — the account is
        deactivated and timestamped as deleted instead.

        Args:
            user: The authenticated user requesting account deletion.

        Returns:
            The updated user record, reflecting the soft-delete.
        """
        return self._repository.soft_delete_user(user)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Provide a `UserService` wired with its repository dependency.

    Args:
        repository: The request-scoped user repository.

    Returns:
        A `UserService` instance.
    """
    return UserService(repository)