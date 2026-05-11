"""Shared helpers for JSON APIs: errors, datetime parsing, pagination, authorization checks."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Sequence, Tuple, TypeVar

from flask import jsonify
from flask_login import current_user

T = TypeVar("T")


def api_error(
    message: str,
    status: int = 400,
    *,
    code: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> Tuple[Any, int]:
    """Return a consistent JSON error body for API blueprints."""
    body: dict[str, Any] = {"error": message}
    if code:
        body["code"] = code
    if details:
        body["details"] = details
    return jsonify(body), status


def parse_iso_datetime(value: str, field_name: str = "value") -> datetime:
    """
    Parse ISO-8601 date/time from JSON or query strings.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Invalid date or time for {field_name}. "
            "Use ISO-8601 format (for example 2025-01-15T14:30:00 or 2025-01-15T14:30:00Z)."
        ) from exc


def try_parse_iso_datetime(
    value: Optional[str], field_name: str
) -> Tuple[Optional[datetime], Optional[Tuple[Any, int]]]:
    """
    Parse an optional ISO datetime.

    Returns:
        (datetime, None) on success,
        (None, None) if value is None/empty,
        (None, api_error tuple) on parse failure.
    """
    if not value:
        return None, None
    try:
        return parse_iso_datetime(value, field_name=field_name), None
    except ValueError as e:
        return None, api_error(str(e), 400, code="INVALID_DATETIME")


def paginated_response(
    items_key: str,
    items: Sequence[T],
    pagination,
) -> Tuple[Any, int]:
    """Standard paginated JSON success response."""
    payload = {
        items_key: [item for item in items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }
    return jsonify(payload), 200


def department_admin_event_forbidden(event) -> Optional[Tuple[Any, int]]:
    """
    Enforce that a department admin may only act on events in their department.

    Returns:
        An api_error response tuple if forbidden, otherwise None.
    """
    if (
        current_user.role == "department_admin"
        and event.department_id != current_user.department_id
    ):
        return api_error(
            "You do not have permission to manage this event for another department.",
            403,
            code="FORBIDDEN_DEPARTMENT_SCOPE",
        )
    return None
