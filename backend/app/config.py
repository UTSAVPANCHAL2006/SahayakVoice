"""
Configuration for Sahayak Voice V2.
Loads settings from environment variables or .env file.
"""

from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "v2/backend/.env", "../backend/.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    port: int = Field(default=8001, validation_alias="PORT")
    databaseUrl: str = Field(
        default="postgresql+psycopg://localhost:5432/sahayak",
        validation_alias="DATABASE_URL",
    )
    openaiApiKey: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openaiModel: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

    sarvamApiKey: str = Field(default="", validation_alias="SARVAM_API_KEY")
    sarvamModel: str = Field(default="bulbul:v3", validation_alias="SARVAM_MODEL")
    sarvamSttModel: str = Field(default="saaras:v3", validation_alias="SARVAM_STT_MODEL")
    sarvamSpeaker: str = Field(default="kavya", validation_alias="SARVAM_SPEAKER")
    managerSpeaker: str = Field(default="ratan", validation_alias="MANAGER_SPEAKER")
    agentGender: str = Field(default="female", validation_alias="AGENT_GENDER")
    enableTts: bool = Field(default=True, validation_alias="ENABLE_TTS")
    demoOtp: str = Field(default="1234", validation_alias="DEMO_OTP")
    sarvamPace: float = Field(default=1.30, validation_alias="SARVAM_PACE")

    # Langfuse Observability
    langfusePublicKey: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_PUBLIC_KEY", "LANGFUSE_PK"),
    )
    langfuseSecretKey: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_SECRET_KEY", "LANGFUSE_SK"),
    )
    langfuseHost: str = Field(
        default="https://us.cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL", "LANGFUSE_HOST", "LANGFUSE_BASEURL"),
    )

    @property
    def langfuseEnabled(self) -> bool:
        return bool(self.langfusePublicKey and self.langfuseSecretKey)


settings = Settings()
