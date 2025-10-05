import asyncio
from fastapi import FastAPI, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from backend.api.api import api_router
from backend.database import engine
from backend.models import usage_log, client_app, admin_login_history
from backend.core.config import settings
from backend.socket_manager import socket_app, trigger_crawl_and_wait

# Create the database tables
usage_log.Base.metadata.create_all(bind=engine)
client_app.Base.metadata.create_all(bind=engine)
admin_login_history.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SEO Content Refactoring API",
    description="An API to analyze and refactor content for SEO.",
    version="1.0.0"
)

# Add SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# --- API Routes ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SEO Content Refactoring API"}


app.include_router(api_router, prefix="/api")
app.mount("/socket.io", socket_app)
