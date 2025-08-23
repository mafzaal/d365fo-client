#!/usr/bin/env python3
"""Test script to verify public entities parsing with constraints."""

import asyncio
import logging

from d365fo_client import FOClient, FOClientConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_public_entities_parsing():
    """Test that public entities are parsed correctly with navigation properties and constraints."""

    # Initialize client
    config = FOClientConfig(
        base_url="https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        use_default_credentials=True,
        enable_metadata_cache=True,
        enable_fts_search=True,
    )

    async with FOClient(config) as client:
        # Test one of the entities from your sample: AbsenceCode
        entity = await client.get_public_entity_info(
            "AbsenceCode", resolve_labels=False
        )

        if entity:
            print(f"\n🔍 Testing entity: {entity.name}")
            print(f"   Entity Set Name: {entity.entity_set_name}")
            print(f"   Properties Count: {len(entity.properties)}")
            print(
                f"   Navigation Properties Count: {len(entity.navigation_properties)}"
            )
            print(f"   Property Groups Count: {len(entity.property_groups)}")
            print(f"   Actions Count: {len(entity.actions)}")

            # Check navigation properties
            if entity.navigation_properties:
                print(f"\n📋 Navigation Properties:")
                for nav_prop in entity.navigation_properties:
                    print(
                        f"   - {nav_prop.name} -> {nav_prop.related_entity} ({nav_prop.cardinality})"
                    )
                    if nav_prop.constraints:
                        print(f"     Constraints:")
                        for constraint in nav_prop.constraints:
                            print(
                                f"       {constraint.constraint_type}: {constraint.property} -> {constraint.referenced_property}"
                            )

            # Check property groups
            if entity.property_groups:
                print(f"\n📁 Property Groups:")
                for group in entity.property_groups:
                    print(f"   - {group.name}: {group.properties}")

            # Check some key properties
            key_props = [prop for prop in entity.properties if prop.is_key]
            print(f"\n🔑 Key Properties: {[p.name for p in key_props]}")

        else:
            print("❌ Entity not found")

        # Test another entity: AbsenceCodeGroup
        entity2 = await client.get_public_entity_info(
            "AbsenceCodeGroup", resolve_labels=False
        )

        if entity2:
            print(f"\n🔍 Testing entity: {entity2.name}")
            print(
                f"   Navigation Properties Count: {len(entity2.navigation_properties)}"
            )

            # Check navigation properties
            if entity2.navigation_properties:
                print(f"\n📋 Navigation Properties:")
                for nav_prop in entity2.navigation_properties:
                    print(
                        f"   - {nav_prop.name} -> {nav_prop.related_entity} ({nav_prop.cardinality})"
                    )
                    if nav_prop.constraints:
                        print(f"     Constraints:")
                        for constraint in nav_prop.constraints:
                            print(
                                f"       {constraint.constraint_type}: {constraint.property} -> {constraint.referenced_property}"
                            )


if __name__ == "__main__":
    asyncio.run(test_public_entities_parsing())
