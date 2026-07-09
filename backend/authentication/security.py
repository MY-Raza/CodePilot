import re

from passlib.context import CryptContext

# -----------------------------------------------------------------------
# Password Hashing Context
# -----------------------------------------------------------------------
# bcrypt is used exclusively. `deprecated="auto"` allows future schemes to
# be added to `schemes` and have passlib automatically flag/upgrade hashes
# produced by older, deprecated schemes on next verification.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_PASSWORD_MIN_LENGTH = 8

# Requires at least one lowercase letter, one uppercase letter, one digit,
# and one special (non-word, non-whitespace) character.
_PASSWORD_PATTERN = re.compile(
    rf"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{{{_PASSWORD_MIN_LENGTH},}}$"
)


class WeakPasswordError(ValueError):
    """Raised when a candidate password fails strength requirements."""


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plain_password: The user-supplied plaintext password.

    Returns:
        A bcrypt password hash suitable for persistent storage.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The plaintext password supplied at login.
        hashed_password: The bcrypt hash stored for the user.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> None:
    """Validate that a password meets minimum strength requirements.

    Requires at least 8 characters, one uppercase letter, one lowercase
    letter, one digit, and one special character.

    Args:
        password: The plaintext password to validate.

    Raises:
        WeakPasswordError: If the password does not meet the requirements.
    """
    if not _PASSWORD_PATTERN.match(password):
        raise WeakPasswordError(
            "Password must be at least 8 characters long and include an "
            "uppercase letter, a lowercase letter, a digit, and a special "
            "character."
        )