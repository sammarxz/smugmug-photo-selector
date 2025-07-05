from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Servidor
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    RELOAD: bool = True

    # SmugMug API
    SMUGMUG_API_BASE_URL: str = 'https://api.smugmug.com/api/v2'
    SMUGMUG_WEB_URI_LOOKUP: str = 'https://api.smugmug.com/api/v2!weburilookup'
    SMUGMUG_USER_AGENT: str = 'SmugMugPhotoSelector/1.0'

    # OAuth (obrigatório)
    SMUGMUG_API_KEY: Optional[str] = None
    SMUGMUG_API_SECRET: Optional[str] = None
    SMUGMUG_ACCESS_TOKEN: Optional[str] = None
    SMUGMUG_ACCESS_TOKEN_SECRET: Optional[str] = None

    # Timeouts
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    class Config:
        env_file = '.env'


settings = Settings()
