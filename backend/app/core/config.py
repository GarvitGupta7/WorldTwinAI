from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name:str="AI Digital Twin of a Small World"
    app_env:str="development"
    database_url:str="sqlite:///./digital_twin.db"
    cors_origins:str="http://localhost:5173"
    default_simulation_seed:int=42
    default_simulation_duration_minutes:int=60
    log_level:str="INFO"
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")

@lru_cache
def get_settings(): return Settings()
