# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import db_init

from app.routers import auth, home, content, forum, profile, admin

app = FastAPI()

db_init()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(home.router)
app.include_router(content.router)
app.include_router(forum.router)
app.include_router(profile.router)
app.include_router(admin.router)

