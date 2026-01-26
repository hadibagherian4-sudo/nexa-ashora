from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import engine
from .models import Base

from .routers import auth, home, content, forum, profile, admin

def create_app():
    app = FastAPI(title=settings.APP_NAME)

    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(home.router)
    app.include_router(content.router)
    app.include_router(forum.router)
    app.include_router(profile.router)
    app.include_router(admin.router)

    return app

app = create_app()
