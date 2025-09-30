from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from sqlalchemy.orm import Session

from backend.schemas.token import Token
from backend.schemas.client import ClientCredentials
from backend.security import create_access_token
from backend.core.config import settings
from backend.database import get_db
from backend.services.client_app_manager import client_app_manager

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(credentials: ClientCredentials, db: Session = Depends(get_db)):
    """
    Authenticate client and return a JWT access token.
    """
    client_app = client_app_manager.authenticate_client(
        db, client_id=credentials.client_id, client_secret=credentials.client_secret
    )
    
    if not client_app:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client ID or secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": client_app.client_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
