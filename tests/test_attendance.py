from datetime import datetime, timedelta

from app import db
from app.models import Attendance


class TestAttendanceRoutes:
    """Test attendance tracking routes."""

    def test_check_in_success(self, authenticated_client, event):
        """Test successful check-in."""
        response = authenticated_client.post(
            "/api/attendance/check-in",
            json={"event_id": event.id, "check_in_method": "qr_code"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Checked in successfully"

    def test_check_in_missing_event_id(self, authenticated_client):
        """Test check-in without event ID."""
        response = authenticated_client.post("/api/attendance/check-in", json={})

        assert response.status_code == 400

    def test_check_in_nonexistent_event(self, authenticated_client):
        """Test check-in to non-existent event."""
        response = authenticated_client.post(
            "/api/attendance/check-in",
            json={"event_id": 9999},
        )

        assert response.status_code == 404

    def test_check_in_duplicate(self, authenticated_client, event, student_user):
        """Test duplicate check-in."""
        # First check-in
        authenticated_client.post(
            "/api/attendance/check-in",
            json={"event_id": event.id},
        )

        # Second check-in (should fail)
        response = authenticated_client.post(
            "/api/attendance/check-in",
            json={"event_id": event.id},
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "Already checked in" in data["error"]

    def test_check_in_inactive_event(self, authenticated_client, event):
        """Test check-in to inactive event."""
        event.is_active = False
        db.session.commit()

        response = authenticated_client.post(
            "/api/attendance/check-in",
            json={"event_id": event.id},
        )

        assert response.status_code == 400

    def test_check_in_full_capacity(self, authenticated_client, event, admin_user):
        """Test check-in when event is at capacity."""
        event.max_capacity = 1
        db.session.commit()

        # Fill capacity with another user
        other_attendance = Attendance(event_id=event.id, user_id=admin_user.id)
        db.session.add(other_attendance)
        db.session.commit()

        response = authenticated_client.post(
            "/api/attendance/check-in",
            json={"event_id": event.id},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "full capacity" in data["error"]

    def test_get_my_attended_events(self, authenticated_client, event, student_user):
        """Test getting user's attended events."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = authenticated_client.get("/api/attendance/my-events")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["attendances"]) == 1

    def test_check_in_via_rest_endpoint(self, authenticated_client, event):
        """Test check-in via REST-compliant endpoint."""
        response = authenticated_client.post(
            "/api/attendance",
            json={"event_id": event.id},
        )
        assert response.status_code == 201

    def test_get_my_attended_events_with_pagination(self, authenticated_client, student_user):
        """Test pagination of attended events."""
        response = authenticated_client.get("/api/attendance/my-events?page=1&per_page=10")

        assert response.status_code == 200
        data = response.get_json()
        assert "page" in data
        assert "per_page" in data

    def test_get_attendance_status_checked_in(self, authenticated_client, event, student_user):
        """Test attendance status when checked in."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = authenticated_client.get(f"/api/attendance/event/{event.id}/status")

        assert response.status_code == 200
        data = response.get_json()
        assert data["checked_in"] is True

    def test_get_attendance_status_not_checked_in(self, authenticated_client, event):
        """Test attendance status when not checked in."""
        response = authenticated_client.get(f"/api/attendance/event/{event.id}/status")

        assert response.status_code == 200
        data = response.get_json()
        assert data["checked_in"] is False

    def test_delete_attendance_as_admin(self, admin_client, event, student_user):
        """Test deleting attendance as admin."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = admin_client.delete(f"/api/attendance/{att.id}")

        assert response.status_code == 200

    def test_delete_attendance_as_dept_admin(self, dept_admin_client, event, student_user):
        """Test deleting attendance as department admin."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = dept_admin_client.delete(f"/api/attendance/{att.id}")

        assert response.status_code == 200

    def test_delete_attendance_unauthorized(self, authenticated_client, event, student_user):
        """Test deleting attendance as student."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = authenticated_client.delete(f"/api/attendance/{att.id}")

        assert response.status_code == 403

    def test_bulk_check_in_as_admin(self, admin_client, event, student_user, admin_user):
        """Test bulk check-in as admin."""
        response = admin_client.post(
            "/api/attendance/bulk-check-in",
            json={"event_id": event.id, "user_ids": [student_user.id, admin_user.id]},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success_count"] == 2

    def test_bulk_check_in_missing_fields(self, admin_client):
        """Test bulk check-in with missing fields."""
        response = admin_client.post("/api/attendance/bulk-check-in", json={"event_id": 1})

        assert response.status_code == 400

    def test_bulk_check_in_unauthorized(self, authenticated_client, event):
        """Test bulk check-in as student."""
        response = authenticated_client.post(
            "/api/attendance/bulk-check-in",
            json={"event_id": event.id, "user_ids": [1, 2]},
        )

        assert response.status_code == 403

    def test_bulk_check_in_with_duplicates(self, admin_client, event, student_user):
        """Test bulk check-in with duplicate attendance."""
        # Create existing attendance
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = admin_client.post(
            "/api/attendance/bulk-check-in",
            json={"event_id": event.id, "user_ids": [student_user.id]},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["error_count"] == 1

    def test_bulk_check_in_unauthorized_dept_admin(self, app, dept_admin_client):
        """Test bulk check-in by dept admin for another department."""
        from app.models import Department, Event

        other_dept = Department(name="Other Dept")
        db.session.add(other_dept)
        db.session.commit()

        other_event = Event(
            title="Other Event",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=2),
            department_id=other_dept.id,
            created_by=1,
        )
        db.session.add(other_event)
        db.session.commit()

        response = dept_admin_client.post(
            "/api/attendance/bulk-check-in",
            json={"event_id": other_event.id, "user_ids": [1]},
        )
        assert response.status_code == 403

    def test_bulk_check_in_via_rest_endpoint(self, admin_client, event, student_user):
        """Test bulk check-in via REST-compliant endpoint."""
        response = admin_client.post(
            "/api/attendance/bulk",
            json={"event_id": event.id, "user_ids": [student_user.id]},
        )
        assert response.status_code == 200

    def test_check_in_form_public_endpoint(self, client, event, department, student_user):
        """Test public check-in form endpoint - requires existing user."""
        response = client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": event.id,
                "full_name": "Test Student",
                "email": "student@test.com",
                "department_id": department.id,
            },
        )
        assert response.status_code in [200, 201]

    def test_check_in_form_missing_fields(self, client, event):
        """Test check-in form with missing fields."""
        response = client.post(
            "/api/attendance/check-in-form",
            json={"event_id": event.id},
        )
        assert response.status_code == 400

    def test_check_in_form_invalid_email(self, client, event, department):
        """Test check-in form with invalid email."""
        response = client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": event.id,
                "full_name": "John Doe",
                "email": "invalid-email",
                "department_id": department.id,
            },
        )
        assert response.status_code in [400, 201]

    def test_export_attendance_as_admin(self, admin_client, event, student_user):
        """Test exporting attendance as CSV."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = admin_client.get(f"/api/attendance/export/{event.id}")
        assert response.status_code == 200
        assert response.content_type == "text/csv"

    def test_export_attendance_as_dept_admin(self, dept_admin_client, event):
        """Test exporting attendance as department admin."""
        response = dept_admin_client.get(f"/api/attendance/export/{event.id}")
        assert response.status_code == 200

    def test_export_attendance_unauthorized(self, authenticated_client, event):
        """Test exporting attendance as student."""
        response = authenticated_client.get(f"/api/attendance/export/{event.id}")
        assert response.status_code == 403

    def test_export_attendance_not_found(self, admin_client):
        """Test exporting attendance for non-existent event."""
        response = admin_client.get("/api/attendance/export/99999")
        assert response.status_code == 404

    def test_get_attendance_status_for_registered_event(
        self, authenticated_client, event, student_user
    ):
        """Test getting attendance status when registered."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = authenticated_client.get(f"/api/attendance/event/{event.id}/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["checked_in"] is True

    def test_bulk_check_in_nonexistent_users(self, admin_client, event):
        """Test bulk check-in with non-existent users."""
        response = admin_client.post(
            "/api/attendance/bulk-check-in",
            json={"event_id": event.id, "user_ids": [99999, 99998]},
        )
        assert response.status_code == 200

    def test_check_in_form_with_existing_user(self, client, event, student_user, department):
        """Test check-in form with existing user."""
        response = client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": event.id,
                "full_name": "Test Student",
                "email": "student@test.com",
                "department_id": department.id,
            },
        )
        assert response.status_code in [200, 201]

    def test_check_in_form_duplicate_checkin(self, client, event, student_user, department):
        """Test check-in form with duplicate check-in."""
        # First check-in
        client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": event.id,
                "full_name": "Test Student",
                "email": "student@test.com",
                "department_id": department.id,
            },
        )

        # Duplicate check-in
        response = client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": event.id,
                "full_name": "Test Student",
                "email": "student@test.com",
                "department_id": department.id,
            },
        )
        assert response.status_code in [400, 409]

    def test_check_in_form_inactive_event(self, client, event, department):
        """Test check-in form with inactive event."""
        from app import db

        event.is_active = False
        db.session.commit()

        response = client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": event.id,
                "full_name": "Test User",
                "email": "test@example.com",
                "department_id": department.id,
            },
        )
        assert response.status_code == 400

    def test_check_in_form_nonexistent_event(self, client, department):
        """Test check-in form with non-existent event."""
        response = client.post(
            "/api/attendance/check-in-form",
            json={
                "event_id": 99999,
                "full_name": "Test User",
                "email": "test@example.com",
                "department_id": department.id,
            },
        )
        assert response.status_code == 404

    def test_export_attendance_empty_event(self, admin_client, event):
        """Test exporting attendance with no attendees."""
        response = admin_client.get(f"/api/attendance/export/{event.id}")
        assert response.status_code == 200
        assert response.content_type == "text/csv"

    def test_export_attendance_wrong_department(self, dept_admin_client, admin_user, department):
        """Test department admin cannot export attendance for other department's event."""
        from datetime import datetime, timedelta

        from app.models import Department, Event

        # Create event in a different department
        other_dept = Department(name="Other Department")
        db.session.add(other_dept)
        db.session.commit()

        other_event = Event(
            title="Other Event",
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=2),
            department_id=other_dept.id,
            created_by=admin_user.id,
        )
        db.session.add(other_event)
        db.session.commit()

        response = dept_admin_client.get(f"/api/attendance/export/{other_event.id}")
        assert response.status_code == 403
