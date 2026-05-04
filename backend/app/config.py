from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./autoai.db"
    HOST: str = "127.0.0.1"
    PORT: int = 18765


settings = Settings()
