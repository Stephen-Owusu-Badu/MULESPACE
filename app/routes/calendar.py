from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.models import Event

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
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Event.start_time >= start)
        except ValueError:
            return jsonify({"error": "Invalid start date format"}), 400

    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Event.end_time <= end)
        except ValueError:
            return jsonify({"error": "Invalid end date format"}), 400

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
    data = request.get_json()

    if not data.get("start_time") or not data.get("end_time"):
        return jsonify({"error": "Start time and end time required"}), 400

    try:
        start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

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
