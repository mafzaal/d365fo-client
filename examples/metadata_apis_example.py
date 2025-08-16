#!/usr/bin/env python3
"""
Example: Using the new Metadata APIs

This example demonstrates how to use the new metadata APIs to:
1. Discover data entities and their capabilities
2. Get detailed entity schemas with properties
3. Explore enumerations and their values
4. Filter and search metadata efficiently
"""

import asyncio
import os
from d365fo_client import FOClient, FOClientConfig, QueryOptions

async def metadata_apis_example():
    """Comprehensive example of metadata APIs usage"""
    
    # Configuration
    base_url = os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com')
    config = FOClientConfig(base_url=base_url)
    
    async with FOClient(config) as client:
        print("🚀 D365 F&O Metadata APIs Example")
        print("=" * 50)
        
        # 1. Discover Available Entities
        print("\n1️⃣ Discovering Entities")
        print("-" * 25)
        
        # Find customer-related data entities
        print("Finding customer-related data entities...")
        customer_data_entities = await client.search_data_entities("customer")
        print(f"   Found {len(customer_data_entities)} entities")
        
        # Show different entity categories
        categories = {}
        for entity in customer_data_entities[:20]:  # First 20 for brevity
            cat = entity.entity_category or "Unknown"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(entity.name)
        
        print("   Categories found:")
        for cat, entities in categories.items():
            print(f"     {cat}: {len(entities)} entities")
            for entity_name in entities[:3]:  # Show first 3
                print(f"       - {entity_name}")
            if len(entities) > 3:
                print(f"       ... and {len(entities) - 3} more")
        
        # 2. Entity Schema Discovery
        print("\n2️⃣ Entity Schema Discovery")
        print("-" * 28)
        
        # Get detailed schema for Customer entity
        print("Getting Customer entity schema...")
        customer_entity = await client.get_public_entity_info("Customer")
        
        if customer_entity:
            print(f"   Entity: {customer_entity.name}")
            print(f"   Label: {customer_entity.label_text}")
            print(f"   Entity Set: {customer_entity.entity_set_name}")
            print(f"   Read-only: {customer_entity.is_read_only}")
            print(f"   Total Properties: {len(customer_entity.properties)}")
            
            # Analyze properties
            key_props = [p for p in customer_entity.properties if p.is_key]
            mandatory_props = [p for p in customer_entity.properties if p.is_mandatory]
            readonly_props = [p for p in customer_entity.properties if not p.allow_edit]
            
            print(f"   Key Properties: {len(key_props)}")
            for prop in key_props:
                print(f"     - {prop.name} ({prop.type_name})")
            
            print(f"   Mandatory Properties: {len(mandatory_props)}")
            for prop in mandatory_props[:5]:  # Show first 5
                label = prop.label_text or prop.name
                print(f"     - {prop.name}: '{label}' ({prop.type_name})")
            
            print(f"   Read-only Properties: {len(readonly_props)}")
            
            # Show data types distribution
            type_counts = {}
            for prop in customer_entity.properties:
                data_type = prop.data_type
                type_counts[data_type] = type_counts.get(data_type, 0) + 1
            
            print("   Data Types Distribution:")
            for dtype, count in sorted(type_counts.items()):
                print(f"     {dtype}: {count}")
        
        # 3. Enumeration Discovery
        print("\n3️⃣ Enumeration Discovery")
        print("-" * 25)
        
        # Find payment-related enumerations
        print("Finding payment-related enumerations...")
        payment_enums = await client.search_public_enumerations("payment")
        print(f"   Found {len(payment_enums)} payment-related enumerations:")
        for enum_info in payment_enums[:5]:
            print(f"     - {enum_info.name}")
        
        # Get detailed enumeration info
        if payment_enums:
            enum_name = payment_enums[0].name
            print(f"\n   Getting details for '{enum_name}' enumeration...")
            enum_details = await client.get_public_enumeration_info(enum_name)
            
            if enum_details:
                print(f"     Name: {enum_details.name}")
                print(f"     Label: {enum_details.label_text}")
                print(f"     Members: {len(enum_details.members)}")
                
                if enum_details.members:
                    print("     Values:")
                    for member in enum_details.members:
                        label = member.label_text or member.name
                        print(f"       {member.value}: {member.name} - '{label}'")
        
        # 4. Advanced Filtering and Analytics
        print("\n4️⃣ Advanced Filtering & Analytics")
        print("-" * 35)
        
        # Analyze data entities by category
        print("Analyzing data entities by category...")
        
        categories_to_check = ["Master", "Transaction", "Reference", "Document"]
        category_stats = {}
        
        for category in categories_to_check:
            entities = await client.search_data_entities("", entity_category=category)
            readonly_count = len([e for e in entities if e.is_read_only])
            data_mgmt_count = len([e for e in entities if e.data_management_enabled])
            
            category_stats[category] = {
                'total': len(entities),
                'readonly': readonly_count,
                'data_management': data_mgmt_count
            }
        
        print("   Category Statistics:")
        for category, stats in category_stats.items():
            print(f"     {category}:")
            print(f"       Total: {stats['total']}")
            print(f"       Read-only: {stats['readonly']}")
            print(f"       Data Management Enabled: {stats['data_management']}")
        
        # Find largest entities by property count
        print("\n   Finding entities with most properties...")
        entity_names = ["Customer", "Vendor", "Item", "Worker", "LedgerJournalLine"]
        entity_sizes = []
        
        for entity_name in entity_names:
            try:
                entity = await client.get_public_entity_info(entity_name)
                if entity:
                    entity_sizes.append((entity_name, len(entity.properties)))
            except:
                continue
        
        entity_sizes.sort(key=lambda x: x[1], reverse=True)
        
        print("   Largest entities by property count:")
        for name, count in entity_sizes:
            print(f"     {name}: {count} properties")
        
        # 5. Integration Patterns
        print("\n5️⃣ Integration Patterns")
        print("-" * 23)
        
        # Find integration-ready entities
        print("Finding integration-ready entities...")
        
        # Get entities that are not read-only and have data management enabled
        integration_entities = await client.search_data_entities(
            "",
            data_service_enabled=True,
            data_management_enabled=True,
            is_read_only=False
        )
        
        print(f"   Found {len(integration_entities)} entities suitable for integration")
        
        # Group by category
        integration_by_category = {}
        for entity in integration_entities:
            cat = entity.entity_category or "Unknown"
            if cat not in integration_by_category:
                integration_by_category[cat] = []
            integration_by_category[cat].append(entity)
        
        print("   Integration entities by category:")
        for category, entities in integration_by_category.items():
            print(f"     {category}: {len(entities)} entities")
        
        # 6. Configuration Discovery
        print("\n6️⃣ Configuration Discovery")
        print("-" * 26)
        
        # Find configuration entities
        config_entities = await client.search_data_entities("", entity_category="Configuration")
        print(f"   Found {len(config_entities)} configuration entities")
        
        # Find setup/parameter entities
        setup_entities = await client.search_data_entities("setup")
        param_entities = await client.search_data_entities("parameters")
        
        print(f"   Setup entities: {len(setup_entities)}")
        print(f"   Parameter entities: {len(param_entities)}")
        
        # Show some examples
        print("   Configuration entity examples:")
        for entity in config_entities[:5]:
            label = entity.label_text or entity.name
            print(f"     - {entity.name}: '{label}'")
        
        print("\n✅ Metadata APIs exploration completed!")
        print("\n💡 Next steps:")
        print("   - Use entity schemas to build integration mappings")
        print("   - Use enumerations to validate field values")
        print("   - Filter entities based on your integration needs")
        print("   - Explore navigation properties for related data")

if __name__ == "__main__":
    asyncio.run(metadata_apis_example())