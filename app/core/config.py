from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class Settings(BaseSettings):
    MODE: str = 'DEV'
    
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int

    DERIBIT_BASE_URL: str
    
    @property
    def DATABASE_URL(self):
        if self.MODE == 'TEST':
            return 'sqlite+aiosqlite:///:memory:'
        password = quote_plus(str(self.DB_PASS))
        return f"postgresql+asyncpg://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file="",
                                      extra='ignore')
    
settings = Settings() # type: ignore Без дефолтов