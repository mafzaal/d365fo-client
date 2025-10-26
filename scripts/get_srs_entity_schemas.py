"""Retrieve entity schemas for SRS document entities.

This script retrieves the full schema information for the data entities used
to query documents before downloading their SRS reports. The schema information
can be used to further enrich the documentation.

Entities queried:
1. CustInvoiceJourBiEntity - Customer Invoice Journal
2. SalesOrderConfirmationHeaderEntity - Sales Order Confirmation Headers
3. PurchPurchaseOrderConfirmationHeaderEntity - Purchase Order Confirmation Headers
"""

import asyncio
import json
import os
from pathlib import Path

from d365fo_client import FOClient, FOClientConfig


async def get_entity_schema(client: FOClient, entity_name: str) -> dict:
    """Get schema information for an entity.

    Args:
        client: FOClient instance
        entity_name: Name of the entity to retrieve schema for

    Returns:
        Dictionary containing entity schema information
    """
    print(f"\n{'='*80}")
    print(f"Retrieving schema for: {entity_name}")
    print(f"{'='*80}")

    try:
        # Get entity metadata
        entity_info = await client.get_public_entity_info(entity_name)

        if not entity_info:
            print(f"❌ Entity '{entity_name}' not found")
            return {"error": f"Entity '{entity_name}' not found"}

        # Extract relevant information
        schema = {
            "entity_name": entity_info.name,
            "public_entity_name": entity_info.public_entity_name,
            "public_collection_name": entity_info.public_collection_name,
            "label": entity_info.label_text,
            "entity_category": getattr(entity_info, "entity_category", "Unknown"),
            "data_service_enabled": getattr(entity_info, "data_service_enabled", False),
            "is_read_only": getattr(entity_info, "is_read_only", False),
            "properties": [],
            "key_properties": [],
            "navigation_properties": [],
        }

        # Get properties
        if hasattr(entity_info, "properties") and entity_info.properties:
            print(f"\n✓ Found {len(entity_info.properties)} properties")

            for prop in entity_info.properties:
                prop_info = {
                    "name": prop.name,
                    "data_type": prop.data_type,
                    "is_key": getattr(prop, "is_key", False),
                    "is_mandatory": getattr(prop, "is_mandatory", False),
                    "is_nullable": getattr(prop, "is_nullable", True),
                    "label": getattr(prop, "label", ""),
                }

                schema["properties"].append(prop_info)

                # Track key properties separately
                if prop_info["is_key"]:
                    schema["key_properties"].append(prop_info)

            # Sort properties by name
            schema["properties"].sort(key=lambda x: x["name"])

            print(f"  - Key properties: {len(schema['key_properties'])}")
            print(
                f"  - Mandatory properties: {len([p for p in schema['properties'] if p['is_mandatory']])}"
            )

        # Get navigation properties
        if (
            hasattr(entity_info, "navigation_properties")
            and entity_info.navigation_properties
        ):
            print(
                f"✓ Found {len(entity_info.navigation_properties)} navigation properties"
            )

            for nav_prop in entity_info.navigation_properties:
                nav_info = {
                    "name": nav_prop.name,
                    "partner": getattr(nav_prop, "partner", ""),
                    "relationship_type": getattr(nav_prop, "relationship_type", ""),
                }
                schema["navigation_properties"].append(nav_info)

        print(f"\n✓ Schema retrieved successfully")
        return schema

    except Exception as e:
        print(f"❌ Error retrieving schema: {e}")
        return {"error": str(e), "entity_name": entity_name}


