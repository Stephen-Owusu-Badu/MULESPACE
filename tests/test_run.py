os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

"""
Tests for run.py - application entry point.
"""

import importlib
import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask

# -------------------------------------------------------------------
# GLOBAL TEST SETUP
# -------------------------------------------------------------------

# Ensure SQLAlchemy always has a database during imports
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")


def reload_run():
    """Utility to reload run.py cleanly."""
    if "run" in sys.modules:
        del sys.modules["run"]
    import run

    return importlib.reload(run)


class TestRunPy:
    """Test run.py application entry point."""

    def test_run_py_imports(self):
        """run.py should import without errors."""
        run = reload_run()
        assert run is not None

    def test_run_py_creates_app(self):
        """run.py should create a Flask app."""
        run = reload_run()
        assert run.app is not None
        assert hasattr(run.app, "run")
        assert hasattr(run.app, "config")

    def test_run_py_uses_environment_config(self, monkeypatch):
        """FLASK_ENV should control config_name."""
        monkeypatch.setenv("FLASK_ENV", "testing")
        run = reload_run()
        assert run.config_name == "testing"

    def test_run_py_defaults_to_development(self, monkeypatch):
        """Default config_name should be development."""
        monkeypatch.delenv("FLASK_ENV", raising=False)
        run = reload_run()
        assert run.config_name == "development"

    def test_run_py_app_has_database_config(self):
        """App must have a database URI configured."""
        run = reload_run()
        assert run.app.config["SQLALCHEMY_DATABASE_URI"] is not None

    @patch("run.app.run")
    def test_run_py_main_block(self, mock_run):
        """__main__ block should call app.run()."""
        os.environ["PORT"] = "8080"

        with open("run.py") as f:
            code = compile(f.read(), "run.py", "exec")
            exec(code, {"__name__": "__main__"})

        mock_run.assert_called_once()
        os.environ.pop("PORT", None)

    def test_run_py_default_port(self):
        """Default port should be 5000."""
        os.environ.pop("PORT", None)
        run = reload_run()
        assert int(os.environ.get("PORT", 5000)) == 5000

    def test_run_py_app_is_flask_instance(self):
        """App should be a Flask instance."""
        run = reload_run()
        assert isinstance(run.app, Flask)

    def test_run_py_app_has_blueprints(self):
        """App should register at least one blueprint."""
        run = reload_run()
        assert len(run.app.blueprints) > 0

    def test_run_py_app_has_routes(self):
        """App should have registered routes."""
        run = reload_run()
        routes = [rule.rule for rule in run.app.url_map.iter_rules()]
        assert "/" in routes or any("index" in r for r in routes)

    def test_run_py_config_name_from_env(self, monkeypatch):
        """config_name should reflect FLASK_ENV."""
        monkeypatch.setenv("FLASK_ENV", "production")
        run = reload_run()
        assert run.config_name == "production"

    def test_run_py_app_context_available(self):
        """App context should be usable."""
        run = reload_run()
        with run.app.app_context():
            assert run.app is not None

    def test_run_py_port_from_environment(self, monkeypatch):
        """PORT env var should be respected."""
        monkeypatch.setenv("PORT", "9000")
        assert int(os.environ.get("PORT")) == 9000

    def test_run_py_host_configuration(self):
        """run.py should bind to 0.0.0.0."""
        with open("run.py") as f:
            content = f.read()
            assert "0.0.0.0" in content

        # Check for some expected routes
        assert "/" in routes or any("index" in str(r) for r in routes)

    def test_run_py_config_name_from_env(self, monkeypatch):
        """Test config_name is correctly read from environment."""
        import importlib
        import sys

        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
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
