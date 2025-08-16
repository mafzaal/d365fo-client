"""OData query utilities for D365 F&O client."""

from typing import Optional
from urllib.parse import quote, urlencode

from .models import QueryOptions


class QueryBuilder:
    """Utility class for building OData queries"""
    
    @staticmethod
    def build_query_string(options: Optional[QueryOptions] = None) -> str:
        """Build OData query string from options
        
        Args:
            options: Query options to convert
            
        Returns:
            URL query string (with leading ? if parameters exist)
        """
        if not options:
            return ""
        
        params = {}
        
        if options.select:
            params['$select'] = ','.join(options.select)
        
        if options.filter:
            params['$filter'] = options.filter
        
        if options.expand:
            params['$expand'] = ','.join(options.expand)
        
        if options.orderby:
            params['$orderby'] = ','.join(options.orderby)
        
        if options.top is not None:
            params['$top'] = str(options.top)
        
        if options.skip is not None:
            params['$skip'] = str(options.skip)
        
        if options.count:
            params['$count'] = 'true'
        
        if options.search:
            params['$search'] = options.search
        
        if params:
            return '?' + urlencode(params, quote_via=quote)
        return ""
    
    @staticmethod
    def encode_key(key: str) -> str:
        """Encode entity key for URL
        
        Args:
            key: Entity key value
            
        Returns:
            URL-encoded key
        """
        return quote(str(key), safe='')
    
    @staticmethod
    def build_entity_url(base_url: str, entity_name: str, key: Optional[str] = None) -> str:
        """Build entity URL
        
        Args:
            base_url: Base F&O URL
            entity_name: Entity set name
            key: Optional entity key
            
        Returns:
            Complete entity URL
        """
        base = f"{base_url.rstrip('/')}/data/{entity_name}"
        if key:
            encoded_key = QueryBuilder.encode_key(key)
            return f"{base}('{encoded_key}')"
        return base
    
    @staticmethod
    def build_action_url(base_url: str, action_name: str, 
                        entity_name: Optional[str] = None, 
                        entity_key: Optional[str] = None) -> str:
        """Build action URL
        
        Args:
            base_url: Base F&O URL
            action_name: Action name
            entity_name: Optional entity name for bound actions
            entity_key: Optional entity key for bound actions
            
        Returns:
            Complete action URL
        """
        base = base_url.rstrip('/')
        
        if entity_name and entity_key:
            # Bound action on specific entity
            encoded_key = QueryBuilder.encode_key(entity_key)
            return f"{base}/data/{entity_name}('{encoded_key}')/Microsoft.Dynamics.DataEntities.{action_name}"
        elif entity_name:
            # Bound action on entity set
            return f"{base}/data/{entity_name}/Microsoft.Dynamics.DataEntities.{action_name}"
        else:
            # Unbound action
            return f"{base}/data/Microsoft.Dynamics.DataEntities.{action_name}"