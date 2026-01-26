# app/config.py
import os

COOKIE_NAME = os.getenv("COOKIE_NAME", "nexa_session")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"

MANAGER_PHONE = os.getenv("MANAGER_PHONE", "09146862029")
MANAGER_NID = os.getenv("MANAGER_NID", "136232506")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD", "Hadi136236")
