from datetime import datetime, timedelta

from app import db
from app.models import Event


class TestCalendarRoutes:
    """Test calendar routes."""

    def test_get_calendar_events(self, client, event):
        """Test getting calendar events."""
        response = client.get("/api/calendar")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) >= 1

    def test_get_calendar_events_with_date_filter(self, client, event):
        """Test calendar events with date range."""
        start = datetime.utcnow().isoformat()
        end = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = client.get(f"/api/calendar?start={start}&end={end}")

        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data

    def test_get_calendar_events_with_department_filter(self, client, event, department):
        """Test calendar events filtered by department."""
        response = client.get(f"/api/calendar?department_id={department.id}")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) >= 1

    def test_get_calendar_events_invalid_start_date(self, client):
        """Test calendar with invalid start date."""
        response = client.get("/api/calendar?start=invalid-date")

        assert response.status_code == 400

    def test_get_calendar_events_invalid_end_date(self, client):
        """Test calendar with invalid end date."""
        response = client.get("/api/calendar?end=invalid-date")

        assert response.status_code == 400

    def test_check_conflicts_with_conflicts(self, client, event):
        """Test conflict detection with overlapping events."""
        response = client.post(
            "/api/calendar/conflicts",
            json={
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["has_conflicts"] is True
        assert data["conflict_count"] >= 1

    def test_check_conflicts_without_conflicts(self, client):
        """Test conflict detection without conflicts."""
        start = (datetime.utcnow() + timedelta(days=10)).isoformat()
        end = (datetime.utcnow() + timedelta(days=10, hours=2)).isoformat()

        response = client.post(
            "/api/calendar/conflicts",
            json={"start_time": start, "end_time": end},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["has_conflicts"] is False

    def test_check_conflicts_exclude_event(self, client, event):
        """Test conflict detection excluding the event being edited."""
        response = client.post(
            "/api/calendar/conflicts",
            json={
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "event_id": event.id,
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["has_conflicts"] is False

    def test_check_conflicts_missing_fields(self, client):
        """Test conflict check with missing fields."""
        response = client.post("/api/calendar/conflicts", json={"start_time": "2024-01-01"})

        assert response.status_code == 400

    def test_check_conflicts_invalid_dates(self, client):
        """Test conflict check with invalid dates."""
        response = client.post(
            "/api/calendar/conflicts",
            json={"start_time": "invalid", "end_time": "invalid"},
        )

        assert response.status_code == 400

    def test_get_upcoming_events(self, client, event):
        """Test getting upcoming events."""
        response = client.get("/api/calendar/upcoming")

        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data
        assert "count" in data

    def test_get_upcoming_events_custom_days(self, client, event):
        """Test upcoming events with custom days parameter."""
        response = client.get("/api/calendar/upcoming?days=14")

        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data

    def test_get_upcoming_events_with_department_filter(self, client, event, department):
        """Test upcoming events filtered by department."""
        response = client.get(f"/api/calendar/upcoming?department_id={department.id}")

        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data

    def test_get_upcoming_events_excludes_past(self, app, client, department, admin_user):
        """Test that upcoming events excludes past events."""
        # Create past event
        past_event = Event(
            title="Past Event",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow() - timedelta(hours=22),
            department_id=department.id,
            created_by=admin_user.id,
        )
        db.session.add(past_event)
        db.session.commit()

        response = client.get("/api/calendar/upcoming")

        assert response.status_code == 200
        data = response.get_json()
        # Past event should not be in upcoming
        event_titles = [e["title"] for e in data["events"]]
        assert "Past Event" not in event_titles

    def test_get_calendar_events_endpoint(self, authenticated_client, event):
        """Test GET /api/calendar/events endpoint."""
        response = authenticated_client.get("/api/calendar/events")
        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data

    def test_add_event_to_calendar_as_admin(self, admin_client, event):
        """Test admin adding event to their calendar (registering)."""
        response = admin_client.post(
            "/api/calendar/events",
            json={"event_id": event.id},
        )
        assert response.status_code == 201

    def test_remove_event_from_calendar_as_admin(self, admin_client, event):
        """Test admin removing event from their calendar."""
        # First add it
        admin_client.post(
            "/api/calendar/events",
            json={"event_id": event.id},
        )
        # Then remove it
        response = admin_client.delete(f"/api/calendar/events/{event.id}")
        assert response.status_code == 200

    def test_get_calendar_events_endpoint_details(self, authenticated_client, event):
        """Test /api/calendar/events endpoint with event details."""
        response = authenticated_client.get("/api/calendar/events")
        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data

    def test_get_calendar_statistics(self, authenticated_client, event):
        """Test getting calendar statistics."""
        response = authenticated_client.get("/api/calendar/statistics")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_events" in data or "stats" in data

    def test_check_conflicts_with_same_event(self, client, event):
        """Test conflict check excludes same event."""
        response = client.post(
            "/api/calendar/conflicts",
            json={
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "exclude_event_id": event.id,
            },
        )
        assert response.status_code == 200

    def test_get_calendar_events_with_limit(self, authenticated_client, event):
        """Test calendar events with limit."""
        response = authenticated_client.get("/api/calendar/events?limit=5")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) <= 5

    def test_add_to_calendar_missing_event_id(self, authenticated_client):
        """Test adding to calendar without event_id."""
        response = authenticated_client.post("/api/calendar/events", json={})
        assert response.status_code == 400

    def test_add_to_calendar_nonexistent_event(self, authenticated_client):
        """Test adding non-existent event to calendar."""
        response = authenticated_client.post("/api/calendar/events", json={"event_id": 99999})
        assert response.status_code == 404

    def test_add_to_calendar_duplicate(self, authenticated_client, event):
        """Test adding same event to calendar twice."""
        authenticated_client.post("/api/calendar/events", json={"event_id": event.id})
        response = authenticated_client.post("/api/calendar/events", json={"event_id": event.id})
        assert response.status_code == 409

    def test_remove_from_calendar_not_registered(self, authenticated_client, event):
        """Test removing event not in calendar."""
        response = authenticated_client.delete(f"/api/calendar/events/{event.id}")
        assert response.status_code == 404
