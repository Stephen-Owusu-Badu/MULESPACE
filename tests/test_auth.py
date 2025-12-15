class TestAuthRoutes:
    """Test authentication routes."""

    def test_register_success(self, client, department):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "username": "newuser",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
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
                "username": "newusername",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "department_id": department.id,
            },
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "Email already registered" in data["error"]

    def test_register_duplicate_username(self, client, student_user, department):
        """Test registration with duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newemail@test.com",
                "username": "student",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "department_id": department.id,
            },
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "Username already taken" in data["error"]

    def test_login_success(self, client, student_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={"username": "student", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Login successful"
        assert data["user"]["username"] == "student"

    def test_login_invalid_credentials(self, client, student_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={"username": "student", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "Invalid username or password" in data["error"]

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post("/api/auth/login", json={"username": "student"})

        assert response.status_code == 400

    def test_login_inactive_user(self, client, student_user):
        """Test login with inactive user."""
        student_user.is_active = False
        from app import db

        db.session.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "student", "password": "password123"},
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "Account is disabled" in data["error"]

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

    def test_get_departments(self, client, department):
        """Test getting all departments."""
        response = client.get("/api/auth/departments")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["departments"]) >= 1
        assert data["departments"][0]["name"] == "Computer Science"
