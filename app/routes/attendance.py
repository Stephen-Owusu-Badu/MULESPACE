import csv
import io
from datetime import datetime

from flask import Blueprint, jsonify, make_response, request
from flask_login import current_user, login_required

from app import db
from app.http_utils import api_error, department_admin_event_forbidden, paginated_response
from app.models import Attendance, Department, Event, User
from app.registration import try_register_user_for_event

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/check-in", methods=["POST"])
@attendance_bp.route("", methods=["POST"])  # REST-compliant alias
@login_required
def check_in():
    """Check in a user to an event."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Expected a JSON object with event_id.", 400, code="INVALID_JSON")

    if not data.get("event_id"):
        return api_error("Event ID required", 400, code="MISSING_FIELD")

    event = db.session.get(Event, data["event_id"])
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    attendance, err = try_register_user_for_event(
        current_user.id,
        event,
        check_in_method=data.get("check_in_method", "qr_code"),
        duplicate_message="Already checked in to this event",
        full_message="Event is at full capacity",
    )
    if err:
        return err

    return (
        jsonify({"message": "Checked in successfully", "attendance": attendance.to_dict()}),
        201,
    )


@attendance_bp.route("/my-events", methods=["GET"])
@login_required
def get_my_attended_events():
    """Get all events the current user has attended."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = (
        Attendance.query.filter_by(user_id=current_user.id)
        .order_by(Attendance.checked_in_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return paginated_response(
        "attendances",
        [att.to_dict() for att in pagination.items],
        pagination,
    )


@attendance_bp.route("/event/<int:event_id>/status", methods=["GET"])
@login_required
def get_attendance_status(event_id):
    """Check if current user is checked in to an event."""
    event = db.session.get(Event, event_id)
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    attendance = Attendance.query.filter_by(event_id=event_id, user_id=current_user.id).first()

    return (
        jsonify(
            {
                "checked_in": attendance is not None,
                "attendance": attendance.to_dict() if attendance else None,
            }
        ),
        200,
    )


@attendance_bp.route("/<int:attendance_id>", methods=["DELETE"])
@login_required
def delete_attendance(attendance_id):
    """Remove an attendance record (admin only)."""
    if current_user.role not in ["admin", "department_admin"]:
        return api_error("Insufficient permissions to delete attendance.", 403, code="FORBIDDEN")

    attendance = db.session.get(Attendance, attendance_id)
    if not attendance:
        return api_error("Attendance not found", 404, code="NOT_FOUND")

    forbidden = department_admin_event_forbidden(attendance.event)
    if forbidden:
        return forbidden

    db.session.delete(attendance)
    db.session.commit()

    return jsonify({"message": "Attendance record deleted"}), 200


@attendance_bp.route("/bulk-check-in", methods=["POST"])
@attendance_bp.route("/bulk", methods=["POST"])  # REST-compliant alias
@login_required
def bulk_check_in():
    """Check in multiple users to an event (admin only)."""
    if current_user.role not in ["admin", "department_admin"]:
        return api_error("Insufficient permissions for bulk check-in.", 403, code="FORBIDDEN")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Expected a JSON object in the request body.", 400, code="INVALID_JSON")

    if not data.get("event_id") or not data.get("user_ids"):
        return api_error("Event ID and user IDs required", 400, code="MISSING_FIELD")

    event = db.session.get(Event, data["event_id"])
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    forbidden = department_admin_event_forbidden(event)
    if forbidden:
        return forbidden

    user_ids = data["user_ids"]
    results = {"success": [], "errors": []}

    for user_id in user_ids:
        # Check if already exists
        existing = Attendance.query.filter_by(event_id=event.id, user_id=user_id).first()
        if existing:
            results["errors"].append({"user_id": user_id, "error": "Already checked in"})
            continue

        # Create attendance
        attendance = Attendance(event_id=event.id, user_id=user_id, check_in_method="manual")
        db.session.add(attendance)
        results["success"].append(user_id)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Bulk check-in completed",
                "success_count": len(results["success"]),
                "error_count": len(results["errors"]),
                "results": results,
            }
        ),
        200,
    )


@attendance_bp.route("/check-in-form", methods=["POST"])
def check_in_form():
    """Process check-in form submission (public endpoint for QR code check-ins)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Expected a JSON object in the request body.", 400, code="INVALID_JSON")

    required_fields = ["event_id", "full_name", "email", "department_id"]
    for field in required_fields:
        if not data.get(field):
            label = field.replace("_", " ").title()
            return api_error(f"{label} is required", 400, code="MISSING_FIELD")

    event = db.session.get(Event, data["event_id"])
    if not event:
        return api_error("Event not found", 404, code="NOT_FOUND")

    # Check if event is active
    if not event.is_active:
        return api_error("Event is not active", 400, code="EVENT_INACTIVE")

    # Try to find user by email
    user = User.query.filter_by(email=data["email"]).first()

    if user:
        # Existing user - check if already checked in
        existing = Attendance.query.filter_by(event_id=event.id, user_id=user.id).first()
        if existing:
            return api_error(
                "You have already checked in to this event",
                409,
                code="ALREADY_REGISTERED",
            )

        # Create attendance record
        attendance = Attendance(event_id=event.id, user_id=user.id, check_in_method="qr_form")
    else:
        # Guest check-in (no user account) - we'll still record it
        # For now, we'll skip this and require users to have accounts
        return api_error("Please register for an account first", 400, code="ACCOUNT_REQUIRED")

    db.session.add(attendance)
    db.session.commit()

    return jsonify({"message": "Check-in successful", "attendance": attendance.to_dict()}), 201


@attendance_bp.route("/export/<int:event_id>", methods=["GET"])
@login_required
def export_attendance(event_id):
    """Export attendance data for an event as CSV (admin only)."""
    if current_user.role not in ["admin", "department_admin"]:
        return api_error("Insufficient permissions to export attendance.", 403, code="FORBIDDEN")

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
        .order_by(Attendance.checked_in_at)
        .all()
    )

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        ["Full Name", "Email", "Student ID", "Department", "Check-in Time", "Check-in Method"]
    )

    # Write data rows
    for attendance in attendances:
        user = attendance.user
        department = db.session.get(Department, user.department_id) if user.department_id else None

        writer.writerow(
            [
                f"{user.first_name} {user.last_name}",
                user.email,
                user.username,  # Using username as student ID
                department.name if department else "N/A",
                attendance.checked_in_at.strftime("%Y-%m-%d %H:%M:%S")
                if attendance.checked_in_at
                else "N/A",
                attendance.check_in_method or "N/A",
            ]
        )

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    filename = (
        f'attendance_{event.title.replace(" ", "_")}_' f'{datetime.now().strftime("%Y%m%d")}.csv'
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"

    return response
