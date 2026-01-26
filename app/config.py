from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "NEXA"
    DB_URL: str = "sqlite:///./nexa.db"
    SESSION_SECRET: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"

    # manager fixed credentials
    MANAGER_PHONE: str = "09146862029"
    MANAGER_NID: str = "1362362506"
    MANAGER_PASSWORD: str = "Hadi136236"

settings = Settings()
