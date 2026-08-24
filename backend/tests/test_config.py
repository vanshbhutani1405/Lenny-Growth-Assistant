def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    from app.core.config import Settings
    settings = Settings()
    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.async_database_url.startswith("postgresql+asyncpg://")
