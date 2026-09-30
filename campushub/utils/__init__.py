"""
Utilities package for CampusHub.
"""
from campushub.utils.exceptions import (
    CampusHubException,
    AuthenticationError,
    PermissionDeniedError,
    ValidationError,
    SchedulingConflictError,
    ResourceNotFoundError,
    DuplicateEntityError,
)
from campushub.utils.validators import (
    validate_email,
    validate_password,
    validate_not_blank,
    validate_datetime_str,
    validate_time_window,
    validate_rating,
)
from campushub.utils.logger import setup_logger

__all__ = [
    "CampusHubException",
    "AuthenticationError",
    "PermissionDeniedError",
    "ValidationError",
    "SchedulingConflictError",
    "ResourceNotFoundError",
    "DuplicateEntityError",
    "validate_email",
    "validate_password",
    "validate_not_blank",
    "validate_datetime_str",
    "validate_time_window",
    "validate_rating",
    "setup_logger",
]
