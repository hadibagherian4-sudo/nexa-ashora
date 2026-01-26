from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from ..deps import require_login, status_fa

router = APIRouter(prefix="/profile", tags=["profile"])
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def profile(request: Request, auth=Depends(require_login)):
    return templates.TemplateResponse("profile.html", {"request": request, "auth": auth, "status_fa": status_fa})
