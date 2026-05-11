from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.http_utils import api_error, parse_iso_datetime, try_parse_iso_datetime
from app.models import Attendance, Event
from app.registration import try_register_user_for_event

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("", methods=["GET"])
def get_calendar_events():
    """Get events formatted for calendar view."""
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    department_id = request.args.get("department_id", type=int)

    query = Event.query.filter_by(is_active=True)

    # Parse and apply date filters
    if start_date:
        start, err = try_parse_iso_datetime(start_date, "start")
        if err:
            return err
        query = query.filter(Event.start_time >= start)

    if end_date:
        end, err = try_parse_iso_datetime(end_date, "end")
        if err:
            return err
        query = query.filter(Event.end_time <= end)

    if department_id:
        query = query.filter_by(department_id=department_id)

    events = query.all()

    # Format for FullCalendar
    calendar_events = []
    for event in events:
        calendar_events.append(
            {
                "id": event.id,
                "title": event.title,
                "start": event.start_time.isoformat(),
                "end": event.end_time.isoformat(),
                "description": event.description,
                "location": event.location,
                "department": event.department.name if event.department else None,
                "backgroundColor": get_department_color(event.department_id),
                "borderColor": get_department_color(event.department_id),
            }
        )

    return jsonify({"events": calendar_events}), 200


@calendar_bp.route("/conflicts", methods=["POST"])
def check_conflicts():
    """Check for scheduling conflicts with other events."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Expected a JSON object in the request body.", 400, code="INVALID_JSON")

    if not data.get("start_time") or not data.get("end_time"):
        return api_error("Start time and end time required", 400, code="MISSING_FIELD")

    try:
        start_time = parse_iso_datetime(data["start_time"], "start_time")
        end_time = parse_iso_datetime(data["end_time"], "end_time")
    except ValueError as e:
        return api_error(str(e), 400, code="INVALID_DATETIME")

    # Find overlapping events
    conflicts = Event.query.filter(
        Event.is_active == True,  # noqa: E712
        Event.start_time < end_time,
        Event.end_time > start_time,
    ).all()

    # Exclude the event being edited if event_id is provided
    event_id = data.get("event_id")
    if event_id:
        conflicts = [e for e in conflicts if e.id != event_id]

    return (
        jsonify(
            {
                "has_conflicts": len(conflicts) > 0,
                "conflicts": [event.to_dict() for event in conflicts],
                "conflict_count": len(conflicts),
            }
        ),
        200,
    )


@calendar_bp.route("/upcoming", methods=["GET"])
def get_upcoming_events():
    """Get upcoming events for the next 7 days."""
    days = request.args.get("days", 7, type=int)
    department_id = request.args.get("department_id", type=int)

    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    query = Event.query.filter(
        Event.is_active == True,  # noqa: E712
        Event.start_time >= now,
        Event.start_time <= end_date,
    ).order_by(Event.start_time.asc())

    if department_id:
        query = query.filter_by(department_id=department_id)

    events = query.all()

    return jsonify({"events": [event.to_dict() for event in events], "count": len(events)}), 200


def get_department_color(department_id):
    """Get a consistent color for a department."""
    colors = [
        "#3788d8",  # Blue
        "#f39c12",  # Orange
        "#27ae60",  # Green
        "#e74c3c",  # Red
        "#9b59b6",  # Purple
        "#1abc9c",  # Turquoise
        "#e67e22",  # Carrot
        "#34495e",  # Dark Gray
    ]
    if department_id:
        return colors[department_id % len(colors)]
    return colors[0]


@calendar_bp.route("/events", methods=["GET"])
@login_required
def get_my_calendar_events():
    """Get current user's registered events."""
    # Get all events the user has registered for
    attendances = Attendance.query.filter_by(user_id=current_user.id).all()
    event_ids = [a.event_id for a in attendances]

    events = (
        Event.query.filter(Event.id.in_(event_ids), Event.is_active == True)  # noqa: E712
        .order_by(Event.start_time.asc())
        .all()
    )

    return jsonify({"events": [event.to_dict() for event in events]}), 200


@calendar_bp.route("/events", methods=["POST"])
@login_required
def add_to_calendar():
    """Add an event to user's calendar (register for event)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Expected a JSON object in the request body.", 400, code="INVALID_JSON")

    event_id = data.get("event_id")

    if not event_id:
        return api_error("Event ID required", 400, code="MISSING_FIELD")

    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    _, err = try_register_user_for_event(
        current_user.id,
        event,
        check_in_method="web_registration",
        duplicate_message="Already added to calendar",
    )
    if err:
        return err

    return jsonify({"message": "Event added to calendar"}), 201


@calendar_bp.route("/events/<int:event_id>", methods=["DELETE"])
@login_required
def remove_from_calendar(event_id):
    """Remove an event from user's calendar."""
    attendance = Attendance.query.filter_by(event_id=event_id, user_id=current_user.id).first()

    if not attendance:
        return api_error("Event not in calendar", 404, code="NOT_FOUND")

    db.session.delete(attendance)
    db.session.commit()

    return jsonify({"message": "Event removed from calendar"}), 200


@calendar_bp.route("/statistics", methods=["GET"])
@login_required
def get_calendar_statistics():
    """Get statistics for user's calendar."""
    # Get user's attendances
    attendances = Attendance.query.filter_by(user_id=current_user.id).all()
    event_ids = [a.event_id for a in attendances]

    total_events = len(event_ids)

    # Get upcoming events
    now = datetime.utcnow()
    upcoming_events = Event.query.filter(
        Event.id.in_(event_ids) if event_ids else Event.id == None,  # noqa: E711
        Event.start_time >= now,
        Event.is_active == True,  # noqa: E712
    ).count()

    # Calculate total points (if events have points)
    total_points = 0

    return (
        jsonify(
            {
                "total_events": total_events,
                "upcoming_events": upcoming_events,
                "total_points": total_points,
            }
        ),
        200,
    )
