"""Label processing utilities for metadata v2.

This module provides utilities for processing D365 Finance & Operations labels
with fallback logic for when label_id doesn't start with '@'.

The main principle is:
- If label_text is already set, preserve it
- If label_id doesn't start with '@', it's already display text - use it as label_text  
- If label_id starts with '@', it's a label reference that needs API resolution

This ensures that direct text labels (like "Customer Groups") are properly
converted to label_text, while label references (like "@SYS123") are preserved
for later resolution through the label API.

Functions:
    process_label_fallback: Core label processing logic
    process_data_entity_labels: Process DataEntityInfo labels
    process_public_entity_labels: Process PublicEntityInfo and property labels
    process_enumeration_labels: Process EnumerationInfo and member labels
    apply_label_fallback: Alias for process_label_fallback (retrieval context)
"""

from typing import Optional

from ..models import DataEntityInfo, EnumerationInfo, PublicEntityInfo


def process_label_fallback(label_id: Optional[str], label_text: Optional[str]) -> Optional[str]:
    """Process label text with fallback to label_id when it doesn't start with '@'
    
    This function implements the core logic for handling D365 F&O labels where:
    - If label_text is already set, use it
    - If label_id doesn't start with '@', it's already display text
    - If label_id starts with '@', it needs resolution via label API
    
    Args:
        label_id: Label identifier (may be actual text or @-prefixed ID)
        label_text: Existing label text (may be None)
        
    Returns:
        Processed label text with fallback applied
    """
    # If label_text is already set, use it
    if label_text:
        return label_text
    
    # If label_id doesn't start with '@', it's already the text
    if label_id and not label_id.startswith('@'):
        return label_id
    
    # Return None for @-prefixed labels without resolved text
    return None


def process_data_entity_labels(entity: DataEntityInfo) -> DataEntityInfo:
    """Process data entity labels with fallback logic
    
    Args:
        entity: Data entity info to process
        
    Returns:
        Processed data entity info with label fallback applied
    """
    entity.label_text = process_label_fallback(entity.label_id, entity.label_text)
    return entity


def process_public_entity_labels(entity: PublicEntityInfo) -> PublicEntityInfo:
    """Process public entity labels with fallback logic
    
    Args:
        entity: Public entity info to process
        
    Returns:
        Processed public entity info with label fallback applied
    """
    # Process entity label
    entity.label_text = process_label_fallback(entity.label_id, entity.label_text)
    
    # Process property labels
    for prop in entity.properties:
        prop.label_text = process_label_fallback(prop.label_id, prop.label_text)
    
    return entity


def process_enumeration_labels(enumeration: EnumerationInfo) -> EnumerationInfo:
    """Process enumeration labels with fallback logic
    
    Args:
        enumeration: Enumeration info to process
        
    Returns:
        Processed enumeration info with label fallback applied
    """
    # Process enumeration label
    enumeration.label_text = process_label_fallback(enumeration.label_id, enumeration.label_text)
    
    # Process member labels
    for member in enumeration.members:
        member.label_text = process_label_fallback(member.label_id, member.label_text)
    
    return enumeration


# Alias for backward compatibility during data retrieval
apply_label_fallback = process_label_fallback