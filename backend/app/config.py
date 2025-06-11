from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str
    EMAIL_HOST: str
    EMAIL_PORT: int = 587
    EMAIL_USER: str
    EMAIL_PASSWORD: str

    jwt_secret_key: str
    jwt_algorithm: str
    jwt_expire_minutes: int

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
