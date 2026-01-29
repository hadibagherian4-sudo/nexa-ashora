import os
from pydantic import BaseModel

from .paths import PROJECT_ROOT


class Settings(BaseModel):
    # --- general ---
    APP_NAME: str = os.getenv("APP_NAME", "NEXA")

    # IMPORTANT: on shared-hosting, relative paths often break.
    # This keeps sqlite DB next to your project by default.
    DB_URL: str = os.getenv(
        "DB_URL",
        f"sqlite:///{(PROJECT_ROOT / 'nexa.db').as_posix()}",
    )

    # put a long random secret in hosting env variables
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET")

    # --- manager fixed credentials (better to set in env on server) ---
    MANAGER_PHONE: str = os.getenv("MANAGER_PHONE", "09146862029")
    MANAGER_NID: str = os.getenv("MANAGER_NID", "1362362506")
    MANAGER_PASSWORD: str = os.getenv("MANAGER_PASSWORD", "Hadi136236")


settings = Settings()
