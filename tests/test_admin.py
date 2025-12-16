from app import db
from app.models import Attendance, Department, User


class TestAdminRoutes:
    """Test admin routes."""

    def test_get_dashboard_stats_as_admin(self, admin_client):
        """Test getting dashboard stats as admin."""
        response = admin_client.get("/api/admin/dashboard")

        assert response.status_code == 200
        data = response.get_json()
        assert "stats" in data
        assert "total_users" in data["stats"]

    def test_get_dashboard_stats_as_dept_admin(self, dept_admin_client):
        """Test getting dashboard stats as department admin."""
        response = dept_admin_client.get("/api/admin/dashboard")

        assert response.status_code == 200
        data = response.get_json()
        assert "stats" in data
        assert "department_users" in data["stats"]

    def test_get_dashboard_stats_unauthorized(self, authenticated_client):
        """Test dashboard access as student."""
        response = authenticated_client.get("/api/admin/dashboard")
        assert response.status_code == 403

    def test_get_all_users_as_admin(self, admin_client, student_user):
        """Test getting all users as admin."""
        response = admin_client.get("/api/admin/users")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["users"]) >= 1

    def test_get_all_users_with_pagination(self, admin_client):
        """Test user list with pagination."""
        response = admin_client.get("/api/admin/users?page=1&per_page=10")

        assert response.status_code == 200
        data = response.get_json()
        assert "page" in data
        assert "per_page" in data

    def test_get_all_users_unauthorized(self, dept_admin_client):
        """Test getting all users as non-admin."""
        response = dept_admin_client.get("/api/admin/users")
        assert response.status_code == 403

    def test_update_user_as_admin(self, admin_client, student_user):
        """Test updating user as admin."""
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}",
            json={"role": "department_admin", "is_active": True},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["role"] == "department_admin"

    def test_update_user_unauthorized(self, dept_admin_client, student_user):
        """Test updating user as non-admin."""
        response = dept_admin_client.put(
            f"/api/admin/users/{student_user.id}",
            json={"role": "admin"},
        )

        assert response.status_code == 403

    def test_create_department_as_admin(self, admin_client):
        """Test creating department as admin."""
        response = admin_client.post(
            "/api/admin/departments",
            json={
                "name": "New Department",
                "description": "New Description",
                "contact_email": "dept@test.com",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["department"]["name"] == "New Department"

    def test_create_department_missing_name(self, admin_client):
        """Test creating department without name."""
        response = admin_client.post(
            "/api/admin/departments",
            json={"description": "No name"},
        )

        assert response.status_code == 400

    def test_create_department_duplicate(self, admin_client, department):
        """Test creating duplicate department."""
        response = admin_client.post(
            "/api/admin/departments",
            json={"name": "Computer Science"},
        )

        assert response.status_code == 409

    def test_create_department_unauthorized(self, dept_admin_client):
        """Test creating department as non-admin."""
        response = dept_admin_client.post(
            "/api/admin/departments",
            json={"name": "Unauthorized Dept"},
        )

        assert response.status_code == 403

    def test_update_department_as_admin(self, admin_client, department):
        """Test updating department as admin."""
        response = admin_client.put(
            f"/api/admin/departments/{department.id}",
            json={"name": "Updated Department", "description": "Updated"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["department"]["name"] == "Updated Department"

    def test_update_department_unauthorized(self, dept_admin_client, department):
        """Test updating department as non-admin."""
        response = dept_admin_client.put(
            f"/api/admin/departments/{department.id}",
            json={"name": "Unauthorized Update"},
        )

        assert response.status_code == 403

    def test_delete_department_as_admin(self, admin_client):
        """Test deleting empty department."""
        dept = Department(name="Empty Dept")
        db.session.add(dept)
        db.session.commit()

        response = admin_client.delete(f"/api/admin/departments/{dept.id}")
        assert response.status_code == 200

    def test_delete_department_with_users(self, admin_client, department, student_user):
        """Test deleting department with users."""
        response = admin_client.delete(f"/api/admin/departments/{department.id}")

        assert response.status_code == 400
        data = response.get_json()
        assert "Cannot delete department with users" in data["error"]

    def test_delete_department_with_events(self, admin_client, department, event):
        """Test deleting department with events."""
        # Remove users from department
        User.query.filter_by(department_id=department.id).update({"department_id": None})
        db.session.commit()

        response = admin_client.delete(f"/api/admin/departments/{department.id}")

        assert response.status_code == 400
        data = response.get_json()
        assert "Cannot delete department with events" in data["error"]

    def test_delete_department_unauthorized(self, dept_admin_client):
        """Test deleting department as non-admin."""
        dept = Department(name="Test Dept")
        db.session.add(dept)
        db.session.commit()

        response = dept_admin_client.delete(f"/api/admin/departments/{dept.id}")
        assert response.status_code == 403

    def test_get_event_analytics_as_admin(self, admin_client, event, student_user):
        """Test getting event analytics as admin."""
        # Add attendance
        att = Attendance(event_id=event.id, user_id=student_user.id)
        db.session.add(att)
        db.session.commit()

        response = admin_client.get("/api/admin/analytics/events")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["analytics"]) >= 1

    def test_get_event_analytics_as_dept_admin(self, dept_admin_client, event):
        """Test getting event analytics as department admin."""
        response = dept_admin_client.get("/api/admin/analytics/events")

        assert response.status_code == 200
        data = response.get_json()
        assert "analytics" in data

    def test_get_event_analytics_with_department_filter(self, admin_client, department):
        """Test event analytics with department filter."""
        response = admin_client.get(f"/api/admin/analytics/events?department_id={department.id}")

        assert response.status_code == 200
        data = response.get_json()
        assert "analytics" in data

    def test_get_event_analytics_unauthorized(self, authenticated_client):
        """Test event analytics as student."""
        response = authenticated_client.get("/api/admin/analytics/events")
        assert response.status_code == 403

    def test_get_department_analytics_as_admin(self, admin_client, department):
        """Test getting department analytics as admin."""
        response = admin_client.get("/api/admin/analytics/departments")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["analytics"]) >= 1

    def test_get_department_analytics_unauthorized(self, dept_admin_client):
        """Test department analytics as non-admin."""
        response = dept_admin_client.get("/api/admin/analytics/departments")
        assert response.status_code == 403

    def test_get_statistics_as_admin(self, admin_client, event, student_user):
        """Test getting statistics as admin."""
        response = admin_client.get("/api/admin/statistics")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_events" in data
        assert "active_users" in data or "total_users" in data

    def test_get_statistics_as_dept_admin(self, dept_admin_client):
        """Test getting statistics as department admin."""
        response = dept_admin_client.get("/api/admin/statistics")
        assert response.status_code == 200

    def test_get_statistics_unauthorized(self, authenticated_client):
        """Test getting statistics as student."""
        response = authenticated_client.get("/api/admin/statistics")
        assert response.status_code == 403

    def test_update_user_email(self, admin_client, student_user):
        """Test updating user email."""
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}", json={"email": "newemail@test.com"}
        )
        assert response.status_code == 200

    def test_update_user_role(self, admin_client, student_user):
        """Test updating user role."""
        response = admin_client.put(
            f"/api/admin/users/{student_user.id}", json={"role": "department_admin"}
        )
        assert response.status_code == 200

    def test_create_department_with_description(self, admin_client):
        """Test creating department with description."""
        response = admin_client.post(
            "/api/admin/departments",
            json={"name": "New Department", "description": "New Description"},
        )
        assert response.status_code == 201

    def test_get_users_with_role_filter(self, admin_client, student_user):
        """Test filtering users by role."""
        response = admin_client.get("/api/admin/users?role=student")
        assert response.status_code == 200

    def test_get_users_with_department_filter(self, admin_client, department):
        """Test filtering users by department."""
        response = admin_client.get(f"/api/admin/users?department_id={department.id}")
        assert response.status_code == 200

    def test_get_users_with_limit(self, admin_client):
        """Test getting users with limit."""
        response = admin_client.get("/api/admin/users?limit=5")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["users"]) <= 5

    def test_get_dashboard_with_events(self, admin_client, event):
        """Test dashboard statistics include events."""
        response = admin_client.get("/api/admin/dashboard")
        assert response.status_code == 200
        data = response.get_json()
        assert "stats" in data
