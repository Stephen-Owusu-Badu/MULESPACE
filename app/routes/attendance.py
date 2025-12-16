from flask import Blueprint, jsonify, request, render_template, make_response
from flask_login import current_user, login_required
from datetime import datetime
import csv
import io

from app import db
from app.models import Attendance, Event, User, Department

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/check-in", methods=["POST"])
@attendance_bp.route("", methods=["POST"])  # REST-compliant alias
@login_required
def check_in():
    """Check in a user to an event."""
    data = request.get_json()

    if not data.get("event_id"):
        return jsonify({"error": "Event ID required"}), 400

    event = db.session.get(Event, data["event_id"])
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check if event is active
    if not event.is_active:
        return jsonify({"error": "Event is not active"}), 400

    # Check if attendance record exists
    existing = Attendance.query.filter_by(event_id=event.id, user_id=current_user.id).first()
    
    if existing:
        return jsonify({"error": "Already checked in to this event"}), 409

    # Check capacity
    if event.max_capacity:
        current_count = Attendance.query.filter_by(event_id=event.id).count()
        if current_count >= event.max_capacity:
            return jsonify({"error": "Event is at full capacity"}), 400

    # Create attendance record with check-in
    attendance = Attendance(
        event_id=event.id,
        user_id=current_user.id,
        check_in_method=data.get("check_in_method", "qr_code")
    )

    db.session.add(attendance)
    db.session.commit()

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

    return (
        jsonify(
            {
                "attendances": [att.to_dict() for att in pagination.items],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@attendance_bp.route("/event/<int:event_id>/status", methods=["GET"])
@login_required
def get_attendance_status(event_id):
    """Check if current user is checked in to an event."""
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

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
        return jsonify({"error": "Unauthorized"}), 403

    attendance = db.session.get(Attendance, attendance_id)
    if not attendance:
        return jsonify({"error": "Attendance not found"}), 404

    # Department admins can only delete from their department's events
    if current_user.role == "department_admin":
        if attendance.event.department_id != current_user.department_id:
            return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(attendance)
    db.session.commit()

    return jsonify({"message": "Attendance record deleted"}), 200


@attendance_bp.route("/bulk-check-in", methods=["POST"])
@attendance_bp.route("/bulk", methods=["POST"])  # REST-compliant alias
@login_required
def bulk_check_in():
    """Check in multiple users to an event (admin only)."""
    if current_user.role not in ["admin", "department_admin"]:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    if not data.get("event_id") or not data.get("user_ids"):
        return jsonify({"error": "Event ID and user IDs required"}), 400

    event = db.session.get(Event, data["event_id"])
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check permission
    if (
        current_user.role == "department_admin"
        and event.department_id != current_user.department_id
    ):
        return jsonify({"error": "Unauthorized"}), 403

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
    data = request.get_json()

    required_fields = ['event_id', 'full_name', 'email', 'department_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field.replace('_', ' ').title()} is required"}), 400

    event = db.session.get(Event, data['event_id'])
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check if event is active
    if not event.is_active:
        return jsonify({"error": "Event is not active"}), 400

    # Check if already checked in with this email
    # For form submissions, we store data differently
    # We'll create an attendance record and store form data in a separate table
    # For now, we'll use the existing Attendance model
    
    # Try to find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if user:
        # Existing user - check if already checked in
        existing = Attendance.query.filter_by(event_id=event.id, user_id=user.id).first()
        if existing:
            return jsonify({"error": "You have already checked in to this event"}), 409
        
        # Create attendance record
        attendance = Attendance(
            event_id=event.id,
            user_id=user.id,
            check_in_method='qr_form'
        )
    else:
        # Guest check-in (no user account) - we'll still record it
        # For now, we'll skip this and require users to have accounts
        return jsonify({"error": "Please register for an account first"}), 400

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        "message": "Check-in successful",
        "attendance": attendance.to_dict()
    }), 201


@attendance_bp.route("/export/<int:event_id>", methods=["GET"])
@login_required
def export_attendance(event_id):
    """Export attendance data for an event as CSV (admin only)."""
    if current_user.role not in ["admin", "department_admin"]:
        return jsonify({"error": "Unauthorized"}), 403

    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check permission
    if current_user.role == "department_admin" and event.department_id != current_user.department_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Get all attendance records for this event
    attendances = Attendance.query.filter_by(event_id=event_id).join(User).order_by(Attendance.checked_in_at).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Full Name',
        'Email',
        'Student ID',
        'Department',
        'Check-in Time',
        'Check-in Method'
    ])

    # Write data rows
    for attendance in attendances:
        user = attendance.user
        department = Department.query.get(user.department_id) if user.department_id else None
        
        writer.writerow([
            f"{user.first_name} {user.last_name}",
            user.email,
            user.username,  # Using username as student ID
            department.name if department else 'N/A',
            attendance.checked_in_at.strftime('%Y-%m-%d %H:%M:%S') if attendance.checked_in_at else 'N/A',
            attendance.check_in_method or 'N/A'
        ])

    # Prepare response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=attendance_{event.title.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response
