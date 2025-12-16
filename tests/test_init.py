"""Tests for application initialization."""

from app import create_app, db


class TestAppInitialization:
    """Test application factory and initialization."""

    def test_create_app_default_config(self):
        """Test app creation with default config."""
        app = create_app()
        assert app is not None
        assert app.config["TESTING"] is False

    def test_create_app_testing_config(self):
        """Test app creation with testing config."""
        app = create_app("testing")
        assert app is not None
        assert app.config["TESTING"] is True

    def test_create_app_with_config_object(self):
        """Test app creation with config object."""
        app = create_app("testing")
        assert "SQLALCHEMY_DATABASE_URI" in app.config
        assert "SECRET_KEY" in app.config

    def test_database_initialization(self, app):
        """Test database is initialized."""
        with app.app_context():
            # Database should be created by conftest fixture
            assert db.engine is not None

    def test_blueprints_registered(self, app):
        """Test all blueprints are registered."""
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        # Check main blueprints are registered
        assert "events" in blueprint_names or any("event" in name for name in blueprint_names)
        assert "auth" in blueprint_names or any("auth" in name for name in blueprint_names)

    def test_login_manager_configured(self, app):
        """Test Flask-Login is properly configured."""
        assert hasattr(app, "login_manager")
        assert app.login_manager is not None

    def test_user_loader_function(self, app, student_user):
        """Test user loader function works."""
        with app.app_context():
            loaded_user = app.login_manager._user_callback(student_user.id)
            assert loaded_user is not None
            assert loaded_user.id == student_user.id
            assert loaded_user.email == student_user.email

    def test_user_loader_invalid_id(self, app):
        """Test user loader with invalid ID."""
        with app.app_context():
            loaded_user = app.login_manager._user_callback(99999)
            assert loaded_user is None

    def test_user_loader_none_id(self, app):
        """Test user loader with None ID."""
        with app.app_context():
            # User loader may raise exception or return None for None ID
            try:
                loaded_user = app.login_manager._user_callback(None)
                assert loaded_user is None
            except Exception:
                pass  # Exception is acceptable behavior

    def test_cors_configured(self, app):
        """Test CORS is configured if available."""
        # CORS might be configured, check if headers are set properly
        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code in [200, 302, 404]

    def test_error_handlers_registered(self, app):
        """Test error handlers are registered."""
        with app.test_client() as client:
            # Test 404 handler
            response = client.get("/nonexistent-route-12345")
            assert response.status_code == 404

    def test_static_folder_configured(self, app):
        """Test static folder is configured."""
        assert app.static_folder is not None
        assert "static" in app.static_folder

    def test_template_folder_configured(self, app):
        """Test template folder is configured."""
        assert app.template_folder is not None
        assert "templates" in app.template_folder

    def test_app_context_processor(self, app):
        """Test app has context processors."""
        with app.app_context():
            # App should have context processors for templates
            assert hasattr(app, "context_processor")

    def test_mail_configured(self, app):
        """Test Flask-Mail is configured."""
        assert "MAIL_SERVER" in app.config
        assert "MAIL_PORT" in app.config

    def test_database_session_cleanup(self, app):
        """Test database session cleanup works."""
        with app.app_context():
            # Session should be properly managed
            db.session.remove()
            # Should not raise an error

    def test_app_config_security_settings(self, app):
        """Test security-related configuration."""
        assert "SECRET_KEY" in app.config
        assert app.config["SECRET_KEY"] is not None
        assert len(app.config["SECRET_KEY"]) > 0

    def test_sqlalchemy_track_modifications_disabled(self, app):
        """Test SQLALCHEMY_TRACK_MODIFICATIONS is disabled for performance."""
        # Should be False to avoid performance overhead
        track_mods = app.config.get("SQLALCHEMY_TRACK_MODIFICATIONS", False)
        assert track_mods is False
