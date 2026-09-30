"""
Input validation utilities for CampusHub.
Provides strong validation for emails, passwords, dates, and names.
"""

import re
from datetime import datetime
from campushub.utils.exceptions import ValidationError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
TIME_FORMAT = "%Y-%m-%d %H:%M"


def validate_email(email: str) -> str:
    """Validate university or generic email address format."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email address cannot be empty.")
    cleaned = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValidationError(f"Invalid email format: '{email}'")
    return cleaned


def validate_password(password: str) -> str:
    """
    Validate password strength:
    Must be at least 6 characters and contain both letters and digits.
    """
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least one letter and one number.")
    return password


def validate_not_blank(value: str, field_name: str) -> str:
    """Ensure string field is not empty or whitespace only."""
    if not value or not str(value).strip():
        raise ValidationError(f"{field_name} cannot be blank.")
    return str(value).strip()


def validate_datetime_str(dt_str: str, field_name: str = "Date/Time") -> datetime:
    """Parse and validate datetime formatted as YYYY-MM-DD HH:MM."""
    if not dt_str:
        raise ValidationError(f"{field_name} is required.")
    try:
        return datetime.strptime(dt_str.strip(), TIME_FORMAT)
    except ValueError:
        raise ValidationError(
            f"Invalid format for {field_name}: '{dt_str}'. Expected format: YYYY-MM-DD HH:MM"
        )


def validate_time_window(start_dt: datetime, end_dt: datetime) -> None:
    """Ensure start time precedes end time and duration is at least 15 minutes."""
    if start_dt >= end_dt:
        raise ValidationError("Session start time must be before end time.")
    duration_minutes = (end_dt - start_dt).total_seconds() / 60
    if duration_minutes < 15:
        raise ValidationError("Session duration must be at least 15 minutes.")
    if duration_minutes > 480:
        raise ValidationError("Session duration cannot exceed 8 hours.")


def validate_rating(rating: int) -> int:
    """Validate numeric rating scale (1 to 5)."""
    try:
        r = int(rating)
    except (ValueError, TypeError):
        raise ValidationError("Rating must be an integer between 1 and 5.")
    if r < 1 or r > 5:
        raise ValidationError("Rating must be between 1 and 5 inclusive.")
    return r
