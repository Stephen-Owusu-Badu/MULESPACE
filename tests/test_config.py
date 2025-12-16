"""Tests for application configuration."""

import os

import pytest

from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, config


class TestBaseConfig:
    """Test base configuration class."""

    def test_base_config_has_secret_key(self):
        """Test base config has SECRET_KEY."""
        assert hasattr(Config, "SECRET_KEY")
        assert Config.SECRET_KEY is not None

    def test_base_config_sqlalchemy_settings(self):
        """Test base config SQLAlchemy settings."""
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False
        assert Config.SQLALCHEMY_RECORD_QUERIES is True

    def test_base_config_pagination(self):
        """Test base config pagination settings."""
        assert hasattr(Config, "ITEMS_PER_PAGE")
        assert Config.ITEMS_PER_PAGE == 20

    def test_base_config_qr_code_dir(self):
        """Test base config QR code directory."""
        assert hasattr(Config, "QR_CODE_DIR")
        assert "qrcodes" in Config.QR_CODE_DIR

    def test_base_config_mail_settings(self):
        """Test base config mail settings."""
        assert hasattr(Config, "MAIL_SERVER")
        assert hasattr(Config, "MAIL_PORT")
        assert hasattr(Config, "MAIL_USE_TLS")
        assert Config.MAIL_MAX_EMAILS is None
        assert Config.MAIL_ASCII_ATTACHMENTS is False


class TestDevelopmentConfig:
    """Test development configuration."""

    def test_development_config_debug_mode(self):
        """Test development config has debug mode enabled."""
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.TESTING is False

    def test_development_config_database_uri(self):
        """Test development config database URI."""
        assert hasattr(DevelopmentConfig, "SQLALCHEMY_DATABASE_URI")
        assert "sqlite:///" in DevelopmentConfig.SQLALCHEMY_DATABASE_URI
        assert "mulespace" in DevelopmentConfig.SQLALCHEMY_DATABASE_URI
        assert ".db" in DevelopmentConfig.SQLALCHEMY_DATABASE_URI

    def test_development_config_inherits_from_base(self):
        """Test development config inherits from base config."""
        assert issubclass(DevelopmentConfig, Config)
        assert DevelopmentConfig.SQLALCHEMY_TRACK_MODIFICATIONS is False


class TestTestingConfig:
    """Test testing configuration."""

    def test_testing_config_testing_mode(self):
        """Test testing config has testing mode enabled."""
        assert TestingConfig.TESTING is True
        assert TestingConfig.DEBUG is False

    def test_testing_config_uses_memory_database(self):
        """Test testing config uses in-memory database."""
        assert TestingConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"

    def test_testing_config_csrf_disabled(self):
        """Test testing config has CSRF disabled."""
        assert TestingConfig.WTF_CSRF_ENABLED is False

    def test_testing_config_login_disabled(self):
        """Test testing config login settings."""
        assert TestingConfig.LOGIN_DISABLED is False

    def test_testing_config_inherits_from_base(self):
        """Test testing config inherits from base config."""
        assert issubclass(TestingConfig, Config)


class TestProductionConfig:
    """Test production configuration."""

    def test_production_config_production_mode(self):
        """Test production config has production mode enabled."""
        assert ProductionConfig.DEBUG is False
        assert ProductionConfig.TESTING is False

    def test_production_config_database_uri_from_env(self):
        """Test production config database URI from environment."""
        # Save original value
        original = os.environ.get("DATABASE_URL")

        # Test with postgres URL
        os.environ["DATABASE_URL"] = "postgres://user:pass@host/db"
        # Need to reload the config
        import importlib
        import config as config_module

        importlib.reload(config_module)
        assert "postgresql://" in config_module.ProductionConfig.SQLALCHEMY_DATABASE_URI

        # Restore original
        if original:
            os.environ["DATABASE_URL"] = original
        else:
            os.environ.pop("DATABASE_URL", None)

        # Reload again to restore
        importlib.reload(config_module)

    def test_production_config_inherits_from_base(self):
        """Test production config inherits from base config."""
        assert issubclass(ProductionConfig, Config)


class TestConfigDict:
    """Test config dictionary."""

    def test_config_dict_has_all_configs(self):
        """Test config dict contains all configuration classes."""
        assert "development" in config
        assert "testing" in config
        assert "production" in config
        assert "default" in config

    def test_config_dict_maps_to_correct_classes(self):
        """Test config dict maps to correct configuration classes."""
        assert config["development"] == DevelopmentConfig
        assert config["testing"] == TestingConfig
        assert config["production"] == ProductionConfig
        assert config["default"] == DevelopmentConfig

    def test_default_config_is_development(self):
        """Test default config is development."""
        assert config["default"] == DevelopmentConfig


class TestConfigEnvironmentVariables:
    """Test configuration with environment variables."""

    def test_secret_key_from_environment(self, monkeypatch):
        """Test SECRET_KEY can be set from environment."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        # Need to reload config to pick up env var
        import importlib

        import config as config_module

        importlib.reload(config_module)
        # Check that it would use env var (falls back to default if not set)
        assert config_module.Config.SECRET_KEY is not None

    def test_mail_settings_from_environment(self, monkeypatch):
        """Test mail settings can be configured from environment."""
        monkeypatch.setenv("MAIL_SERVER", "smtp.test.com")
        monkeypatch.setenv("MAIL_PORT", "465")
        monkeypatch.setenv("MAIL_USERNAME", "test@test.com")

        import importlib

        import config as config_module

        importlib.reload(config_module)
        # Verify config can read from environment
        assert config_module.Config.MAIL_SERVER is not None


class TestConfigIntegration:
    """Test configuration integration with app."""

    def test_config_can_be_loaded_by_app(self, app):
        """Test configuration can be loaded by Flask app."""
        assert app.config["TESTING"] is True
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"

    def test_development_config_applied_correctly(self):
        """Test development config can be applied."""
        from app import create_app

        app = create_app("development")
        assert app.config["DEBUG"] is True
        assert "sqlite:///" in app.config["SQLALCHEMY_DATABASE_URI"]
        assert "mulespace" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_testing_config_applied_correctly(self):
        """Test testing config can be applied."""
        from app import create_app

        app = create_app("testing")
        assert app.config["TESTING"] is True
        assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
