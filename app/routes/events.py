import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.http_utils import (
    api_error,
    department_admin_event_forbidden,
    paginated_response,
    parse_iso_datetime,
    try_parse_iso_datetime,
)
from app.models import Attendance, Department, Event, User
from app.registration import try_register_user_for_event
from app.utils import generate_qr_code, require_role

events_bp = Blueprint("events", __name__)


@events_bp.route("", methods=["GET"])
def get_events():
    """Get all events with optional filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    department_id = request.args.get("department_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "date")  # date, title, capacity

    query = Event.query.filter_by(is_active=True)

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Event.title.ilike(search_pattern))
            | (Event.description.ilike(search_pattern))
            | (Event.location.ilike(search_pattern))
        )

    # Apply filters
    if department_id:
        query = query.filter_by(department_id=department_id)

    if start_date:
        start, err = try_parse_iso_datetime(start_date, "start_date")
        if err:
            return err
        query = query.filter(Event.start_time >= start)

    if end_date:
        end, err = try_parse_iso_datetime(end_date, "end_date")
        if err:
            return err
        query = query.filter(Event.end_time <= end)

    # Apply sorting
    if sort_by == "title":
        query = query.order_by(Event.title.asc())
    elif sort_by == "capacity":
        query = query.order_by(Event.max_capacity.desc())
    else:  # Default to date
        query = query.order_by(Event.start_time.asc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return paginated_response(
        "events",
        [event.to_dict() for event in pagination.items],
        pagination,
    )


@events_bp.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    """Get a specific event by ID."""
    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")
    include_attendees = request.args.get("include_attendees", "false").lower() == "true"
    return jsonify({"event": event.to_dict(include_attendees=include_attendees)}), 200


@events_bp.route("", methods=["POST"])
@login_required
@require_role(["admin", "department_admin"])
def create_event():
    """Create a new event."""
    # Handle both JSON and FormData
    if request.is_json:
        data = request.get_json(silent=True) or {}
        flier_file = None
    else:
        data = request.form.to_dict()
        flier_file = request.files.get("flier")

    # Validation
    required_fields = ["title", "start_time", "end_time", "department_id"]
    for field in required_fields:
        if not data.get(field):
            return api_error(f"Missing required field: {field}", 400, code="MISSING_FIELD")

    try:
        start_time = parse_iso_datetime(data["start_time"], "start_time")
        end_time = parse_iso_datetime(data["end_time"], "end_time")
    except ValueError as e:
        return api_error(str(e), 400, code="INVALID_DATETIME")

    if start_time >= end_time:
        return api_error("Start time must be before end time", 400, code="INVALID_RANGE")

    # Verify department exists
    department = db.session.get(Department, data["department_id"])
    if not department:
        return api_error("Department not found", 404, code="NOT_FOUND")

    # Handle flier upload
    flier_path = None
    if flier_file and flier_file.filename:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("app", "static", "uploads", "fliers")
        os.makedirs(upload_dir, exist_ok=True)

        # Secure filename and save
        filename = secure_filename(flier_file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, filename)
        flier_file.save(file_path)

        # Store relative path for web access
        flier_path = f"/static/uploads/fliers/{filename}"

    # Create event
    event = Event(
        title=data["title"],
        description=data.get("description"),
        location=data.get("location"),
        start_time=start_time,
        end_time=end_time,
        max_capacity=data.get("max_capacity"),
        department_id=data["department_id"],
        created_by=current_user.id,
        flier_path=flier_path,
    )

    db.session.add(event)
    db.session.commit()

    # Generate QR code
    qr_path = generate_qr_code(event.id)
    event.qr_code_path = qr_path
    db.session.commit()

    return jsonify({"message": "Event created successfully", "event": event.to_dict()}), 201


@events_bp.route("/<int:event_id>", methods=["PUT"])
@login_required
@require_role(["admin", "department_admin"])
def update_event(event_id):
    """Update an existing event."""
    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    forbidden = department_admin_event_forbidden(event)
    if forbidden:
        return forbidden

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Expected a JSON object in the request body.", 400, code="INVALID_JSON")

    # Update fields
    if "title" in data:
        event.title = data["title"]
    if "description" in data:
        event.description = data["description"]
    if "location" in data:
        event.location = data["location"]
    if "max_capacity" in data:
        event.max_capacity = data["max_capacity"]

    if "start_time" in data:
        try:
            event.start_time = parse_iso_datetime(data["start_time"], "start_time")
        except ValueError as e:
            return api_error(str(e), 400, code="INVALID_DATETIME")

    if "end_time" in data:
        try:
            event.end_time = parse_iso_datetime(data["end_time"], "end_time")
        except ValueError as e:
            return api_error(str(e), 400, code="INVALID_DATETIME")

    if event.start_time >= event.end_time:
        return api_error("Start time must be before end time", 400, code="INVALID_RANGE")

    db.session.commit()

    return jsonify({"message": "Event updated successfully", "event": event.to_dict()}), 200


@events_bp.route("/<int:event_id>", methods=["DELETE"])
@login_required
@require_role(["admin", "department_admin"])
def delete_event(event_id):
    """Delete (deactivate) an event."""
    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    forbidden = department_admin_event_forbidden(event)
    if forbidden:
        return forbidden

    event.is_active = False
    db.session.commit()

    return jsonify({"message": "Event deleted successfully"}), 200


@events_bp.route("/<int:event_id>/registrations", methods=["GET"])
@login_required
def get_event_registrations(event_id):
    """Get all registrations/attendance for an event (admin only)."""
    if current_user.role not in ["admin", "department_admin"]:
        return api_error("Insufficient permissions to view registrations.", 403, code="FORBIDDEN")

    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    forbidden = department_admin_event_forbidden(event)
    if forbidden:
        return forbidden

    # Get all attendance records for this event
    attendances = (
        Attendance.query.filter_by(event_id=event_id)
        .join(User)
        .order_by(Attendance.checked_in_at.desc())
        .all()
    )

    registrations = []
    for attendance in attendances:
        user = attendance.user
        registrations.append(
            {
                "id": attendance.id,
                "user_id": user.id,
                "user_name": f"{user.first_name} {user.last_name}",
                "user_email": user.email,
                "checked_in_at": attendance.checked_in_at.isoformat()
                if attendance.checked_in_at
                else None,
                "check_in_method": attendance.check_in_method,
            }
        )

    return jsonify({"registrations": registrations, "total": len(registrations)}), 200


@events_bp.route("/<int:event_id>/register", methods=["POST"])
@events_bp.route("/<int:event_id>/registrations", methods=["POST"])  # REST-compliant alias
@login_required
def register_for_event(event_id):
    """Register current user for an event."""
    from app.email import send_registration_confirmation

    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    attendance, err = try_register_user_for_event(
        current_user.id,
        event,
        check_in_method="qr_code",
        duplicate_message="Already registered for this event",
        full_message="Event is full",
    )
    if err:
        return err

    # Send confirmation email
    try:
        send_registration_confirmation(current_user, event)
    except Exception:
        current_app.logger.exception("Failed to send registration confirmation email")

    return (
        jsonify(
            {"message": "Successfully registered for event", "attendance": attendance.to_dict()}
        ),
        201,
    )


@events_bp.route("/<int:event_id>/attendees", methods=["GET"])
@login_required
def get_event_attendees(event_id):
    """Get all attendees for an event."""
    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    forbidden = department_admin_event_forbidden(event)
    if forbidden:
        return forbidden

    attendees = Attendance.query.filter_by(event_id=event_id).all()
    return jsonify({"attendees": [att.to_dict() for att in attendees]}), 200


@events_bp.route("/<int:event_id>/qr-code", methods=["GET"])
@login_required
def get_event_qr_code(event_id):
    """Return URL to a QR code image that points at the event check-in page."""
    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    if current_user.role not in ["admin", "department_admin"]:
        return api_error("Insufficient permissions to view QR codes.", 403, code="FORBIDDEN")

    forbidden = department_admin_event_forbidden(event)
    if forbidden:
        return forbidden

    if not event.qr_code_path:
        event.qr_code_path = generate_qr_code(event.id)
        db.session.commit()

    qr_url = event.qr_code_path

    return (
        jsonify({"qr_code": qr_url, "event_id": event_id, "event_title": event.title}),
        200,
    )
