#!/usr/bin/env python3
"""
Label Resolution Utility Demo

This example demonstrates how to use the generic label resolution utility function
that can set label text based on label ID for any object containing label_id and
label_text properties. The function works on both single objects and lists.
"""

import asyncio
import os
from pathlib import Path

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.metadata_cache import MetadataCache, resolve_labels_generic


async def main():
    """Demonstrate the generic label resolution utility"""

    print("🏷️  Label Resolution Utility Demo")
    print("=" * 50)

    # Configuration
    base_url = os.getenv(
        "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
    )
    cache_dir = Path("example_cache")

    # Configure client with default credentials and label cache
    config = FOClientConfig(
        base_url=base_url,
        use_default_credentials=True,
        use_label_cache=True,
        cache_dir=cache_dir,
    )

    client = FOClient(config=config)

    try:
        # Initialize metadata cache
        cache = MetadataCache(base_url, cache_dir)
        await cache.initialize()

        print(f"✅ Connected to: {base_url}")
        print(f"💾 Cache directory: {cache_dir}")
        print()

        # Example 1: Resolve labels for a single entity
        print("📝 Example 1: Single Entity Label Resolution")
        print("-" * 45)

        # Get a public entity (without labels resolved initially)
        entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=False)
        if entity:
            print(f"Entity: {entity.name}")
            print(f"Label ID: {entity.label_id}")
            print(f"Label Text (before): {entity.label_text}")
            print(
                f"Properties with labels: {len([p for p in entity.properties if p.label_id])}"
            )

            # Use the generic utility to resolve labels
            await resolve_labels_generic(entity, cache)

            print(f"Label Text (after): {entity.label_text}")
            print(
                f"First property with label: {entity.properties[0].name} -> {entity.properties[0].label_text}"
            )
            print()

        # Example 2: Resolve labels for a list of entities
        print("📝 Example 2: Multiple Entities Label Resolution")
        print("-" * 48)

        # Get multiple data entities (without labels resolved)
        entities = await cache.search_data_entities(
            pattern="Customer", data_service_enabled=True
        )
        if entities:
            print(f"Found {len(entities)} customer-related entities")

            # Show before resolution
            print("\nBefore label resolution:")
            for entity in entities[:3]:  # Show first 3
                print(f"  {entity.name}: {entity.label_id} -> {entity.label_text}")

            # Use the generic utility to resolve labels for the entire list
            await resolve_labels_generic(entities, cache)

            # Show after resolution
            print("\nAfter label resolution:")
            for entity in entities[:3]:  # Show first 3
                print(f"  {entity.name}: {entity.label_id} -> {entity.label_text}")
            print()

        # Example 3: Resolve labels for enumeration with members
        print("📝 Example 3: Enumeration with Members Label Resolution")
        print("-" * 54)

        # Get an enumeration (without labels resolved)
        enums = await cache.search_public_enumerations(pattern="Currency")
        if enums:
            enum_info = await cache.get_public_enumeration_info(
                enums[0].name, resolve_labels=False
            )
            if enum_info:
                print(f"Enumeration: {enum_info.name}")
                print(f"Label ID: {enum_info.label_id}")
                print(f"Label Text (before): {enum_info.label_text}")
                print(
                    f"Members with labels: {len([m for m in enum_info.members if m.label_id])}"
                )

                # Use the generic utility (works on complex nested objects too)
                await resolve_labels_generic(enum_info, cache)

                print(f"Label Text (after): {enum_info.label_text}")
                if enum_info.members:
                    print(
                        f"First member: {enum_info.members[0].name} -> {enum_info.members[0].label_text}"
                    )
                print()

        # Example 4: Different language resolution
        print("📝 Example 4: Multi-language Label Resolution")
        print("-" * 44)

        # Get an entity and resolve labels in different languages
        entity = await cache.get_public_entity_info("CustomersV3", resolve_labels=False)
        if entity:
            print(f"Entity: {entity.name}")

            # Resolve in English (default)
            await resolve_labels_generic(entity, cache, "en-US")
            print(f"English: {entity.label_text}")

            # Reset label text and try another language (if available)
            entity.label_text = None
            await resolve_labels_generic(entity, cache, "de-DE")
            print(f"German: {entity.label_text or 'Not available'}")
            print()

        # Example 5: Custom object with label properties
        print("📝 Example 5: Custom Object Label Resolution")
        print("-" * 43)

        # Create a simple custom class that has label_id and label_text
        class CustomObject:
            def __init__(self, name: str, label_id: str = None):
                self.name = name
                self.label_id = label_id
                self.label_text = None

        # Create some custom objects with known label IDs
        custom_objects = []
        if entity and entity.properties:
            # Use label IDs from the entity properties
            for i, prop in enumerate(entity.properties[:3]):
                if prop.label_id:
                    custom_obj = CustomObject(f"custom_obj_{i}", prop.label_id)
                    custom_objects.append(custom_obj)

        if custom_objects:
            print(f"Created {len(custom_objects)} custom objects with label IDs")

            # Show before resolution
            print("\nBefore resolution:")
            for obj in custom_objects:
                print(f"  {obj.name}: {obj.label_id} -> {obj.label_text}")

            # Resolve labels using the generic utility
            await resolve_labels_generic(custom_objects, cache)

            # Show after resolution
            print("\nAfter resolution:")
            for obj in custom_objects:
                print(f"  {obj.name}: {obj.label_id} -> {obj.label_text}")
            print()

        # Display cache statistics
        print("📊 Cache Statistics")
        print("-" * 18)
        stats = await cache.get_statistics()
        print(f"Total labels cached: {stats.get('total_labels', 0)}")
        print(f"Active labels: {stats.get('active_labels', 0)}")
        print(f"Languages: {list(stats.get('languages', {}).keys())}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
