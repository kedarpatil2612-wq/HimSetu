"""Configuration management module for HIMSETU.

Provides Pydantic-backed application settings supporting defaults, environment
variable overrides with HIMSETU_ prefix, and YAML file configuration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class AppConfig(BaseSettings):
    """Application configuration schema and validator."""

    app_name: str = Field(default="HIMSETU", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: Literal["development", "testing", "production"] = Field(
        default="development", description="Deployment environment"
    )
    log_level: str = Field(default="INFO", description="Console/File logging verbosity level")
    log_file_path: Optional[Path] = Field(default=None, description="Optional log file output path")
    cli_enabled: bool = Field(default=True, description="Enable interactive CLI interface")
    default_permission_level: str = Field(
        default="READ_ONLY", description="Default user security permission tier"
    )
    secret_key: Optional[str] = Field(
        default=None, description="Optional internal secret key (excluded from log dumps)", exclude=True
    )

    model_config = SettingsConfigDict(
        env_prefix="HIMSETU_",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level string against standard logging levels."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in allowed:
            raise ValueError(f"Invalid log_level: '{v}'. Must be one of {sorted(allowed)}")
        return upper_v

    @field_validator("default_permission_level")
    @classmethod
    def validate_permission_level(cls, v: str) -> str:
        """Validate permission level string."""
        allowed = {"READ_ONLY", "LOW_RISK", "HIGH_RISK", "ADMIN"}
        upper_v = v.upper()
        if upper_v not in allowed:
            raise ValueError(f"Invalid default_permission_level: '{v}'. Must be one of {sorted(allowed)}")
        return upper_v

    def get_safe_dict(self) -> Dict[str, Any]:
        """Return configuration dictionary excluding sensitive fields."""
        data = self.model_dump(exclude={"secret_key"})
        if "secret_key" in data:
            data.pop("secret_key")
        return data


def load_config(
    config_path: Optional[Path | str] = None,
    env_file: Optional[Path | str] = None,
) -> AppConfig:
    """Load configuration from optional YAML file and environment variables.

    Args:
        config_path: Path to optional YAML configuration file.
        env_file: Path to optional .env file.

    Returns:
        AppConfig: Validated application configuration instance.

    Raises:
        ValueError: If YAML syntax or configuration values are invalid.
    """
    yaml_kwargs: Dict[str, Any] = {}

    if config_path:
        path = Path(config_path)
        if not path.is_file():
            raise ValueError(f"Configuration file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if content is not None:
                    if not isinstance(content, dict):
                        raise ValueError(f"Invalid YAML content in {path}: expected a dictionary/mapping")
                    yaml_kwargs = content
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse YAML configuration in {path}: {exc}") from exc

    try:
        # Override with environment variables if present
        return AppConfig(**yaml_kwargs)
    except Exception as exc:
        raise ValueError(f"Configuration validation failed: {exc}") from exc
