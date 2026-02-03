from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://suchi:suchi_dev_password@postgres:5432/suchi"

    # LinkedIn Parser
    parser_service_url: str = "http://linkedin-parser:8001"

    # Storage (S3-compatible)
    storage_endpoint: str = "http://minio:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_bucket: str = "suchi-pdfs"

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24 * 7  # 1 week

    class Config:
        env_prefix = ""


settings = Settings()
