from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from ..paths import TEMPLATES_DIR
from ..deps import require_login

router = APIRouter(prefix="/profile", tags=["profile"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("")
def profile(request: Request, auth=Depends(require_login)):
    return templates.TemplateResponse("profile.html", {"request": request, "auth": auth})
