"""Pydantic settings model for environment variable management."""

import os
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .utils import get_default_cache_directory


class LogLevel(str, Enum):
    """Valid logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TransportProtocol(str, Enum):
    """Valid MCP transport protocols."""
    
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    STREAMABLE_HTTP = "streamable-http"


class D365FOSettings(BaseSettings):
    """Pydantic settings model for D365FO environment variables.
    
    This model provides type-safe access to all D365FO environment variables
    with proper validation, defaults, and documentation.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="D365FO_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # === Core D365FO Connection Settings ===
    
    base_url: Optional[str] = Field(
        default="https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        description="D365FO environment URL",
        alias="D365FO_BASE_URL"
    )
    
    # === Azure AD Authentication Settings ===
    
    client_id: Optional[str] = Field(
        default=None,
        description="Azure AD client ID (optional, used with client credentials flow)",
        alias="D365FO_CLIENT_ID"
    )
    
    client_secret: Optional[str] = Field(
        default=None,
        description="Azure AD client secret (optional, used with client credentials flow)",
        alias="D365FO_CLIENT_SECRET"
    )
    
    tenant_id: Optional[str] = Field(
        default=None,
        description="Azure AD tenant ID (optional, used with client credentials flow)",
        alias="D365FO_TENANT_ID"
    )
    
    # === MCP Server Transport Settings ===
    
    mcp_transport: TransportProtocol = Field(
        default=TransportProtocol.STDIO,
        description="Default transport protocol (stdio, sse, http, streamable-http)",
        alias="D365FO_MCP_TRANSPORT"
    )
    
    http_host: str = Field(
        default="127.0.0.1",
        description="Default HTTP host",
        alias="D365FO_HTTP_HOST"
    )
    
    http_port: int = Field(
        default=8000,
        gt=0,
        le=65535,
        description="Default HTTP port",
        alias="D365FO_HTTP_PORT"
    )
    
    http_stateless: bool = Field(
        default=False,
        description="Enable stateless mode (true/false)",
        alias="D365FO_HTTP_STATELESS"
    )
    
    http_json: bool = Field(
        default=False,
        description="Enable JSON response mode (true/false)",
        alias="D365FO_HTTP_JSON"
    )
    
    # === Connection and Performance Settings ===
    
    max_concurrent_requests: int = Field(
        default=10,
        gt=0,
        description="Max concurrent requests",
        alias="D365FO_MAX_CONCURRENT_REQUESTS"
    )
    
    request_timeout: int = Field(
        default=30,
        gt=0,
        description="Request timeout in seconds",
        alias="D365FO_REQUEST_TIMEOUT"
    )
    
    timeout: int = Field(
        default=60,
        gt=0,
        description="General timeout in seconds",
        alias="D365FO_TIMEOUT"
    )
    
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
        alias="D365FO_VERIFY_SSL"
    )
    
    # === Logging Settings ===
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        alias="D365FO_LOG_LEVEL"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        description="Custom log file path (default: ~/.d365fo-mcp/logs/fastmcp-server.log)",
        alias="D365FO_LOG_FILE"
    )
    
    # === Cache and Metadata Settings ===
    
    cache_dir: Optional[str] = Field(
        default=None,
        description="General cache directory",
        alias="D365FO_CACHE_DIR"
    )
    
    meta_cache_dir: Optional[str] = Field(
        default=None,
        description="Metadata cache directory (default: ~/.d365fo-mcp/cache)",
        alias="D365FO_META_CACHE_DIR"
    )
    
    use_label_cache: bool = Field(
        default=True,
        description="Enable label caching",
        alias="D365FO_LABEL_CACHE"
    )
    
    label_cache_expiry_minutes: int = Field(
        default=1440,  # 24 hours
        gt=0,
        description="Label cache expiry in minutes",
        alias="D365FO_LABEL_EXPIRY"
    )
    
    use_cache_first: bool = Field(
        default=True,
        description="Use cache first before making API calls",
        alias="D365FO_USE_CACHE_FIRST"
    )
    
    # === Debug and Development Settings ===
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        alias="DEBUG"
    )
    
    @field_validator("log_file", mode="before")
    @classmethod
    def validate_log_file(cls, v):
        """Validate and set default log file path."""
        if v is None:
            # Return default log file path
            log_dir = Path.home() / ".d365fo-mcp" / "logs"
            return str(log_dir / "fastmcp-server.log")
        return v
    
    @field_validator("cache_dir", mode="before")
    @classmethod
    def validate_cache_dir(cls, v):
        """Validate and set default cache directory."""
        if v is None:
            return get_default_cache_directory()
        return v
    
    @field_validator("meta_cache_dir", mode="before")
    @classmethod
    def validate_meta_cache_dir(cls, v):
        """Validate and set default metadata cache directory."""
        if v is None:
            cache_dir = Path.home() / ".d365fo-mcp" / "cache"
            return str(cache_dir)
        return v
    
    @field_validator("http_stateless", "http_json", "use_label_cache", "use_cache_first", "verify_ssl", "debug", mode="before")
    @classmethod
    def validate_boolean_env_vars(cls, v):
        """Convert string environment variables to booleans."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    def get_default_log_file(self) -> str:
        """Get the default log file path."""
        log_dir = Path.home() / ".d365fo-mcp" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir / "fastmcp-server.log")
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        # Ensure log file directory exists
        if self.log_file:
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure cache directories exist
        if self.cache_dir:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
            
        if self.meta_cache_dir:
            Path(self.meta_cache_dir).mkdir(parents=True, exist_ok=True)
    
    def has_client_credentials(self) -> bool:
        """Check if client credentials are configured."""
        return all([self.client_id, self.client_secret, self.tenant_id])
    
    def get_startup_mode(self) -> Literal["profile_only", "default_auth", "client_credentials"]:
        """Determine startup mode based on configuration."""
        if self.base_url and self.base_url != "https://usnconeboxax1aos.cloud.onebox.dynamics.com":
            if self.has_client_credentials():
                return "client_credentials"
            else:
                return "default_auth"
        return "profile_only"
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return self.dict()
    
    def to_env_dict(self) -> dict:
        """Convert settings to environment variable dictionary."""
        env_dict = {}
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if value is not None:
                # Use the alias if available, otherwise construct the env var name
                if field_info.alias:
                    env_var_name = field_info.alias
                else:
                    env_var_name = f"D365FO_{field_name.upper()}"
                
                # Convert boolean values to string
                if isinstance(value, bool):
                    env_dict[env_var_name] = "true" if value else "false"
                else:
                    env_dict[env_var_name] = str(value)
        
        return env_dict


# Global settings instance
_settings: Optional[D365FOSettings] = None


def get_settings(reload: bool = False) -> D365FOSettings:
    """Get the global settings instance.
    
    Args:
        reload: If True, force reload settings from environment
        
    Returns:
        D365FOSettings instance
    """
    global _settings
    
    if _settings is None or reload:
        _settings = D365FOSettings()
        _settings.ensure_directories()
    
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance.
    
    Useful for testing when you want to reload settings.
    """
    global _settings
    _settings = None