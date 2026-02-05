from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://suchi:suchi_dev_password@postgres:5432/suchi"

    # Claude API (primary LLM)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # OpenAI (fallback LLM for cheap tasks)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Gmail OAuth2
    gmail_credentials_json: str = "/app/secrets/credentials.json"
    gmail_token_json: str = "/app/secrets/token.json"
    gmail_sender_email: str = ""
    gmail_sender_name: str = "Suchi - Executive Search Agent"

    # Rajamohan (the candidate)
    rajamohan_email: str = ""
    rajamohan_name: str = "Rajamohan"

    # Agent behaviour
    inbox_check_interval_minutes: int = 15
    daily_briefing_hour: int = 9  # 9 AM IST
    daily_briefing_timezone: str = "Asia/Kolkata"
    initial_followup_days: int = 4
    max_escalation_level: int = 5
    max_daily_outreach: int = 20

    # One-pager asset
    one_pager_path: str = "app/assets/rajamohan_one_pager.md"

    # CORS
    cors_origins: str = ""

    class Config:
        env_prefix = ""


settings = Settings()
