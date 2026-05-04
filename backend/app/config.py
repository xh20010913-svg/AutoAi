from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AUTOAI_", "env_file": ".env", "extra": "ignore"}

    database_url: str = "sqlite+aiosqlite:///./autoai.db"
    host: str = "127.0.0.1"
    port: int = 18765


settings = Settings()
