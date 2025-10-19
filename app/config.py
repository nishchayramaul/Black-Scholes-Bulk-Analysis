from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000", 
        "http://localhost:4200",  # Angular dev server
        "http://localhost:8080",
        "http://127.0.0.1:4200",  # Alternative localhost format
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