async def main():
    """Main function to retrieve all entity schemas."""
    print("=" * 80)
    print("D365 F&O SRS Entity Schema Retrieval")
    print("=" * 80)

    # Configuration
    config = FOClientConfig(
        base_url=os.getenv(
            "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com/"
        ),
        verify_ssl=False,
    )

    # Entities to retrieve
    entities = [
        {
            "name": "CustInvoiceJourBiEntity",
            "collection": "CustInvoiceJourBiEntities",
            "label": "Customer Invoice Journal",
            "description": "Used for customer invoices, free text invoices, and debit/credit notes",
        },
        {
            "name": "SalesOrderConfirmationHeaderEntity",
            "collection": "SalesOrderConfirmationHeaders",
            "label": "Sales Order Confirmation Headers",
            "description": "Used for sales order confirmations",
        },
        {
            "name": "PurchPurchaseOrderConfirmationHeaderEntity",
            "collection": "PurchaseOrderConfirmationHeaders",
            "label": "Purchase Order Confirmation Headers",
            "description": "Used for purchase orders",
        },
    ]

    results = {}

    async with FOClient(config) as client:
        print(f"\n✓ Connected to D365 F&O: {config.base_url}")

        for entity_meta in entities:
            print(f"\n\n{'#'*80}")
            print(f"# {entity_meta['label']}")
            print(f"# Collection: {entity_meta['collection']}")
            print(f"# Description: {entity_meta['description']}")
            print(f"{'#'*80}")

            # Get schema
            schema = await get_entity_schema(client, entity_meta["name"])
            results[entity_meta["name"]] = {
                "metadata": entity_meta,
                "schema": schema,
            }

    # Save results
    output_dir = Path(__file__).parent.parent / "docs" / "schemas"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "srs_entity_schemas.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n\n{'='*80}")
    print(f"✓ Schemas saved to: {output_file}")
    print(f"{'='*80}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for entity_name, entity_data in results.items():
        schema = entity_data["schema"]
        if "error" in schema:
            print(f"\n❌ {entity_name}: {schema['error']}")
        else:
            print(f"\n✓ {entity_name}")
            print(f"  Collection: {schema.get('public_collection_name', 'N/A')}")
            print(f"  Label: {schema.get('label', 'N/A')}")
            print(f"  Properties: {len(schema.get('properties', []))}")
            print(f"  Key Properties: {len(schema.get('key_properties', []))}")
            print(
                f"  Navigation Properties: {len(schema.get('navigation_properties', []))}"
            )
            print(f"  OData Enabled: {schema.get('data_service_enabled', False)}")
            print(f"  Read Only: {schema.get('is_read_only', False)}")

            # Show key properties
            if schema.get("key_properties"):
                print(f"\n  Key Fields:")
                for key_prop in schema["key_properties"]:
                    print(f"    - {key_prop['name']} ({key_prop['data_type']})")

    # Generate markdown documentation
    print(f"\n\n{'='*80}")
    print("Generating Markdown Documentation...")
    print(f"{'='*80}")

    markdown_file = output_dir / "srs_entity_schemas.md"
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write("# D365 F&O SRS Document Entity Schemas\n\n")
        f.write(
            "This document contains detailed schema information for data entities used to query documents before downloading SRS reports.\n\n"
        )
        f.write("## Entities\n\n")

        for entity_name, entity_data in results.items():
            metadata = entity_data["metadata"]
            schema = entity_data["schema"]

            if "error" in schema:
                f.write(f"### {metadata['label']}\n\n")
                f.write(f"**Error**: {schema['error']}\n\n")
                continue

            f.write(f"### {metadata['label']}\n\n")
            f.write(f"**Entity Name**: `{schema['entity_name']}`\n\n")
            f.write(f"**Collection Name**: `{schema['public_collection_name']}`\n\n")
            f.write(f"**Description**: {metadata['description']}\n\n")
            f.write(f"**OData Enabled**: {schema['data_service_enabled']}\n\n")
            f.write(f"**Read Only**: {schema['is_read_only']}\n\n")

            # Key properties
            if schema.get("key_properties"):
                f.write("#### Key Properties\n\n")
                f.write("| Property | Data Type | Mandatory |\n")
                f.write("|----------|-----------|----------|\n")
                for prop in schema["key_properties"]:
                    f.write(
                        f"| {prop['name']} | {prop['data_type']} | {prop['is_mandatory']} |\n"
                    )
                f.write("\n")

            # All properties
            if schema.get("properties"):
                f.write("#### All Properties\n\n")
                f.write(
                    "| Property | Data Type | Key | Mandatory | Nullable | Label |\n"
                )
                f.write(
                    "|----------|-----------|-----|-----------|----------|-------|\n"
                )
                for prop in schema["properties"][:20]:  # First 20 properties
                    label = prop.get("label", "")[:30]  # Truncate long labels
                    f.write(
                        f"| {prop['name']} | {prop['data_type']} | {prop['is_key']} | {prop['is_mandatory']} | {prop['is_nullable']} | {label} |\n"
                    )

                if len(schema["properties"]) > 20:
                    f.write(
                        f"\n*Showing first 20 of {len(schema['properties'])} properties. See JSON file for complete list.*\n\n"
                    )
                else:
                    f.write("\n")

            # Navigation properties
            if schema.get("navigation_properties"):
                f.write("#### Navigation Properties\n\n")
                f.write("| Property | Partner | Relationship Type |\n")
                f.write("|----------|---------|------------------|\n")
                for nav_prop in schema["navigation_properties"]:
                    f.write(
                        f"| {nav_prop['name']} | {nav_prop['partner']} | {nav_prop['relationship_type']} |\n"
                    )
                f.write("\n")

            # Example query
            f.write("#### Example Query\n\n")
            f.write("```python\n")
            f.write("# Query for documents in USMF company\n")
            f.write("result = await client.get_entities(\n")
            f.write(f'    "{schema["public_collection_name"]}",\n')
            f.write("    options=QueryOptions(\n")
            f.write("        filter=\"DataAreaId eq 'USMF'\",\n")

            # Select key fields
            key_fields = [prop["name"] for prop in schema.get("key_properties", [])]
            if key_fields:
                f.write(f"        select={key_fields[:5]},\n")

            f.write("        top=10\n")
            f.write("    )\n")
            f.write(")\n")
            f.write("```\n\n")

            f.write("---\n\n")

    print(f"✓ Markdown documentation saved to: {markdown_file}")

    print(f"\n\n{'='*80}")
    print("✓ All schemas retrieved and documented successfully!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
