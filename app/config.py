# app/config.py
import os

DB_PATH = os.getenv("NEXA_DB_PATH", "nexa.db")

JWT_SECRET = os.getenv("NEXA_JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
JWT_ALG = "HS256"
COOKIE_NAME = "nexa_token"
COOKIE_SECURE = os.getenv("NEXA_COOKIE_SECURE", "0") == "1"  # روی HTTPS بذار 1

# Manager credentials (ENV)
MANAGER_PHONE = os.getenv("NEXA_MANAGER_PHONE", "")
MANAGER_NID = os.getenv("NEXA_MANAGER_NID", "")
MANAGER_PASSWORD = os.getenv("NEXA_MANAGER_PASSWORD", "")

