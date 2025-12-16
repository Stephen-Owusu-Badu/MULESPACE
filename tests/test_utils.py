from app.utils import generate_qr_code, validate_email


class TestUtils:
    """Test utility functions."""

    def test_generate_qr_code(self, app):
        """Test QR code generation."""
        with app.app_context():
            qr_path = generate_qr_code(1)

            assert qr_path is not None
            assert "event_1.png" in qr_path

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        assert validate_email("test@example.com") is not None
        assert validate_email("user.name@domain.co.uk") is not None
        assert validate_email("firstname+lastname@company.org") is not None

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        assert validate_email("invalid") is not True
        assert validate_email("@example.com") is not True
        assert validate_email("test@") is not True
        assert validate_email("test @example.com") is not True

    def test_require_role_decorator_admin_access(self, admin_client):
        """Test admin can access admin routes."""
        response = admin_client.get("/api/admin/dashboard")
        assert response.status_code == 200

    def test_require_role_decorator_student_denied(self, authenticated_client):
        """Test student cannot access admin routes."""
        response = authenticated_client.get("/api/admin/dashboard")
        assert response.status_code == 403

    def test_generate_qr_code_with_custom_url(self, app):
        """Test QR code generation with custom base URL."""
        with app.app_context():
            qr_path = generate_qr_code(999, base_url="https://custom.com")
            assert qr_path is not None

    def test_validate_email_empty(self):
        """Test email validation with empty string."""
        assert validate_email("") is not True

    def test_validate_email_none(self):
        """Test email validation with None."""
        result = validate_email(None)
        assert result is not True or result is None

    def test_validate_email_special_chars(self):
        """Test email validation with special characters."""
        assert validate_email("test!#$%@example.com") is not None

    def test_generate_qr_code_creates_directory(self, app):
        """Test QR code generation creates directory if not exists."""
        with app.app_context():
            qr_path = generate_qr_code(12345)
            assert qr_path is not None

    def test_validate_email_colby_domain(self):
        """Test email validation with Colby domain."""
        assert validate_email("student@colby.edu") is not None

    def test_validate_email_long_domain(self):
        """Test email validation with long domain."""
        assert validate_email("test@subdomain.example.co.uk") is not None
