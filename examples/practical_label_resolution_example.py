#!/usr/bin/env python3
"""
Practical Label Resolution Example

This example shows how to use resolve_labels_generic() in real scenarios
with the d365fo-client package to efficiently resolve labels for various
metadata objects.
"""

import os
import asyncio
from pathlib import Path
from d365fo_client import FOClient, FOClientConfig, resolve_labels_generic
from d365fo_client.metadata_cache import MetadataCache


async def practical_label_resolution_example():
    """Demonstrate practical usage of label resolution utility"""
    
    print("🏷️  Practical Label Resolution Examples")
    print("=" * 50)
    
    # Configuration
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    cache_dir = Path("example_cache")
    
    # Configure client
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        use_label_cache=True,
        cache_dir=cache_dir
    )
    
    try:
        # Initialize metadata cache directly
        cache = MetadataCache(base_url, cache_dir)
        await cache.initialize()
        
        print(f"✅ Connected to: {base_url}")
        print(f"💾 Cache directory: {cache_dir}")
        print()
        
        # Example 1: Batch process multiple entities efficiently
        print("📋 Example 1: Batch Processing Multiple Entities")
        print("-" * 47)
        
        # Get multiple entities without resolving labels individually
        customer_entities = await cache.search_data_entities(
            pattern="Customer", 
            data_service_enabled=True
        )
        
        if customer_entities:
            print(f"Found {len(customer_entities)} customer-related entities")
            
            # Instead of resolving labels one by one (inefficient):
            # for entity in customer_entities:
            #     await resolve_labels_generic(entity, cache)  # Multiple cache calls
            
            # Resolve all at once (efficient - single batch operation):
            await resolve_labels_generic(customer_entities, cache)
            
            print("✅ Resolved labels for all entities in one batch operation")
            
            # Display results
            for entity in customer_entities[:3]:  # Show first 3
                print(f"  {entity.name}: {entity.label_text or 'No label'}")
            
            if len(customer_entities) > 3:
                print(f"  ... and {len(customer_entities) - 3} more")
            print()
        
        # Example 2: Working with detailed entity information
        print("📋 Example 2: Detailed Entity with Properties")
        print("-" * 42)
        
        # Get a specific entity with all its details
        entity_name = "CustomersV3"
        entity = await cache.get_public_entity_info(entity_name, resolve_labels=False)
        
        if entity:
            print(f"Entity: {entity.name}")
            print(f"Properties: {len(entity.properties)}")
            print(f"Actions: {len(entity.actions)}")
            print(f"Navigation Properties: {len(entity.navigation_properties)}")
            
            # Count objects with labels before resolution
            entity_has_label = bool(entity.label_id)
            props_with_labels = len([p for p in entity.properties if p.label_id])
            
            print(f"\nBefore resolution:")
            print(f"  Entity has label: {entity_has_label}")
            print(f"  Properties with labels: {props_with_labels}")
            
            # Resolve all labels (entity + all nested properties, actions, etc.)
            await resolve_labels_generic(entity, cache)
            
            print(f"\nAfter resolution:")
            print(f"  Entity label: {entity.label_text or 'No label'}")
            
            # Show some resolved property labels
            resolved_props = [p for p in entity.properties if p.label_text][:5]
            print(f"  Resolved property labels: {len(resolved_props)}")
            for prop in resolved_props:
                print(f"    {prop.name}: {prop.label_text}")
            print()
        
        # Example 3: Custom processing workflow
        print("📋 Example 3: Custom Processing Workflow")
        print("-" * 39)
        
        # Simulate a workflow where you need to process entities
        # and prepare them for different output formats
        
        # Get entities for processing
        entities = await cache.search_public_entities(pattern="Product")
        
        if entities:
            print(f"Processing {len(entities)} product-related entities...")
            
            # Step 1: Resolve labels for all entities
            await resolve_labels_generic(entities, cache)
            
            # Step 2: Create a summary report
            summary_data = []
            for entity in entities:
                summary_data.append({
                    'technical_name': entity.name,
                    'display_name': entity.label_text or entity.name,
                    'entity_set': entity.entity_set_name,
                    'read_only': entity.is_read_only
                })
            
            # Display summary
            print("Summary Report:")
            for item in summary_data[:3]:  # Show first 3
                print(f"  {item['technical_name']} -> {item['display_name']}")
            
            if len(summary_data) > 3:
                print(f"  ... and {len(summary_data) - 3} more")
            print()
        
        # Example 4: Multi-language support
        print("📋 Example 4: Multi-language Label Resolution")
        print("-" * 45)
        
        # Get an entity for language testing
        entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=False)
        
        if entity and entity.label_id:
            print(f"Entity: {entity.name} (Label ID: {entity.label_id})")
            
            # Try different languages
            languages = ["en-US", "de-DE", "fr-FR", "es-ES"]
            
            for lang in languages:
                # Reset label text
                entity.label_text = None
                
                # Resolve in specific language
                await resolve_labels_generic(entity, cache, lang)
                
                print(f"  {lang}: {entity.label_text or 'Not available'}")
            print()
        
        # Example 5: Error handling and edge cases
        print("📋 Example 5: Error Handling")
        print("-" * 27)
        
        # Test with various edge cases
        test_cases = [
            None,  # None object
            [],    # Empty list
            [None, None],  # List with None objects
        ]
        
        print("Testing edge cases:")
        for i, test_case in enumerate(test_cases):
            try:
                result = await resolve_labels_generic(test_case, cache)
                print(f"  Case {i+1}: ✅ Handled gracefully")
            except Exception as e:
                print(f"  Case {i+1}: ❌ Error: {e}")
        
        # Example 6: Performance comparison
        print("\n📋 Example 6: Performance Benefits")
        print("-" * 33)
        
        entities = await cache.search_data_entities(pattern="Item")
        
        if entities and len(entities) > 5:
            print(f"Performance test with {len(entities)} entities")
            
            # Measure batch resolution time
            import time
            
            start_time = time.time()
            await resolve_labels_generic(entities, cache)
            batch_time = time.time() - start_time
            
            print(f"Batch resolution time: {batch_time:.3f} seconds")
            print(f"Average per entity: {batch_time/len(entities):.4f} seconds")
            print("✅ Efficient batch processing completed")
        
        print(f"\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(practical_label_resolution_example())