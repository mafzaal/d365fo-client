"""Metadata management for D365 F&O client."""

import json
import os
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional, Any

from .models import EntityInfo, ActionInfo


class MetadataManager:
    """Handles metadata operations for F&O client"""
    
    def __init__(self, cache_dir: str):
        """Initialize metadata manager
        
        Args:
            cache_dir: Directory for metadata cache files
        """
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, "odata_metadata.xml")
        self.entities_cache = os.path.join(cache_dir, "entities.json")
        self.actions_cache = os.path.join(cache_dir, "actions.json")
        self._root = None
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
    
    @property
    def root(self) -> Optional[ET.Element]:
        """Get parsed metadata root, loading if needed
        
        Returns:
            Parsed XML root element or None if not available
        """
        if self._root is None and os.path.exists(self.metadata_file):
            try:
                tree = ET.parse(self.metadata_file)
                self._root = tree.getroot()
            except Exception as e:
                print(f"Error loading metadata: {e}")
        return self._root
    
    def save_metadata(self, content: str) -> None:
        """Save metadata XML content
        
        Args:
            content: XML metadata content
        """
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            f.write(content)
        self._root = None  # Reset cache
        self._build_caches()
    
    def _build_caches(self) -> None:
        """Build entity and action caches from metadata"""
        if not self.root:
            return
            
        self._build_entities_cache()
        self._build_actions_cache()
    
    def _build_entities_cache(self) -> None:
        """Build entities cache from metadata"""
        entities = {}
        
        for entity_type in self.root.iter():
            if entity_type.tag.endswith('EntityType'):
                entity_name = entity_type.get('Name', '')
                
                # Get keys
                keys = []
                for key_elem in entity_type.iter():
                    if key_elem.tag.endswith('Key'):
                        for prop_ref in key_elem.iter():
                            if prop_ref.tag.endswith('PropertyRef'):
                                keys.append(prop_ref.get('Name', ''))
                
                # Get properties
                properties = []
                for prop in entity_type.iter():
                    if prop.tag.endswith('Property'):
                        properties.append({
                            'name': prop.get('Name', ''),
                            'type': prop.get('Type', ''),
                            'nullable': prop.get('Nullable', 'true')
                        })
                
                entities[entity_name] = {
                    'name': entity_name,
                    'keys': keys,
                    'properties': properties
                }
        
        with open(self.entities_cache, 'w') as f:
            json.dump(entities, f, indent=2)
    
    def _build_actions_cache(self) -> None:
        """Build actions cache from metadata"""
        actions = {}
        
        for action in self.root.iter():
            if action.tag.endswith('Action'):
                action_name = action.get('Name', '')
                is_bound = action.get('IsBound', 'false')
                entity_set_path = action.get('EntitySetPath', '')
                
                # Get parameters
                parameters = []
                return_type = "void"
                annotations = []
                
                for element in action:
                    if element.tag.endswith('Parameter'):
                        parameters.append({
                            'name': element.get('Name', ''),
                            'type': element.get('Type', ''),
                            'nullable': element.get('Nullable', 'true')
                        })
                    elif element.tag.endswith('ReturnType'):
                        return_type = element.get('Type', 'void')
                    elif element.tag.endswith('Annotation'):
                        annotations.append({
                            'term': element.get('Term', ''),
                            'value': element.get('String', '')
                        })
                
                actions[action_name] = {
                    'name': action_name,
                    'is_bound': is_bound,
                    'entity_set_path': entity_set_path,
                    'parameters': parameters,
                    'return_type': return_type,
                    'annotations': annotations
                }
        
        with open(self.actions_cache, 'w') as f:
            json.dump(actions, f, indent=2)
    
    def search_entities(self, pattern: str = "") -> List[str]:
        """Search entities by pattern
        
        Args:
            pattern: Search pattern (regex supported)
            
        Returns:
            List of matching entity names
        """
        if not os.path.exists(self.entities_cache):
            return []
        
        with open(self.entities_cache, 'r') as f:
            entities = json.load(f)
        
        if not pattern:
            return sorted(entities.keys())
        
        flags = re.IGNORECASE
        return sorted([name for name in entities.keys() 
                      if re.search(pattern, name, flags)])
    
    def get_entity_info(self, entity_name: str) -> Optional[EntityInfo]:
        """Get detailed entity information
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            EntityInfo object or None if not found
        """
        if not os.path.exists(self.entities_cache):
            return None
        
        with open(self.entities_cache, 'r') as f:
            entities = json.load(f)
        
        if entity_name not in entities:
            return None
        
        entity_data = entities[entity_name]
        return EntityInfo(
            name=entity_data['name'],
            keys=entity_data['keys'],
            properties=entity_data['properties'],
            actions=[]  # Will be populated when needed
        )
    
    def search_actions(self, pattern: str = "") -> List[str]:
        """Search actions by pattern
        
        Args:
            pattern: Search pattern (regex supported)
            
        Returns:
            List of matching action names
        """
        if not os.path.exists(self.actions_cache):
            return []
        
        with open(self.actions_cache, 'r') as f:
            actions = json.load(f)
        
        if not pattern:
            return sorted(actions.keys())
        
        flags = re.IGNORECASE
        return sorted([name for name in actions.keys() 
                      if re.search(pattern, name, flags)])
    
    def get_action_info(self, action_name: str) -> Optional[ActionInfo]:
        """Get detailed action information
        
        Args:
            action_name: Name of the action
            
        Returns:
            ActionInfo object or None if not found
        """
        if not os.path.exists(self.actions_cache):
            return None
        
        with open(self.actions_cache, 'r') as f:
            actions = json.load(f)
        
        if action_name not in actions:
            return None
        
        action_data = actions[action_name]
        return ActionInfo(
            name=action_data['name'],
            is_bound=action_data['is_bound'] == 'true',
            entity_set_path=action_data['entity_set_path'],
            parameters=action_data['parameters'],
            return_type=action_data['return_type'],
            annotations=action_data['annotations']
        )
    
    def is_metadata_available(self) -> bool:
        """Check if metadata is available
        
        Returns:
            True if metadata file exists
        """
        return os.path.exists(self.metadata_file)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get metadata cache information
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "metadata_file_exists": os.path.exists(self.metadata_file),
            "entities_cache_exists": os.path.exists(self.entities_cache),
            "actions_cache_exists": os.path.exists(self.actions_cache),
            "cache_directory": self.cache_dir
        }