from datetime import datetime, timedelta

from app import db


class TestAdditionalCoverage:
    """Additional tests to reach 100% coverage."""

    def test_get_event_not_found(self, client):
        """Test getting non-existent event returns proper error."""
        response = client.get("/api/events/99999")
        assert response.status_code == 404
        data = response.get_json()
        assert "not found" in data["error"].lower()

    def test_update_event_not_found(self, admin_client):
        """Test updating non-existent event."""
        response = admin_client.put("/api/events/99999", json={"title": "Test"})
        assert response.status_code == 404

    def test_delete_event_not_found(self, admin_client):
        """Test deleting non-existent event."""
        response = admin_client.delete("/api/events/99999")
        assert response.status_code == 404

    def test_get_event_attendees_not_found(self, admin_client):
        """Test getting attendees for non-existent event."""
        response = admin_client.get("/api/events/99999/attendees")
        assert response.status_code == 404

    def test_check_in_event_not_found(self, authenticated_client):
        """Test check-in to non-existent event."""
        response = authenticated_client.post("/api/attendance/check-in", json={"event_id": 99999})
        assert response.status_code == 404

    def test_get_attendance_status_not_found(self, authenticated_client):
        """Test attendance status for non-existent event."""
        response = authenticated_client.get("/api/attendance/event/99999/status")
        assert response.status_code == 404

    def test_delete_attendance_not_found(self, admin_client):
        """Test deleting non-existent attendance."""
        response = admin_client.delete("/api/attendance/99999")
        assert response.status_code == 404

    def test_bulk_check_in_event_not_found(self, admin_client):
        """Test bulk check-in for non-existent event."""
        response = admin_client.post(
            "/api/attendance/bulk-check-in", json={"event_id": 99999, "user_ids": [1]}
        )
        assert response.status_code == 404

    def test_update_user_not_found(self, admin_client):
        """Test updating non-existent user."""
        response = admin_client.put("/api/admin/users/99999", json={"role": "admin"})
        assert response.status_code == 404

    def test_update_department_not_found(self, admin_client):
        """Test updating non-existent department."""
        response = admin_client.put("/api/admin/departments/99999", json={"name": "Test"})
        assert response.status_code == 404

    def test_delete_department_not_found(self, admin_client):
        """Test deleting non-existent department."""
        response = admin_client.delete("/api/admin/departments/99999")
        assert response.status_code == 404

    def test_event_update_time_boundary(self, admin_client, event):
        """Test event update with same start and end time."""
        same_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        response = admin_client.put(
            f"/api/events/{event.id}",
            json={"start_time": same_time, "end_time": same_time},
        )
        assert response.status_code == 400

    def test_calendar_get_department_color_edge_case(self, client, app):
        """Test department color function with large department ID."""
        from app.routes.calendar import get_department_color

        with app.app_context():
            # Test wrapping behavior
            color1 = get_department_color(1)
            color9 = get_department_color(9)
            assert color1 == color9  # Should wrap around

            # Test None department
            color_none = get_department_color(None)
            assert color_none is not None

    def test_update_user_all_fields(self, admin_client, student_user, department):
        """Test updating all user fields."""
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}",
            json={
                "role": "department_admin",
                "is_active": False,
                "department_id": department.id,
            },
        )
        assert response.status_code == 200

    def test_update_department_all_fields(self, admin_client, department):
        """Test updating all department fields."""
        response = admin_client.put(
            f"/api/admin/departments/{department.id}",
            json={
                "name": "Updated CS",
                "description": "Updated Description",
                "contact_email": "updated@test.com",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["department"]["name"] == "Updated CS"

    def test_check_in_with_no_capacity_limit(self, authenticated_client, admin_user, department):
        """Test check-in when event has no capacity limit."""
        from app.models import Event

        event_no_limit = Event(
            title="No Limit Event",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=2),
            max_capacity=None,  # No limit
            department_id=department.id,
            created_by=admin_user.id,
        )
        db.session.add(event_no_limit)
        db.session.commit()

        response = authenticated_client.post(
            "/api/attendance/check-in", json={"event_id": event_no_limit.id}
        )
        assert response.status_code == 201

    def test_update_event_invalid_end_time_format(self, admin_client, event):
        """Test updating event with invalid end_time format."""
        response = admin_client.put(f"/api/events/{event.id}", json={"end_time": "not-a-date"})
        assert response.status_code == 400

    def test_load_user_from_login_manager(self, app, student_user):
        """Test Flask-Login's user loader."""
        from app.models import load_user

        with app.app_context():
            loaded = load_user(student_user.id)
            assert loaded.id == student_user.id

            # Test with invalid ID
            invalid = load_user(99999)
            assert invalid is None

    def test_utils_validate_email_regex(self):
        """Test email validation regex function."""
        from app.utils import validate_email

        # Additional edge cases
        assert validate_email("test.name@example.com")
        assert validate_email("test+tag@example.com")
        assert not validate_email("test@")
        assert not validate_email("@test.com")

    def test_update_event_invalid_start_time_format(self, admin_client, event):
        """Test updating event with invalid start_time format."""
        response = admin_client.put(
            f"/api/events/{event.id}", json={"start_time": "invalid-date-format"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid start_time format" in data["error"]

    def test_delete_attendance_unauthorized_dept_admin(self, app, dept_admin_client, student_user):
        """Test dept admin cannot delete attendance from another department."""
        from app.models import Attendance, Department, Event

        # Create another department
        other_dept = Department(name="Other Department")
        db.session.add(other_dept)
        db.session.commit()

        # Create event in other department
        other_event = Event(
            title="Other Dept Event",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=2),
            department_id=other_dept.id,
            created_by=student_user.id,
        )
        db.session.add(other_event)
        db.session.commit()

        # Create attendance in other department's event
        other_att = Attendance(event_id=other_event.id, user_id=student_user.id)
        db.session.add(other_att)
        db.session.commit()

        # Try to delete as dept admin from different department
        response = dept_admin_client.delete(f"/api/attendance/{other_att.id}")
        assert response.status_code == 403

    def test_require_role_unauthenticated(self, client):
        """Test require_role decorator with unauthenticated user."""
        # Try to access admin endpoint without authentication
        response = client.get("/api/admin/dashboard")
        # Will redirect to login (302) instead of 401
        assert response.status_code in [302, 401]

    def test_update_user_partial_fields(self, admin_client, student_user):
        """Test updating only some user fields."""
        # Update only role
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}",
            json={"role": "admin"},
        )
        assert response.status_code == 200

        # Update only is_active
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}",
            json={"is_active": True},
        )
        assert response.status_code == 200

        # Update only department_id
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}",
            json={"department_id": None},
        )
        assert response.status_code == 200

    def test_update_department_partial_fields(self, admin_client, department):
        """Test updating only some department fields."""
        # Update only name
        response = admin_client.put(
            f"/api/admin/departments/{department.id}",
            json={"name": "New Name Only"},
        )
        assert response.status_code == 200

        # Update only description
        response = admin_client.put(
            f"/api/admin/departments/{department.id}",
            json={"description": "New Description Only"},
        )
        assert response.status_code == 200

        # Update only contact_email
        response = admin_client.put(
            f"/api/admin/departments/{department.id}",
            json={"contact_email": "new@email.com"},
        )
        assert response.status_code == 200

    def test_update_event_only_max_capacity(self, admin_client, event):
        """Test updating only max_capacity field."""
        response = admin_client.put(
            f"/api/events/{event.id}",
            json={"max_capacity": 100},
        )
        assert response.status_code == 200

    def test_update_event_only_location(self, admin_client, event):
        """Test updating only location field."""
        response = admin_client.put(
            f"/api/events/{event.id}",
            json={"location": "New Location"},
        )
        assert response.status_code == 200

    def test_utils_generate_qr_code_creates_dir(self, app):
        """Test QR code generation creates directory if needed."""
        import os
        import shutil

        from app.utils import generate_qr_code

        with app.app_context():
            # Remove qrcodes directory if exists
            qr_dir = os.path.join("app", "static", "qrcodes")
            if os.path.exists(qr_dir):
                shutil.rmtree(qr_dir)

            # Generate QR code (should create directory)
            result = generate_qr_code(999)
            assert result is not None
            assert os.path.exists(qr_dir)

    def test_delete_event_success_message(self, admin_client, event):
        """Test delete event returns correct success message."""
        response = admin_client.delete(f"/api/events/{event.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Event deleted successfully"

    def test_validate_email_comprehensive(self):
        """Test comprehensive email validation cases."""
        from app.utils import validate_email

        # Valid emails
        assert validate_email("simple@example.com")
        assert validate_email("very.common@example.com")
        assert validate_email("disposable.style.email.with+symbol@example.com")
        assert validate_email("user-name@example-domain.com")

        # Invalid emails (should return falsy)
        assert not validate_email("plainaddress")
        assert not validate_email("missing-domain@.com")
        assert not validate_email("@no-local.org")

    def test_require_role_without_login_required(self, app, client):
        """Test require_role decorator without login_required (edge case)."""
        from flask import Blueprint, jsonify

        from app.utils import require_role

        # Create a test blueprint with require_role but no login_required
        test_bp = Blueprint("test", __name__)

        @test_bp.route("/test-role-only")
        @require_role(["admin"])
        def test_endpoint():
            return jsonify({"message": "success"}), 200

        app.register_blueprint(test_bp)

        # Test unauthenticated access - should hit line 38 in utils.py
        with app.test_client() as test_client:
            response = test_client.get("/test-role-only")
            assert response.status_code == 401
            data = response.get_json()
            assert "Authentication required" in data["error"]

    def test_delete_event_success_response_body(self, admin_client, event):
        """Test event deletion returns success message in JSON response."""
        response = admin_client.delete(f"/api/events/{event.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "deleted successfully" in data["message"]

    def test_delete_event_success_as_dept_admin(self, dept_admin_client, event):
        """Test dept admin deleting event returns success message."""
        response = dept_admin_client.delete(f"/api/events/{event.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Event deleted successfully"

    def test_dept_admin_cannot_delete_other_department_event(
        self, dept_admin_client, dept_admin_user
    ):
        """Test department admin cannot delete event from another department."""
        from app import db
        from app.models import Department, Event

        # Create another department
        other_dept = Department(name="Other Department")
        db.session.add(other_dept)
        db.session.commit()

        # Create event in other department (different from dept_admin's department)
        other_event = Event(
            title="Other Dept Event",
            description="Test event",
            start_time=datetime(2025, 12, 20, 10, 0),
            end_time=datetime(2025, 12, 20, 11, 0),
            location="Room B",
            department_id=other_dept.id,
            created_by=dept_admin_user.id,
        )
        db.session.add(other_event)
        db.session.commit()

        # Try to delete with dept_admin from different department
        response = dept_admin_client.delete(f"/api/events/{other_event.id}")
        assert response.status_code == 403
        data = response.get_json()
        assert "Unauthorized" in data["error"]
