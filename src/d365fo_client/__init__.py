"""Microsoft Dynamics 365 Finance & Operations client package.

A comprehensive Python client for connecting to D365 F&O and performing:
- Metadata download, storage, and search
- OData action method calls
- CRUD operations on data entities
- OData query parameters support
- Label text retrieval and caching
- Multilingual label support
- Entity metadata with resolved labels

Basic Usage:
    from d365fo_client import FOClient, FOClientConfig
    
    config = FOClientConfig(
        base_url="https://your-fo-environment.dynamics.com",
        use_default_credentials=True
    )
    
    async with FOClient(config) as client:
        # Download metadata
        await client.download_metadata()
        
        # Search entities
        entities = client.search_entities("customer")
        
        # Get entities
        customers = await client.get_entities("Customers", top=10)
        
        # Get labels
        label_text = await client.get_label_text("@SYS13342")

Quick Start:
    from d365fo_client import create_client
    
    client = create_client("https://your-fo-environment.dynamics.com")
"""

__version__ = "0.1.0"
__author__ = "Muhammad Afzaal"
__email__ = "mo@thedataguy.pro"

# Import main classes and functions for public API
from .client import FOClient, create_client
from .models import (
    FOClientConfig, QueryOptions, LabelInfo, 
    EntityInfo, EntityPropertyInfo, ActionInfo
)
from .exceptions import (
    FOClientError, AuthenticationError, MetadataError,
    EntityError, ActionError, LabelError, ConfigurationError, NetworkError
)
from .main import main

# Public API
__all__ = [
    # Main client
    "FOClient",
    "create_client",
    
    # Configuration and models
    "FOClientConfig",
    "QueryOptions",
    "LabelInfo",
    "EntityInfo", 
    "EntityPropertyInfo",
    "ActionInfo",
    
    # Exceptions
    "FOClientError",
    "AuthenticationError",
    "MetadataError", 
    "EntityError",
    "ActionError",
    "LabelError",
    "ConfigurationError",
    "NetworkError",
    
    # Entry point
    "main",
]
