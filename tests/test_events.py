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
