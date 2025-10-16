from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Launch Loop"
    ENV: str = "staging"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Additional allowed origins (comma-separated)
    CORS_ORIGINS: str = ""
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    
    # Anthropic
    ANTHROPIC_API_KEY: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Cloudflare R2
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_PUBLIC_URL: str = ""
    
    # Stripe (will be test keys initially)
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_PRO: Optional[str] = None
    STRIPE_PRICE_ID_ULTIMATE: Optional[str] = None
    
    # Resend
    RESEND_API_KEY: str
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # Domain
    MAIN_DOMAIN: str = "thelaunchloop.com"
    
    # Rate Limiting
    SIGNUP_RATE_LIMIT_PER_IP: int = 10
    GENERATION_RATE_LIMIT_PER_HOUR: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
