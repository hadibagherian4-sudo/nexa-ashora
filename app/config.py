# app/config.py
import os

# ---- Database ----
DB_PATH = os.getenv("NEXA_DB_PATH", "nexa.db")

# ---- Auth / Cookies ----
COOKIE_NAME = os.getenv("COOKIE_NAME", "nexa_session")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"

# ---- Manager credentials (ENV) ----
MANAGER_PHONE = os.getenv("MANAGER_PHONE", "09146862029")
MANAGER_NID = os.getenv("MANAGER_NID", "136232506")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD", "Hadi136236")

# ---- JWT (optional) ----
JWT_SECRET = os.getenv("NEXA_JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
JWT_ALG = "HS256"
