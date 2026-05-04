from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./autoai.db"
    HOST: str = "127.0.0.1"
    PORT: int = 18765
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Auto-assign algorithm weights (must sum to 1.0)
    WEIGHT_SKILL_MATCH: float = 0.4
    WEIGHT_LOAD: float = 0.3
    WEIGHT_SUCCESS_RATE: float = 0.3

    # Auto-assign scheduling
    AUTO_ASSIGN_INTERVAL_SECONDS: int = 60
    AUTO_ASSIGN_ENABLED: bool = True
    STARVATION_THRESHOLD_MINUTES: int = 30


settings = Settings()
