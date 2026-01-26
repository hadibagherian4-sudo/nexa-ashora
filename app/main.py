# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# .env loader (اختیاری ولی پیشنهاد می‌شود)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.db import db_init
from app.routers import auth, home, content, forum, profile, admin

app = FastAPI()

db_init()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# اگر کسی مستقیم بیاد /، بفرستش /start
# (اگر سشن داشت، خود home.py می‌برتش پنل)
@app.get("/_")
def health():
    return {"ok": True}

app.include_router(auth.router)
app.include_router(home.router)
app.include_router(content.router)
app.include_router(forum.router)
app.include_router(profile.router)
app.include_router(admin.router)
