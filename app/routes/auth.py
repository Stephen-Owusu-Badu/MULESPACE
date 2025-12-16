from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import Department, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()

    # Validation
    required_fields = ["email", "password", "name"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Check if user already exists
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    # Split name into first and last
    name_parts = data["name"].strip().split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Generate username from email
    username = data["email"].split("@")[0]

    # Make username unique if it already exists
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # Create new user
    user = User(
        email=data["email"],
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=data.get("role", "student"),
        department_id=data.get("department_id"),
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and create session."""
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    login_user(user, remember=data.get("remember", False))

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout current user."""
    logout_user()
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current authenticated user info."""
    return jsonify({"user": current_user.to_dict()}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@auth_bp.route("/password", methods=["PUT"])  # REST-compliant alias
@login_required
def change_password():
    """Change user password."""
    data = request.get_json()

    if not data.get("old_password") or not data.get("new_password"):
        return jsonify({"error": "Old and new passwords required"}), 400

    if not current_user.check_password(data["old_password"]):
        return jsonify({"error": "Incorrect old password"}), 401

    current_user.set_password(data["new_password"])
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200


@auth_bp.route("/departments", methods=["GET"])
def get_departments():
    """Get all departments for registration."""
    departments = Department.query.all()
    return jsonify({"departments": [dept.to_dict() for dept in departments]}), 200
