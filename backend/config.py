"""Environment-driven app configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config fields the fixture-backed phase needs; more get added per phase."""

    data_source: str = "fixture"
    fixture_path: str = "data/fixtures/sample_transfers.json"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
