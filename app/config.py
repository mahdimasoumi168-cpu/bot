from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Telegram Cross Poster"
    database_url: str
    redis_url: str
    telegram_bot_token: str
    telegram_webhook_secret: str
    telegram_source_chat_id: str
    admin_username: str = "admin"
    admin_password: str
    public_base_url: str = ""
    eitaa_token: str = ""
    eitaa_chat_id: str = ""
    bale_token: str = ""
    bale_chat_id: str = ""
    rubika_token: str = ""
    rubika_chat_id: str = ""
    rubika_endpoint: str = ""
    soroush_endpoint: str = ""
    soroush_token: str = ""
    soroush_chat_id: str = ""
    request_timeout: float = 45.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
