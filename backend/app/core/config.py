from pydantic import Field, SecretStr
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """All values come from the environment / .env; missing ones fail at startup."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Project Bridge"
    api_v1_prefix: str = "/api/v1"

    db_driver: str = "sqlite+aiosqlite"
    db_user: str = "bridge"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "bridge.db"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)
    cookie_secure: bool = False
    google_client_id: str = ""
    mail_mode: Literal["file", "smtp", "disabled"] = "file"
    public_url: str = "http://localhost:3000"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = ""
    smtp_starttls: bool = True
    llm_provider: Literal["gemini"] = "gemini"
    gemini_api_key: SecretStr = SecretStr("")
    llm_model: str = Field(default="gemini-3.5-flash-lite", pattern=r"^[A-Za-z0-9._-]+$")
    llm_timeout_seconds: int = Field(default=40, ge=5, le=90)
    llm_max_output_tokens: int = Field(default=4096, ge=128, le=8192)
    pattern_min_messages: int = Field(default=3, ge=3, le=20)
    pattern_min_conversations: int = Field(default=2, ge=2, le=10)
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def database_url(self) -> str:
        if self.db_driver == "sqlite+aiosqlite":
            return URL.create(self.db_driver, database=self.db_name).render_as_string(hide_password=False)
        # URL.create escapes special characters in the credentials.
        return URL.create(
            drivername=self.db_driver,
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)


settings = Settings()
