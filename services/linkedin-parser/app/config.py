from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001
    max_pdf_size_mb: int = 10

    class Config:
        env_prefix = "PARSER_"


settings = Settings()
