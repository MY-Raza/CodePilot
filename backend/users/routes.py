from fastapi import APIRouter, Depends, HTTPException, status

from backend.authentication.dependencies import get_current_active_user
from backend.core.constants import ApiTag
from backend.database.models.user import User
from backend.users.schemas import (
    ChangePasswordRequest,
    DeleteAccountResponse,
    PasswordChangeResponse,
    UserProfileResponse,
    UserUpdateRequest,
)
from backend.users.service import (
    EmailAlreadyTakenError,
    IncorrectCurrentPasswordError,
    InactiveAccountError,
    UsernameAlreadyTakenError,
    UserService,
    get_user_service,
)

router = APIRouter(prefix="/users", tags=[ApiTag.USERS.value])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get the current user's profile",
    description=(
        "Returns the authenticated user's profile. Sensitive fields such "
        "as the password hash are never included in the response."
    ),
)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Return the authenticated user's profile.

    Args:
        current_user: The authenticated, active user.
        user_service: The injected user management service.

    Returns:
        The current user's profile.

    Raises:
        HTTPException: 403 if the account has been deactivated.
    """
    try:
        return user_service.get_current_profile(current_user)
    except InactiveAccountError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.put(
    "/me",
    response_model=UserProfileResponse,
    summary="Update the current user's profile",
    description=(
        "Partially updates the authenticated user's profile. Only fields "
        "included in the request body are changed; omitted fields are "
        "left untouched. Validates email and username uniqueness when "
        "either is being changed."
    ),
)
def update_my_profile(
    update_request: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Apply a partial update to the authenticated user's profile.

    Args:
        update_request: The partial profile update payload.
        current_user: The authenticated, active user.
        user_service: The injected user management service.

    Returns:
        The updated user profile.

    Raises:
        HTTPException: 409 if the requested email or username is already
            taken by another account.
    """
    try:
        return user_service.update_profile(current_user, update_request)
    except (EmailAlreadyTakenError, UsernameAlreadyTakenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.put(
    "/me/password",
    response_model=PasswordChangeResponse,
    summary="Change the current user's password",
    description=(
        "Verifies the supplied current password, validates the new "
        "password's strength, and replaces the stored password hash."
    ),
)
def change_my_password(
    change_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> PasswordChangeResponse:
    """Change the authenticated user's password.

    Args:
        change_request: The current/new password payload.
        current_user: The authenticated, active user.
        user_service: The injected user management service.

    Returns:
        A confirmation message.

    Raises:
        HTTPException: 401 if the current password is incorrect.
    """
    try:
        user_service.change_password(current_user, change_request)
    except IncorrectCurrentPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return PasswordChangeResponse()


@router.delete(
    "/me",
    response_model=DeleteAccountResponse,
    summary="Delete the current user's account",
    description=(
        "Soft-deletes the authenticated user's account: the database "
        "record is never physically removed. The account is deactivated "
        "and timestamped as deleted, and can no longer authenticate."
    ),
)
def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> DeleteAccountResponse:
    """Soft-delete the authenticated user's account.

    Args:
        current_user: The authenticated, active user.
        user_service: The injected user management service.

    Returns:
        A confirmation message including the deletion timestamp.
    """
    deleted_user = user_service.delete_account(current_user)
    return DeleteAccountResponse(deleted_at=deleted_user.deleted_at)


# ---------------------------------------------------------------------------
# Avatar Upload — Placeholder
# ---------------------------------------------------------------------------
# Not yet implemented. Reserved for future integration with object storage
# (e.g. S3-compatible storage). For now, clients should set `avatar_url`
# directly via `PUT /users/me` once an image has been uploaded elsewhere.
@router.post(
    "/me/avatar",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Upload a profile avatar (not yet implemented)",
    description=(
        "Placeholder endpoint reserved for future avatar upload support "
        "backed by object storage. Currently returns 501 Not Implemented. "
        "In the meantime, set `avatar_url` directly via `PUT /users/me`."
    ),
    include_in_schema=True,
)
def upload_my_avatar(
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Reserved placeholder for future avatar upload functionality.

    Args:
        current_user: The authenticated, active user.

    Raises:
        HTTPException: 501, always, until object storage integration is
            implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Avatar upload is not yet implemented. Set 'avatar_url' via "
            "PUT /users/me in the meantime."
        ),
    )