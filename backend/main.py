from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from backend.api.api import api_router
from backend.database import engine
from backend.models import usage_log, client_app # Import the models module
from backend.core.config import settings

# Create the database tables
usage_log.Base.metadata.create_all(bind=engine)
client_app.Base.metadata.create_all(bind=engine)


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

@app.get("/")
def read_root():
    return {"message": "Welcome to the SEO Content Refactoring API"}

app.include_router(api_router, prefix="/api")
