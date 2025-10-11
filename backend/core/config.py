from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Admin
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    # Generate a secure key using: import pyotp; pyotp.random_base32()
    TOTP_SECRET_KEY: str

    # Worker
    WORKER_CLIENT_ID: str 
    WORKER_SECRET_ID: str 
    MAX_CONCURRENT_CRAWLS: int = 3

    class Config:
        env_file = "backend/.env"

settings = Settings()
