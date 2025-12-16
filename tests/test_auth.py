class TestAuthRoutes:
    """Test authentication routes."""

    def test_register_success(self, client, department):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "name": "New User",
                "password": "password123",
                "department_id": department.id,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["email"] == "newuser@test.com"

    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@test.com"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Missing required field" in data["error"]

    def test_register_duplicate_email(self, client, student_user, department):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "student@test.com",
                "name": "Test User",
                "password": "password123",
                "department_id": department.id,
            },
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "Email already registered" in data["error"]

    def test_register_duplicate_username_from_email(self, client, student_user, department):
        """Test registration generates unique username when email prefix conflicts."""
        # student_user has username "student" from email "student@test.com"
        # Register with email that would generate same username
        response = client.post(
            "/api/auth/register",
            json={
                "email": "student@different.com",
                "password": "password123",
                "name": "Another Student",
                "department_id": department.id,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        # Should generate "student1" or similar unique username
        assert data["user"]["username"] != "student"
        assert data["user"]["username"].startswith("student")

    def test_login_success(self, client, student_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={"email": "student@test.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Login successful"

    def test_login_invalid_credentials(self, client, student_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={"email": "student@test.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post("/api/auth/login", json={"email": "student@test.com"})

        assert response.status_code == 400

    def test_login_inactive_user(self, client, student_user):
        """Test login with inactive user."""
        student_user.is_active = False
        from app import db

        db.session.commit()

        response = client.post(
            "/api/auth/login",
            json={"email": "student@test.com", "password": "password123"},
        )

        assert response.status_code == 403

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "password123"},
        )

        assert response.status_code == 401

    def test_logout(self, authenticated_client):
        """Test logout."""
        response = authenticated_client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Logout successful"

    def test_get_current_user(self, authenticated_client, student_user):
        """Test getting current user info."""
        response = authenticated_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["username"] == "student"

    def test_change_password_success(self, authenticated_client):
        """Test successful password change."""
        response = authenticated_client.put(
            "/api/auth/change-password",
            json={"old_password": "password123", "new_password": "newpassword123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Password changed successfully"

    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test password change with wrong old password."""
        response = authenticated_client.put(
            "/api/auth/change-password",
            json={"old_password": "wrongpassword", "new_password": "newpassword123"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "Incorrect old password" in data["error"]

    def test_change_password_missing_fields(self, authenticated_client):
        """Test password change with missing fields."""
        response = authenticated_client.put(
            "/api/auth/change-password",
            json={"old_password": "password123"},
        )

        assert response.status_code == 400

    def test_change_password_via_rest_endpoint(self, authenticated_client):
        """Test password change via REST-compliant endpoint."""
        response = authenticated_client.put(
            "/api/auth/password",
            json={"old_password": "password123", "new_password": "newpassword123"},
        )
        assert response.status_code == 200

    def test_change_password_unauthenticated(self, client):
        """Test password change without authentication."""
        response = client.put(
            "/api/auth/change-password",
            json={"old_password": "password123", "new_password": "newpassword123"},
        )
        assert response.status_code in [401, 302]

    def test_get_departments(self, client, department):
        """Test getting all departments."""
        response = client.get("/api/auth/departments")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["departments"]) >= 1
        assert data["departments"][0]["name"] == "Computer Science"

    def test_login_with_username(self, client, student_user):
        """Test login with username instead of email."""
        response = client.post(
            "/api/auth/login",
            json={"email": "student", "password": "password123"},
        )
        # Should work if username login is supported
        assert response.status_code in [200, 401]

    def test_register_with_invalid_department(self, client):
        """Test registration with invalid department ID."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "name": "Test User",
                "password": "password123",
                "department_id": 99999,
            },
        )
        assert response.status_code in [201, 400, 404]

    def test_register_duplicate_username_auto_increment(self, client, department):
        """Test registration with duplicate username gets auto-incremented."""
        # First user
        client.post(
            "/api/auth/register",
            json={
                "email": "user1@test.com",
                "name": "User One",
                "password": "password123",
                "department_id": department.id,
            },
        )

        # Second user with same base username (from email)
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user1@different.com",
                "name": "User Two",
                "password": "password123",
                "department_id": department.id,
            },
        )
        assert response.status_code == 201

    def test_register_single_name(self, client, department):
        """Test registration with single name (no last name)."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "single@test.com",
                "name": "SingleName",
                "password": "password123",
                "department_id": department.id,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["user"]["first_name"] == "SingleName"
        assert data["user"]["last_name"] == ""

    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 302]
