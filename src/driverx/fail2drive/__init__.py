"""Agent-facing OODrive extensions over the pinned Fail2Drive submodule."""

from driverx.fail2drive.catalog import (
    Fail2DriveCatalog,
    Fail2DriveScenarioParam,
    Fail2DriveScenarioType,
    load_fail2drive_catalog,
)
from driverx.fail2drive.route_validation import (
    Fail2DriveRouteValidation,
    RouteIssue,
    validate_fail2drive_route,
)

__all__ = [
    "Fail2DriveCatalog",
    "Fail2DriveRouteValidation",
    "Fail2DriveScenarioParam",
    "Fail2DriveScenarioType",
    "RouteIssue",
    "load_fail2drive_catalog",
    "validate_fail2drive_route",
]
