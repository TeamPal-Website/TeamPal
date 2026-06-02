from pathlib import Path
from typing import Annotated, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DB_URL(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ['http://localhost:5173'])

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def split_allowed_origins(cls, value: str | list[str]) -> list[str] | str:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(',') if origin.strip()]
        return value
    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str | None = None

    @property
    def celery_broker(self) -> str | None:
        return self.CELERY_BROKER_URL or self.REDIS_URL
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET: str | None = None
    S3_REGION: str = 'us-east-1'
    S3_PUBLIC_BASE_URL: str | None = None
    S3_AVATAR_PREFIX: str = 'avatars/'
    S3_ADDRESSING_STYLE: Literal['path', 'virtual'] = 'path'

    SMTP_HOST: str = 'smtp.gmail.com'
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    model_config = SettingsConfigDict(env_file=ROOT_DIR / '.env', extra='ignore')
settings = Settings()
