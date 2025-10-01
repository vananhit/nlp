from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Admin
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    class Config:
        env_file = "backend/.env"

settings = Settings()
