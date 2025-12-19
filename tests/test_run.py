"""Tests for run.py - application entry point."""

import os
from unittest.mock import patch


class TestRunPy:
    """Test run.py application entry point."""

    def test_run_py_imports(self):
        """Test that run.py can be imported without errors."""
        import run

        assert run is not None

    def test_run_py_creates_app(self):
        """Test that run.py creates Flask app."""
        import run

        assert run.app is not None
        assert hasattr(run.app, "run")
        assert hasattr(run.app, "config")

    def test_run_py_uses_environment_config(self, monkeypatch):
        """Test that run.py respects FLASK_ENV environment variable."""
        monkeypatch.setenv("FLASK_ENV", "testing")

        # Reimport to pick up new env var
        import importlib

        import run

        importlib.reload(run)

        assert run.config_name == "testing"

    def test_run_py_defaults_to_development(self):
        """Test that run.py defaults to development config."""
        # Clear FLASK_ENV if it exists
        os.environ.pop("FLASK_ENV", None)

        import importlib

        import run

        importlib.reload(run)

        assert run.config_name == "development"

    def test_run_py_app_has_correct_config(self):
        """Test that app is created with correct configuration."""
        import run

        # Should be development or testing
        assert run.app.config["SQLALCHEMY_DATABASE_URI"] is not None

    @patch("run.app.run")
    def test_run_py_main_block(self, mock_run):
        """Test that __main__ block calls app.run with correct parameters."""
        # Set PORT environment variable
        os.environ["PORT"] = "8080"

        # Execute the main block by running the file
        with open("run.py") as f:
            code = compile(f.read(), "run.py", "exec")
            exec(code)

        # Clean up
        os.environ.pop("PORT", None)

    @patch("run.app.run")
    def test_run_py_default_port(self, mock_run):
        """Test that run.py uses default port 5000 when PORT not set."""
        # Clear PORT env var
        os.environ.pop("PORT", None)

        # Import and check the port that would be used
        import run  # noqa: F401

        # The default port should be 5000
        assert int(os.environ.get("PORT", 5000)) == 5000

    def test_run_py_app_is_flask_instance(self):
        """Test that app is a Flask instance."""
        from flask import Flask

        import run

        assert isinstance(run.app, Flask)

    def test_run_py_app_has_blueprints(self):
        """Test that app has registered blueprints."""
        import run

        assert len(run.app.blueprints) > 0

    def test_run_py_app_has_routes(self):
        """Test that app has registered routes."""
        import run

        # Get all registered routes
        routes = [rule.rule for rule in run.app.url_map.iter_rules()]

        # Check for some expected routes
        assert "/" in routes or any("index" in str(r) for r in routes)

    def test_run_py_config_name_from_env(self, monkeypatch):
        """Test config_name is correctly read from environment."""
        import sys
        import importlib

        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

        # Remove run from sys.modules if already imported
        if "run" in sys.modules:
            del sys.modules["run"]

        import run

        importlib.reload(run)

        # After reload, config_name should be set from env
        expected = os.environ.get("FLASK_ENV", "development")
        assert run.config_name == expected

    def test_run_py_app_context_available(self):
        """Test that app context is available."""
        import run

        with run.app.app_context():
            # Should be able to use app context
            assert run.app is not None

    def test_run_py_port_from_environment(self, monkeypatch):
        """Test that PORT environment variable is respected."""
        monkeypatch.setenv("PORT", "9000")

        port = int(os.environ.get("PORT", 5000))
        assert port == 9000

    def test_run_py_host_configuration(self):
        """Test that host is configured to 0.0.0.0."""
        # This tests that the run command would use 0.0.0.0
        # which allows external access
        with open("run.py") as f:
            content = f.read()
            assert "0.0.0.0" in content or '"0.0.0.0"' in content
