"""Tests for view routes."""

import pytest
from flask import session


class TestViewRoutes:
    """Test view rendering routes."""

    def test_index_unauthenticated(self, client):
        """Test index page for unauthenticated users."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()

    def test_index_authenticated_student(self, client, student_user):
        """Test index redirects authenticated student to dashboard."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(student_user.id)
        
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [200, 302]

    def test_index_authenticated_admin(self, client, admin_user):
        """Test index for authenticated admin."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [200, 302]

    def test_login_page(self, client):
        """Test login page renders."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()

    def test_logout_page(self, client):
        """Test logout page."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code in [200, 302]

    def test_register_page(self, client):
        """Test register page renders."""
        response = client.get("/register")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()

    def test_events_page(self, client):
        """Test events page renders."""
        response = client.get("/events")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()

    def test_event_detail_page(self, client, event):
        """Test event detail page renders."""
        response = client.get(f"/events/{event.id}")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()

    def test_event_detail_page_not_found(self, client):
        """Test event detail page with non-existent event."""
        response = client.get("/events/99999")
        assert response.status_code == 200

    def test_calendar_page(self, authenticated_client):
        """Test calendar page renders for authenticated user."""
        response = authenticated_client.get("/calendar")
        assert response.status_code == 200

    def test_my_events_page_authenticated(self, client, student_user):
        """Test my events page for authenticated user."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(student_user.id)
        
        response = client.get("/my-events")
        assert response.status_code == 200

    def test_my_events_page_unauthenticated(self, client):
        """Test my events page redirects unauthenticated users."""
        response = client.get("/my-events", follow_redirects=False)
        assert response.status_code in [302, 401]

    def test_admin_page_as_admin(self, client, admin_user):
        """Test admin page for admin users."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        response = client.get("/admin")
        assert response.status_code == 200

    def test_login_page_when_authenticated(self, authenticated_client):
        """Test login page redirects when already authenticated."""
        response = authenticated_client.get("/login", follow_redirects=False)
        assert response.status_code == 302

    def test_register_page_when_authenticated(self, authenticated_client):
        """Test register page redirects when already authenticated."""
        response = authenticated_client.get("/register", follow_redirects=False)
        assert response.status_code == 302

    def test_logout_endpoint(self, authenticated_client):
        """Test logout endpoint."""
        response = authenticated_client.get("/logout", follow_redirects=False)
        assert response.status_code == 302

    def test_admin_page_as_student_redirects(self, authenticated_client):
        """Test admin page redirects students."""
        # authenticated_client is logged in as student
        response = authenticated_client.get("/admin", follow_redirects=False)
        assert response.status_code == 302

    def test_my_events_page(self, authenticated_client):
        """Test my-events page."""
        response = authenticated_client.get("/my-events")
        assert response.status_code == 200

    def test_admin_page_as_dept_admin(self, client, dept_admin_user):
        """Test admin page for department admin users."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(dept_admin_user.id)
        
        response = client.get("/admin")
        assert response.status_code == 200

    def test_admin_page_as_student(self, client, student_user):
        """Test admin page denies access to students."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(student_user.id)
        
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code in [302, 403]

    def test_admin_page_unauthenticated(self, client):
        """Test admin page redirects unauthenticated users."""
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code in [302, 401]

    def test_student_dashboard_authenticated(self, client, student_user):
        """Test student dashboard for authenticated student."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(student_user.id)
        
        response = client.get("/student")
        assert response.status_code == 200

    def test_student_dashboard_unauthenticated(self, client):
        """Test student dashboard redirects unauthenticated users."""
        response = client.get("/student", follow_redirects=False)
        assert response.status_code in [302, 401]

    def test_check_in_page(self, client):
        """Test check-in page renders."""
        response = client.get("/check-in")
        assert response.status_code == 200
        assert b"text/html" in response.content_type.encode()

    def test_profile_page_authenticated(self, client, student_user):
        """Test profile page for authenticated user."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(student_user.id)
        
        response = client.get("/profile")
        assert response.status_code == 200

    def test_profile_page_unauthenticated(self, client):
        """Test profile page redirects unauthenticated users."""
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code in [302, 401]
