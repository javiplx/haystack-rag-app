import logging
import sys

from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import (
    Field,
    ValidationError,
    model_validator,
    field_validator
)


class Settings(BaseSettings):
    opensearch_host: str = Field(default="http://localhost:9200", description="OpenSearch host URL")
    opensearch_user: str = Field(default="admin", description="OpenSearch username")
    opensearch_password: str = Field(default="admin", description="OpenSearch password")
    generator: str = Field(default="openai", description="Generator to use (currently openai only)")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    use_openai_embedder: bool = Field(default=True, description="Use OpenAI embedder")
    log_level: str = Field(default="INFO", description="Logging level")
    haystack_log_level: str = Field(default="INFO", description="Haystack logging level")
    index_on_startup: bool = Field(default=True, description="Always index files on startup")
    pipelines_from_yaml: bool = Field(default=False, description="Load pipelines from YAML files")
    pipelines_dir: Path = Field(
        default=Path(__file__).resolve().parent.parent / "pipelines",
        description="Path to pipelines directory"
    )
    file_storage_path: Path = Field(
        default=Path(__file__).resolve().parent.parent / "files",
        description="Path to file storage"
    )
    
    @model_validator(mode='after')
    def validate_openai_api_key(self):
        if (self.generator == 'openai' or self.use_openai_embedder) and not self.openai_api_key:
            raise ValueError(
                "OpenAI API key is required when using the OpenAI generator or OpenAI embedder"
            )
        return self

    @field_validator('log_level', 'haystack_log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return upper_v

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False  # This allows case-insensitive matching of env vars

def load_settings():
    try:
        # Load .env file if it exists
        #print(f"Looking for .env file at: {Settings.Config.env_file.resolve()}")
        load_dotenv(Settings.Config.env_file)
        return Settings()
    except ValidationError as e:
        print("Error: Failed to load configuration settings.", file=sys.stderr)
        print("\nMissing or invalid settings:", file=sys.stderr)
        for error in e.errors():
            if "loc" in error and error["loc"]:
                field = ".".join(str(item) for item in error["loc"])
            else:
                field = "Unknown field"
            message = error.get("msg", "No error message provided")
            print(f"- {field}: {message}", file=sys.stderr)
        print("\nPlease check your .env file or environment variables.", file=sys.stderr)
        print(f"Expected .env file location: {Settings.Config.env_file.resolve()}", file=sys.stderr)
        sys.exit(1)

# This will read from environment variables or .env file
settings = load_settings()
