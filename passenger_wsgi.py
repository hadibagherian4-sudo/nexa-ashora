from a2wsgi import ASGIMiddleware
from app.main import app

# Passenger دنبال آبجکت "application" می‌گرده
application = ASGIMiddleware(app)
