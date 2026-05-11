"""Shared event registration (attendance) logic used by multiple API routes."""

from __future__ import annotations

from typing import Optional, Tuple

from app import db
from app.http_utils import api_error
from app.models import Attendance, Event


def try_register_user_for_event(
    user_id: int,
    event: Event,
    *,
    check_in_method: str = "qr_code",
    duplicate_message: str = "Already registered for this event",
    inactive_message: str = "Event is not active",
    full_message: str = "Event is full",
) -> Tuple[Optional[Attendance], Optional[Tuple]]:
    """
    Create an attendance row for a user and event if business rules pass.

    Returns:
        (Attendance, None) on success,
        (None, (jsonify, status)) on failure.
    """
    if not event.is_active:
        return None, api_error(inactive_message, 400, code="EVENT_INACTIVE")

    existing = Attendance.query.filter_by(event_id=event.id, user_id=user_id).first()
    if existing:
        return None, api_error(duplicate_message, 409, code="ALREADY_REGISTERED")

    if event.max_capacity is not None:
        registered_count = Attendance.query.filter_by(event_id=event.id).count()
        if registered_count >= event.max_capacity:
            return None, api_error(full_message, 400, code="EVENT_FULL")

    attendance = Attendance(
        event_id=event.id,
        user_id=user_id,
        check_in_method=check_in_method,
    )
    db.session.add(attendance)
    db.session.commit()
    return attendance, None
