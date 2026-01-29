from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # .../app
PROJECT_ROOT = BASE_DIR.parent                      # پروژه (کنار requirements.txt)

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
