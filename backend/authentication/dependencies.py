import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.authentication.jwt import InvalidTokenError, TokenExpiredError, TokenType, verify_token
from backend.authentication.repository import UserRepository
from backend.authentication.service import AuthService
from backend.core.settings import API_V1_PREFIX
from backend.database.models.user import User, UserRole
from backend.database.session import get_db

# -----------------------------------------------------------------------
# OAuth2 Scheme
# -----------------------------------------------------------------------
# Points Swagger UI's "Authorize" flow at the login endpoint. The actual
# credential exchange still happens via OAuth2PasswordRequestForm in
# routes.py; this only tells FastAPI where to send the browser-based
# login form and how to extract the bearer token from subsequent requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/auth/login")


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Provide a `UserRepository` bound to the current request's session.

    Args:
        db: The request-scoped database session.

    Returns:
        A `UserRepository` instance.
    """
    return UserRepository(db)


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Provide an `AuthService` wired with its repository dependency.

    Args:
        repository: The request-scoped user repository.

    Returns:
        An `AuthService` instance.
    """
    return AuthService(repository)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Resolve the currently authenticated user from a bearer token.

    Args:
        token: The bearer token extracted from the Authorization header.
        repository: The request-scoped user repository.

    Returns:
        The authenticated `User`.

    Raises:
        HTTPException: 401 if the token is missing, malformed, expired, or
            does not correspond to an existing user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token, expected_type=TokenType.ACCESS)
    except TokenExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise credentials_exception from exc

    user = repository.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Resolve the current user and ensure the account is active.

    Args:
        current_user: The user resolved by `get_current_user`.

    Returns:
        The authenticated, active `User`.

    Raises:
        HTTPException: 401 if the account has been deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
        )
    return current_user


class RoleChecker:
    """Dependency factory enforcing that the current user holds an allowed role.

    This lays the groundwork for future RBAC; it currently performs a
    simple role-membership check with no granular permission logic.

    Example:
        require_admin = RoleChecker([UserRole.ADMIN])

        @router.get("/admin-only", dependencies=[Depends(require_admin)])
        def admin_only_endpoint() -> dict[str, str]:
            ...
    """

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        """Configure the checker with the set of roles permitted access.

        Args:
            allowed_roles: Roles that are permitted to access the
                protected endpoint.
        """
        self._allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """Verify the current user's role is permitted.

        Args:
            current_user: The authenticated, active user.

        Returns:
            The authenticated `User`, if authorized.

        Raises:
            HTTPException: 403 if the user's role is not in the allowed set.
        """
        if current_user.role not in self._allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user