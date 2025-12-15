import pytest

from app.models import User


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, app, department):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role="student",
            department_id=department.id,
        )
        user.set_password("password123")

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.check_password("password123")

    def test_password_hashing(self, app):
        """Test password is hashed."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        user.set_password("password123")

        assert user.password_hash != "password123"
        assert user.check_password("password123")
        assert not user.check_password("wrongpassword")

    def test_user_to_dict(self, student_user):
        """Test user to_dict method."""
        user_dict = student_user.to_dict()

        assert user_dict["email"] == "student@test.com"
        assert user_dict["username"] == "student"
        assert user_dict["role"] == "student"
        assert "password_hash" not in user_dict

    def test_user_repr(self, student_user):
        """Test user __repr__ method."""
        assert repr(student_user) == "<User student>"


class TestDepartmentModel:
    """Test Department model."""

    def test_department_creation(self, app):
        """Test creating a department."""
        from app import db
        from app.models import Department

        dept = Department(name="Test Dept", description="Test Description")
        db.session.add(dept)
        db.session.commit()

        assert dept.name == "Test Dept"
        assert dept.description == "Test Description"

    def test_department_to_dict(self, department):
        """Test department to_dict method."""
        dept_dict = department.to_dict()

        assert dept_dict["name"] == "Computer Science"
        assert "user_count" in dept_dict
        assert "event_count" in dept_dict

    def test_department_repr(self, department):
        """Test department __repr__ method."""
        assert repr(department) == "<Department Computer Science>"


class TestEventModel:
    """Test Event model."""

    def test_event_creation(self, event):
        """Test creating an event."""
        assert event.title == "Test Event"
        assert event.is_active is True
        assert event.max_capacity == 50

    def test_event_to_dict(self, event):
        """Test event to_dict method."""
        event_dict = event.to_dict()

        assert event_dict["title"] == "Test Event"
        assert event_dict["location"] == "Test Location"
        assert "attendance_count" in event_dict

    def test_event_to_dict_with_attendees(self, event, student_user):
        """Test event to_dict with attendees."""
        from app import db
        from app.models import Attendance

        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        event_dict = event.to_dict(include_attendees=True)

        assert "attendees" in event_dict
        assert len(event_dict["attendees"]) == 1

    def test_event_repr(self, event):
        """Test event __repr__ method."""
        assert repr(event) == "<Event Test Event>"


class TestAttendanceModel:
    """Test Attendance model."""

    def test_attendance_creation(self, app, event, student_user):
        """Test creating attendance."""
        from app import db
        from app.models import Attendance

        att = Attendance(event_id=event.id, user_id=student_user.id, check_in_method="qr_code")
        db.session.add(att)
        db.session.commit()

        assert att.event_id == event.id
        assert att.user_id == student_user.id
        assert att.check_in_method == "qr_code"

    def test_attendance_to_dict(self, app, event, student_user):
        """Test attendance to_dict method."""
        from app import db
        from app.models import Attendance

        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        att_dict = att.to_dict()

        assert att_dict["event_id"] == event.id
        assert att_dict["user_id"] == student_user.id
        assert "checked_in_at" in att_dict

    def test_attendance_unique_constraint(self, app, event, student_user):
        """Test attendance unique constraint."""
        from sqlalchemy.exc import IntegrityError

        from app import db
        from app.models import Attendance

        att1 = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att1)
        db.session.commit()

        att2 = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att2)

        with pytest.raises(IntegrityError):
            db.session.commit()

    def test_attendance_repr(self, app, event, student_user):
        """Test attendance __repr__ method."""
        from app import db
        from app.models import Attendance

        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        assert repr(att) == f"<Attendance Event:{event.id} User:{student_user.id}>"


class TestNotificationModel:
    """Test Notification model."""

    def test_notification_creation(self, app, student_user, event):
        """Test creating a notification."""
        from app import db
        from app.models import Notification

        notif = Notification(
            user_id=student_user.id,
            event_id=event.id,
            title="Test Notification",
            message="Test Message",
            notification_type="event_alert",
        )
        db.session.add(notif)
        db.session.commit()

        assert notif.title == "Test Notification"
        assert notif.is_read is False

    def test_notification_to_dict(self, app, student_user):
        """Test notification to_dict method."""
        from app import db
        from app.models import Notification

        notif = Notification(user_id=student_user.id, title="Test", message="Test Message")
        db.session.add(notif)
        db.session.commit()

        notif_dict = notif.to_dict()

        assert notif_dict["title"] == "Test"
        assert notif_dict["is_read"] is False

    def test_notification_repr(self, app, student_user):
        """Test notification __repr__ method."""
        from app import db
        from app.models import Notification

        notif = Notification(user_id=student_user.id, title="Test", message="Test Message")
        db.session.add(notif)
        db.session.commit()

        assert repr(notif) == "<Notification Test>"
