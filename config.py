from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str = ""  # comma-separated admin telegram IDs
    DATABASE_URL: str = "sqlite+aiosqlite:///learnbot.db"

    # Private channel where content is stored
    CONTENT_CHANNEL_ID: str = ""

    # Required subscription channels (comma-separated, e.g. "@chan1,-100123456")
    REQUIRED_CHANNELS: str = ""

    # Referral: how many invites = 1 free pass
    INVITES_PER_FREE_PASS: int = 5

    # Throttle: max messages per second
    THROTTLE_RATE: float = 0.5

    # Lockout after wrong code attempts
    MAX_WRONG_ATTEMPTS: int = 3
    LOCKOUT_MINUTES: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def admin_id_list(self) -> list[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    @property
    def required_channel_list(self) -> list[str]:
        if not self.REQUIRED_CHANNELS:
            return []
        return [x.strip() for x in self.REQUIRED_CHANNELS.split(",") if x.strip()]


settings = Settings()
