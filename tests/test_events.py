from datetime import datetime, timedelta

from app import db
from app.models import Attendance, Event


class TestEventRoutes:
    """Test event management routes."""

    def test_get_all_events(self, client, event):
        """Test getting all events."""
        response = client.get("/api/events")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) >= 1
        assert data["events"][0]["title"] == "Test Event"

    def test_get_events_with_pagination(self, client, event):
        """Test events with pagination."""
        response = client.get("/api/events?page=1&per_page=10")

        assert response.status_code == 200
        data = response.get_json()
        assert "page" in data
        assert "per_page" in data
        assert "total" in data

    def test_get_events_filtered_by_department(self, client, event, department):
        """Test filtering events by department."""
        response = client.get(f"/api/events?department_id={department.id}")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) >= 1

    def test_get_events_filtered_by_date(self, client, event):
        """Test filtering events by date range."""
        start = datetime.utcnow().isoformat()
        end = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = client.get(f"/api/events?start_date={start}&end_date={end}")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) >= 1

    def test_get_single_event(self, client, event):
        """Test getting a single event."""
        response = client.get(f"/api/events/{event.id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["event"]["title"] == "Test Event"

    def test_get_single_event_with_attendees(self, client, event, student_user):
        """Test getting event with attendees."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = client.get(f"/api/events/{event.id}?include_attendees=true")

        assert response.status_code == 200
        data = response.get_json()
        assert "attendees" in data["event"]

    def test_get_nonexistent_event(self, client):
        """Test getting non-existent event."""
        response = client.get("/api/events/9999")
        assert response.status_code == 404

    def test_create_event_as_admin(self, admin_client, department):
        """Test creating event as admin."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = admin_client.post(
            "/api/events",
            json={
                "title": "New Event",
                "description": "New Description",
                "location": "New Location",
                "start_time": start_time,
                "end_time": end_time,
                "max_capacity": 100,
                "department_id": department.id,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["event"]["title"] == "New Event"

    def test_create_event_as_dept_admin(self, dept_admin_client, department):
        """Test creating event as department admin."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = dept_admin_client.post(
            "/api/events",
            json={
                "title": "Dept Event",
                "start_time": start_time,
                "end_time": end_time,
                "department_id": department.id,
            },
        )

        assert response.status_code == 201

    def test_create_event_as_student(self, authenticated_client, department):
        """Test creating event as student (should fail)."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = authenticated_client.post(
            "/api/events",
            json={
                "title": "Student Event",
                "start_time": start_time,
                "end_time": end_time,
                "department_id": department.id,
            },
        )

        assert response.status_code == 403

    def test_create_event_missing_fields(self, admin_client):
        """Test creating event with missing fields."""
        response = admin_client.post("/api/events", json={"title": "Incomplete Event"})

        assert response.status_code == 400

    def test_create_event_invalid_dates(self, admin_client, department):
        """Test creating event with invalid dates."""
        response = admin_client.post(
            "/api/events",
            json={
                "title": "Invalid Event",
                "start_time": "invalid-date",
                "end_time": "invalid-date",
                "department_id": department.id,
            },
        )

        assert response.status_code == 400

    def test_create_event_start_after_end(self, admin_client, department):
        """Test creating event where start is after end."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=1)).isoformat()

        response = admin_client.post(
            "/api/events",
            json={
                "title": "Invalid Times",
                "start_time": start_time,
                "end_time": end_time,
                "department_id": department.id,
            },
        )

        assert response.status_code == 400

    def test_create_event_nonexistent_department(self, admin_client):
        """Test creating event with non-existent department."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = admin_client.post(
            "/api/events",
            json={
                "title": "Test",
                "start_time": start_time,
                "end_time": end_time,
                "department_id": 9999,
            },
        )

        assert response.status_code == 404

    def test_update_event_as_admin(self, admin_client, event):
        """Test updating event as admin."""
        response = admin_client.put(
            f"/api/events/{event.id}",
            json={"title": "Updated Title", "location": "Updated Location"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["event"]["title"] == "Updated Title"

    def test_update_event_as_dept_admin(self, dept_admin_client, event):
        """Test updating event as department admin."""
        response = dept_admin_client.put(
            f"/api/events/{event.id}",
            json={"description": "Updated Description"},
        )

        assert response.status_code == 200

    def test_update_event_unauthorized_dept_admin(self, app, dept_admin_client):
        """Test updating event from another department."""
        # Create another department and event
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

        response = dept_admin_client.put(
            f"/api/events/{other_event.id}",
            json={"title": "Unauthorized Update"},
        )

        assert response.status_code == 403

    def test_update_event_invalid_times(self, admin_client, event):
        """Test updating event with invalid times."""
        response = admin_client.put(
            f"/api/events/{event.id}",
            json={"start_time": "invalid-date"},
        )

        assert response.status_code == 400

    def test_delete_event_as_admin(self, admin_client, event):
        """Test deleting event as admin."""
        response = admin_client.delete(f"/api/events/{event.id}")

        assert response.status_code == 200

        # Verify event is deactivated
        deleted_event = db.session.get(Event, event.id)
        assert deleted_event.is_active is False

    def test_delete_event_as_dept_admin(self, dept_admin_client, event):
        """Test deleting event as department admin."""
        response = dept_admin_client.delete(f"/api/events/{event.id}")
        assert response.status_code == 200

    def test_delete_event_unauthorized(self, authenticated_client, event):
        """Test deleting event as student (should fail)."""
        response = authenticated_client.delete(f"/api/events/{event.id}")
        assert response.status_code == 403

    def test_get_event_attendees(self, admin_client, event, student_user):
        """Test getting event attendees."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = admin_client.get(f"/api/events/{event.id}/attendees")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["attendees"]) == 1

    def test_get_event_attendees_unauthorized(self, app, dept_admin_client):
        """Test getting attendees from another department's event."""
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

        response = dept_admin_client.get(f"/api/events/{other_event.id}/attendees")
        assert response.status_code == 403

    def test_register_for_event_success(self, authenticated_client, event):
        """Test successful event registration."""
        response = authenticated_client.post(f"/api/events/{event.id}/register", json={})
        assert response.status_code in [200, 201]

    def test_register_for_event_via_registrations_endpoint(self, authenticated_client, event):
        """Test registration via REST-compliant endpoint."""
        response = authenticated_client.post(f"/api/events/{event.id}/registrations", json={})
        assert response.status_code in [200, 201]

    def test_register_for_event_not_found(self, authenticated_client):
        """Test registering for non-existent event."""
        response = authenticated_client.post("/api/events/99999/register", json={})
        assert response.status_code == 404

    def test_register_for_event_duplicate(self, authenticated_client, event, student_user):
        """Test duplicate registration."""
        # First registration
        authenticated_client.post(f"/api/events/{event.id}/register", json={})

        # Duplicate registration
        response = authenticated_client.post(f"/api/events/{event.id}/register", json={})
        assert response.status_code in [200, 400, 409]

    def test_get_event_registrations_as_admin(self, admin_client, event, student_user):
        """Test getting event registrations as admin."""
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = admin_client.get(f"/api/events/{event.id}/registrations")
        assert response.status_code == 200
        data = response.get_json()
        assert "registrations" in data

    def test_get_event_registrations_not_found(self, admin_client):
        """Test getting registrations for non-existent event."""
        response = admin_client.get("/api/events/99999/registrations")
        assert response.status_code == 404

    def test_get_event_registrations_unauthorized(self, authenticated_client, event):
        """Test getting registrations as non-admin."""
        response = authenticated_client.get(f"/api/events/{event.id}/registrations")
        assert response.status_code == 403

    def test_get_event_qr_code_as_admin(self, admin_client, event):
        """Test generating QR code as admin."""
        response = admin_client.get(f"/api/events/{event.id}/qr-code")
        assert response.status_code == 200
        data = response.get_json()
        assert "qr_code" in data

    def test_get_event_qr_code_as_dept_admin(self, dept_admin_client, event):
        """Test generating QR code as department admin."""
        response = dept_admin_client.get(f"/api/events/{event.id}/qr-code")
        assert response.status_code == 200

    def test_get_event_qr_code_unauthorized(self, authenticated_client, event):
        """Test QR code generation as student."""
        response = authenticated_client.get(f"/api/events/{event.id}/qr-code")
        assert response.status_code == 403

    def test_get_event_qr_code_not_found(self, admin_client):
        """Test QR code for non-existent event."""
        response = admin_client.get("/api/events/99999/qr-code")
        assert response.status_code == 404

    def test_create_event_with_flier(self, admin_client, department):
        """Test creating event - flier needs file upload not JSON."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = admin_client.post(
            "/api/events",
            json={
                "title": "Event with Flier",
                "start_time": start_time,
                "end_time": end_time,
                "department_id": department.id,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["event"]["title"] == "Event with Flier"

    def test_update_event_capacity(self, admin_client, event):
        """Test updating event capacity."""
        response = admin_client.put(f"/api/events/{event.id}", json={"max_capacity": 200})
        assert response.status_code == 200
        data = response.get_json()
        assert data["event"]["max_capacity"] == 200

    def test_get_events_with_limit(self, client, event):
        """Test getting events with limit parameter."""
        response = client.get("/api/events?limit=5")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) <= 5

    def test_get_events_search_by_title(self, client, event):
        """Test searching events by title."""
        response = client.get(f"/api/events?search={event.title}")
        assert response.status_code == 200

    def test_update_event_start_time_only(self, admin_client, event):
        """Test updating only start time - must stay before end time."""
        # Event starts at +1 day, ends at +1 day +2 hours
        # Move start to +1 day +1 hour (still before end)
        new_start = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat()
        response = admin_client.put(f"/api/events/{event.id}", json={"start_time": new_start})
        assert response.status_code == 200

    def test_update_event_end_time_only(self, admin_client, event):
        """Test updating only end time - must stay after start time."""
        # Event starts at +1 day, ends at +1 day +2 hours
        # Move end to +1 day +3 hours (still after start)
        new_end = (datetime.utcnow() + timedelta(days=1, hours=3)).isoformat()
        response = admin_client.put(f"/api/events/{event.id}", json={"end_time": new_end})
        assert response.status_code == 200

    def test_create_event_with_all_fields(self, admin_client, department):
        """Test creating event with all optional fields."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = admin_client.post(
            "/api/events",
            json={
                "title": "Full Event",
                "description": "Full description",
                "location": "Test Location",
                "start_time": start_time,
                "end_time": end_time,
                "max_capacity": 50,
                "department_id": department.id,
                "flier_path": "/uploads/flier.png",
            },
        )
        assert response.status_code == 201

    def test_update_event_times_with_invalid_format(self, admin_client, event):
        """Test updating event with invalid time format."""
        response = admin_client.put(
            f"/api/events/{event.id}", json={"start_time": "not-a-valid-date"}
        )
        assert response.status_code == 400

    def test_update_event_flier_path(self, admin_client, event):
        """Test updating event flier path."""
        response = admin_client.put(
            f"/api/events/{event.id}", json={"flier_path": "/uploads/new-flier.png"}
        )
        assert response.status_code == 200

    def test_create_event_missing_title(self, admin_client, department):
        """Test creating event without title."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = admin_client.post(
            "/api/events",
            json={
                "start_time": start_time,
                "end_time": end_time,
                "department_id": department.id,
            },
        )
        assert response.status_code == 400

    def test_update_event_description(self, admin_client, event):
        """Test updating event description."""
        response = admin_client.put(
            f"/api/events/{event.id}", json={"description": "Updated description"}
        )
        assert response.status_code == 200

    def test_get_events_sort_by_title(self, client):
        """Test getting events sorted by title."""
        response = client.get("/api/events?sort=title")
        assert response.status_code == 200

    def test_get_events_sort_by_capacity(self, client):
        """Test getting events sorted by capacity."""
        response = client.get("/api/events?sort=capacity")
        assert response.status_code == 200

    def test_get_event_with_attendees(self, client, event):
        """Test getting event with attendees included."""
        response = client.get(f"/api/events/{event.id}?include_attendees=true")
        assert response.status_code == 200

    def test_register_for_inactive_event(self, authenticated_client, event):
        """Test registering for inactive event."""
        event.is_active = False
        db.session.commit()

        response = authenticated_client.post(f"/api/events/{event.id}/register")
        assert response.status_code == 400

    def test_register_for_full_event(self, authenticated_client, admin_user, event):
        """Test registering for full event."""
        event.max_capacity = 1
        db.session.commit()

        # Fill the event with a different user
        att = Attendance(event_id=event.id, user_id=admin_user.id)
        db.session.add(att)
        db.session.commit()

        # authenticated_client is logged in as student_user, try to register
        response = authenticated_client.post(f"/api/events/{event.id}/register")
        assert response.status_code == 400

    def test_get_registrations_wrong_department(self, dept_admin_client, admin_user, department):
        """Test department admin cannot get registrations for other department's event."""
        from app.models import Department, Event

        # Create event in different department
        other_dept = Department(name="Other Dept")
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

        response = dept_admin_client.get(f"/api/events/{other_event.id}/registrations")
        assert response.status_code == 403

    def test_generate_qr_code_wrong_department(self, dept_admin_client, admin_user):
        """Test department admin cannot generate QR for other department's event."""
        from app.models import Department, Event

        # Create event in different department
        other_dept = Department(name="Another Dept")
        db.session.add(other_dept)
        db.session.commit()

        other_event = Event(
            title="Another Event",
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=2),
            department_id=other_dept.id,
            created_by=admin_user.id,
        )
        db.session.add(other_event)
        db.session.commit()

        response = dept_admin_client.get(f"/api/events/{other_event.id}/qr-code")
        assert response.status_code == 403

    def test_create_event_with_form_data(self, admin_client, department):
        """Test creating event with form data (not JSON)."""
        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        # Use form data instead of JSON
        response = admin_client.post(
            "/api/events",
            data={
                "title": "Form Event",
                "start_time": start_time,
                "end_time": end_time,
                "department_id": str(department.id),
            },
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 201

    def test_create_event_with_file_upload(self, admin_client, department):
        """Test creating event with file upload."""
        from io import BytesIO

        start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        # Create a fake image file
        data = {
            "title": "Event with File",
            "start_time": start_time,
            "end_time": end_time,
            "department_id": str(department.id),
            "flier": (BytesIO(b"fake image content"), "test_flier.png"),
        }

        response = admin_client.post(
            "/api/events",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        resp_data = response.get_json()
        # Flier path should be set when file is uploaded
        assert resp_data["event"]["flier_path"] is not None

    def test_register_event_email_failure(self, authenticated_client, event, monkeypatch):
        """Test event registration succeeds even if email fails."""
        import app.email

        # Mock send_registration_confirmation to raise exception
        def mock_send_email(*args, **kwargs):
            raise Exception("Email service unavailable")

        monkeypatch.setattr(app.email, "send_registration_confirmation", mock_send_email)

        response = authenticated_client.post(f"/api/events/{event.id}/register")
        # Registration should succeed despite email failure
        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Successfully registered for event"
