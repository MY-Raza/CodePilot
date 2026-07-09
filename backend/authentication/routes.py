from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.authentication.dependencies import get_auth_service, get_current_active_user
from backend.authentication.jwt import InvalidTokenError, TokenExpiredError
from backend.authentication.schemas import (
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    Token,
    UserLogin,
    UserResponse,
)
from backend.authentication.service import (
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from backend.core.constants import ApiTag
from backend.database.models.user import User

router = APIRouter(prefix="/auth", tags=[ApiTag.AUTHENTICATION.value])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a new user account after validating email/username "
        "uniqueness and password strength. Returns the created user's "
        "public profile; the password is never included in the response."
    ),
)
def register(
    registration: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Handle user registration requests.

    Args:
        registration: The validated registration payload.
        auth_service: The injected authentication service.

    Returns:
        The newly created user.

    Raises:
        HTTPException: 409 if the email or username is already registered.
    """
    try:
        return auth_service.register_user(registration)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and obtain tokens",
    description=(
        "Verifies user credentials via the OAuth2 password flow and "
        "returns an access token, refresh token, and the user's profile."
    ),
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Handle login requests using the OAuth2 password grant.

    Args:
        form_data: OAuth2 form data; `username` carries the user's email.
        auth_service: The injected authentication service.

    Returns:
        The issued tokens along with the authenticated user's profile.

    Raises:
        HTTPException: 401 if credentials are invalid, 403 if the account
            is inactive.
    """
    credentials = UserLogin(email=form_data.username, password=form_data.password)

    try:
        user = auth_service.authenticate_user(credentials)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

    tokens = auth_service.issue_tokens(user)
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh an access token",
    description=(
        "Exchanges a valid, unexpired refresh token for a new access "
        "token and a rotated refresh token."
    ),
)
def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Handle access token refresh requests.

    Args:
        payload: The request body containing the refresh token.
        auth_service: The injected authentication service.

    Returns:
        A new access/refresh token pair.

    Raises:
        HTTPException: 401 if the token is expired or invalid, 404 if the
            associated user no longer exists, 403 if the account is
            inactive.
    """
    try:
        return auth_service.refresh_access_token(payload.refresh_token)
    except (TokenExpiredError, InvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
    description=(
        "Returns the public profile of the user associated with the "
        "supplied access token."
    ),
)
def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    """Return the currently authenticated user's profile.

    Args:
        current_user: The authenticated, active user resolved from the
            request's bearer token.

    Returns:
        The current user's public profile.
    """
    return current_user