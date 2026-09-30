"""
CampusHub - Academic Resource & Peer Study Group Scheduling System
Core Exceptions Module
"""

class CampusHubException(Exception):
    """Base exception for all domain-specific CampusHub errors."""
    pass


class AuthenticationError(CampusHubException):
    """Raised when authentication or token validation fails."""
    pass


class PermissionDeniedError(CampusHubException):
    """Raised when an operation violates Role-Based Access Control (RBAC)."""
    pass


class ValidationError(CampusHubException):
    """Raised when input validation constraints are violated."""
    pass


class SchedulingConflictError(CampusHubException):
    """Raised when a session booking clashes with an existing time slot."""
    pass


class ResourceNotFoundError(CampusHubException):
    """Raised when a requested entity (user, group, session, resource) does not exist."""
    pass


class DuplicateEntityError(CampusHubException):
    """Raised when attempting to create an entity that already exists."""
    pass
