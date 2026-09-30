"""
Services package for CampusHub.
"""

from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.services.scheduler_service import SchedulerService
from campushub.services.resource_service import ResourceService
from campushub.services.analytics_service import AnalyticsService
from campushub.services.integrity_service import IntegrityService

__all__ = [
    "AuthService",
    "GroupService",
    "SchedulerService",
    "ResourceService",
    "AnalyticsService",
    "IntegrityService",
]
