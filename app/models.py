from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(
        db.String(20), nullable=False, default="student"
    )  # student, admin, department_admin
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    department = db.relationship("Department", back_populates="users")
    attended_events = db.relationship("Attendance", back_populates="user", lazy="dynamic")
    notifications = db.relationship(
        "Notification", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user to dictionary for API responses."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "department_id": self.department_id,
            "department": self.department.name if self.department else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Department(db.Model):
    """Department model for organizing users and events."""

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", back_populates="department", lazy="dynamic")
    events = db.relationship(
        "Event", back_populates="department", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert department to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "contact_email": self.contact_email,
            "created_at": self.created_at.isoformat(),
            "user_count": self.users.count(),
            "event_count": self.events.count(),
        }

    def __repr__(self):
        return f"<Department {self.name}>"


class Event(db.Model):
    """Event model for managing campus events."""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=True)
    flier_path = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = db.relationship("Department", back_populates="events")
    creator = db.relationship("User", foreign_keys=[created_by])
    attendees = db.relationship("Attendance", back_populates="event", lazy="dynamic")

    def to_dict(self, include_attendees=False):
        """Convert event to dictionary for API responses."""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "date": self.start_time.date().isoformat(),
            "start_time": self.start_time.time().isoformat(),
            "end_time": self.end_time.time().isoformat(),
            "max_capacity": self.max_capacity,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "created_by": self.created_by,
            "creator_name": f"{self.creator.first_name} {self.creator.last_name}",
            "qr_code_path": self.qr_code_path,
            "flier_path": self.flier_path,
            "is_active": self.is_active,
            "registered_count": self.attendees.count(),
            "attendance_count": self.attendees.count(),
            "registration_required": True,
            "points": 0,
            "tags": None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_attendees:
            data["attendees"] = [att.to_dict() for att in self.attendees.all()]

        return data

    def __repr__(self):
        return f"<Event {self.title}>"


class Attendance(db.Model):
    """Attendance model for tracking event participation."""

    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    checked_in_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    check_in_method = db.Column(db.String(20), default="qr_code")  # qr_code, manual, self_check_in

    # Relationships
    event = db.relationship("Event", back_populates="attendees")
    user = db.relationship("User", back_populates="attended_events")

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint("event_id", "user_id", name="unique_attendance"),)

    def to_dict(self):
        """Convert attendance to dictionary for API responses."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_title": self.event.title if self.event else None,
            "user_id": self.user_id,
            "user_name": f"{self.user.first_name} {self.user.last_name}" if self.user else None,
            "user_email": self.user.email if self.user else None,
            "checked_in_at": self.checked_in_at.isoformat(),
            "check_in_method": self.check_in_method,
        }

    def __repr__(self):
        return f"<Attendance Event:{self.event_id} User:{self.user_id}>"


class Notification(db.Model):
    """Notification model for targeted event alerts."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(
        db.String(20), default="event_alert"
    )  # event_alert, reminder, update
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="notifications")
    event = db.relationship("Event")

    def to_dict(self):
        """Convert notification to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "sent_at": self.sent_at.isoformat(),
        }

    def __repr__(self):
        return f"<Notification {self.title}>"
