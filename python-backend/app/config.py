from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    azure_notification_hub_connection_string: str
    azure_notification_hub_name: str
    vapid_public_key: str
    vapid_private_key: str
    vapid_subject: str = "mailto:you@example.com"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


settings = Settings()
