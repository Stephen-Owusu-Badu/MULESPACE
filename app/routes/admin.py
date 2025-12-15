from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import Attendance, Department, Event, User
from app.utils import require_role

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard", methods=["GET"])
@login_required
@require_role(["admin", "department_admin"])
def get_dashboard_stats():
    """Get dashboard statistics."""
    stats = {}

    if current_user.role == "admin":
        # Global stats for admin
        stats["total_users"] = User.query.count()
        stats["total_departments"] = Department.query.count()
        stats["total_events"] = Event.query.filter_by(is_active=True).count()
        stats["total_attendance"] = Attendance.query.count()
    else:
        # Department-specific stats
        stats["department_users"] = User.query.filter_by(
            department_id=current_user.department_id
        ).count()
        stats["department_events"] = Event.query.filter_by(
            department_id=current_user.department_id, is_active=True
        ).count()
        stats["department_attendance"] = (
            Attendance.query.join(Event)
            .filter(Event.department_id == current_user.department_id)
            .count()
        )

    return jsonify({"stats": stats}), 200


@admin_bp.route("/users", methods=["GET"])
@login_required
@require_role(["admin"])
def get_all_users():
    """Get all users (admin only)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "users": [user.to_dict() for user in pagination.items],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
@require_role(["admin"])
def update_user(user_id):
    """Update user details (admin only)."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json()

    # Update allowed fields
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "department_id" in data:
        user.department_id = data["department_id"]

    db.session.commit()

    return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200


@admin_bp.route("/departments", methods=["POST"])
@login_required
@require_role(["admin"])
def create_department():
    """Create a new department (admin only)."""
    data = request.get_json()

    if not data.get("name"):
        return jsonify({"error": "Department name required"}), 400

    # Check if exists
    existing = Department.query.filter_by(name=data["name"]).first()
    if existing:
        return jsonify({"error": "Department already exists"}), 409

    department = Department(
        name=data["name"],
        description=data.get("description"),
        contact_email=data.get("contact_email"),
    )

    db.session.add(department)
    db.session.commit()

    return (
        jsonify({"message": "Department created successfully", "department": department.to_dict()}),
        201,
    )


@admin_bp.route("/departments/<int:dept_id>", methods=["PUT"])
@login_required
@require_role(["admin"])
def update_department(dept_id):
    """Update department details (admin only)."""
    department = db.session.get(Department, dept_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404
    data = request.get_json()

    if "name" in data:
        department.name = data["name"]
    if "description" in data:
        department.description = data["description"]
    if "contact_email" in data:
        department.contact_email = data["contact_email"]

    db.session.commit()

    return (
        jsonify({"message": "Department updated successfully", "department": department.to_dict()}),
        200,
    )


@admin_bp.route("/departments/<int:dept_id>", methods=["DELETE"])
@login_required
@require_role(["admin"])
def delete_department(dept_id):
    """Delete a department (admin only)."""
    department = db.session.get(Department, dept_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404

    # Check if department has users or events
    if department.users.count() > 0:
        return jsonify({"error": "Cannot delete department with users"}), 400
    if department.events.count() > 0:
        return jsonify({"error": "Cannot delete department with events"}), 400

    db.session.delete(department)
    db.session.commit()

    return jsonify({"message": "Department deleted successfully"}), 200


@admin_bp.route("/analytics/events", methods=["GET"])
@login_required
@require_role(["admin", "department_admin"])
def get_event_analytics():
    """Get event analytics."""
    department_id = request.args.get("department_id", type=int)

    query = db.session.query(
        Event.id,
        Event.title,
        Event.start_time,
        func.count(Attendance.id).label("attendance_count"),
    ).outerjoin(Attendance, Event.id == Attendance.event_id)

    if current_user.role == "department_admin":
        query = query.filter(Event.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Event.department_id == department_id)

    query = query.filter(Event.is_active == True).group_by(Event.id)  # noqa: E712

    results = query.all()

    analytics = []
    for event_id, title, start_time, attendance_count in results:
        analytics.append(
            {
                "event_id": event_id,
                "title": title,
                "start_time": start_time.isoformat(),
                "attendance_count": attendance_count,
            }
        )

    return jsonify({"analytics": analytics}), 200


@admin_bp.route("/analytics/departments", methods=["GET"])
@login_required
@require_role(["admin"])
def get_department_analytics():
    """Get department analytics (admin only)."""
    analytics = (
        db.session.query(
            Department.id,
            Department.name,
            func.count(Event.id).label("event_count"),
            func.count(Attendance.id).label("total_attendance"),
        )
        .outerjoin(Event, Department.id == Event.department_id)
        .outerjoin(Attendance, Event.id == Attendance.event_id)
        .group_by(Department.id)
        .all()
    )

    results = []
    for dept_id, dept_name, event_count, total_attendance in analytics:
        results.append(
            {
                "department_id": dept_id,
                "department_name": dept_name,
                "event_count": event_count,
                "total_attendance": total_attendance,
            }
        )

    return jsonify({"analytics": results}), 200
