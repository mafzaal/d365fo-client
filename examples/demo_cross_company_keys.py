"""
Demonstration of automatic cross-company parameter for composite keys.

This example shows how the QueryBuilder automatically adds cross-company=true
when dataAreaId is part of the entity key (for get_entity, update_entity,
delete_entity, and call_action operations).

This complements the existing cross-company support for filter queries.
"""

from d365fo_client.query import QueryBuilder


def main():
    print("=" * 80)
    print("Cross-Company Parameter for Composite Keys Demo")
    print("=" * 80)

    base_url = "https://example.dynamics.com"

    # Example 1: Simple composite key with dataAreaId
    print("\n1. GET entity with composite key containing dataAreaId:")
    print("   Operation: Get a single customer record")
    key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
    url = QueryBuilder.build_entity_url(base_url, "CustomersV3", key)
    print(f"   Key: {key}")
    print(f"   URL: {url}")
    print("   ✓ Automatically added '?cross-company=true' for cross-company access")

    # Example 2: Composite key without dataAreaId (no cross-company)
    print("\n2. GET entity with composite key WITHOUT dataAreaId:")
    print("   Operation: Get a record that doesn't use dataAreaId")
    key = {"CustomerAccount": "CUST001", "InvoiceId": "INV001"}
    url = QueryBuilder.build_entity_url(base_url, "SomeEntity", key)
    print(f"   Key: {key}")
    print(f"   URL: {url}")
    print("   ✓ No 'cross-company' parameter (not needed)")

    # Example 3: Simple string key (no cross-company)
    print("\n3. GET entity with simple string key:")
    print("   Operation: Get a record with single-field key")
    key = "CUST001"
    url = QueryBuilder.build_entity_url(base_url, "CustomersV3", key)
    print(f"   Key: {key}")
    print(f"   URL: {url}")
    print("   ✓ No 'cross-company' parameter (simple key, not composite)")

    # Example 4: Entity-bound action with dataAreaId in key
    print("\n4. Call action on specific entity with dataAreaId:")
    print("   Operation: Execute action on a specific customer")
    key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
    url = QueryBuilder.build_action_url(
        base_url, "UpdateCreditLimit", "CustomersV3", key
    )
    print("   Action: UpdateCreditLimit")
    print(f"   Entity Key: {key}")
    print(f"   URL: {url}")
    print("   ✓ Automatically added '?cross-company=true' for action")

    # Example 5: Entity set-bound action (no cross-company)
    print("\n5. Call action on entity set (not bound to specific entity):")
    print("   Operation: Execute action on entire entity set")
    url = QueryBuilder.build_action_url(base_url, "GetStatistics", "CustomersV3")
    print("   Action: GetStatistics")
    print(f"   URL: {url}")
    print("   ✓ No 'cross-company' parameter (entity set action)")

    # Example 6: Multiple key fields with dataAreaId
    print("\n6. Complex composite key with multiple fields:")
    print("   Operation: Get a specific invoice line")
    key = {
        "dataAreaId": "USMF",
        "InvoiceId": "INV-2024-001",
        "LineNumber": 1,
        "ItemId": "ITEM-001",
    }
    url = QueryBuilder.build_entity_url(base_url, "SalesInvoiceLines", key)
    print(f"   Key: {key}")
    print(f"   URL: {url}")
    print("   ✓ Works with any number of key fields")

    # Example 7: Case-insensitive dataAreaId detection
    print("\n7. Case-insensitive dataAreaId detection:")
    print("   Different case variations all work:")

    test_cases = [
        {"dataAreaId": "USMF", "Account": "A001"},
        {"DataAreaId": "USMF", "Account": "A001"},
        {"DATAAREAID": "USMF", "Account": "A001"},
        {"dataareaId": "USMF", "Account": "A001"},
    ]

    for i, key in enumerate(test_cases, 1):
        url = QueryBuilder.build_entity_url(base_url, "Entity", key)
        has_cross_company = "cross-company=true" in url
        print(
            f"   {i}. Key field: {list(key.keys())[0]} → cross-company: {has_cross_company}"
        )

    # Example 8: Real-world CRUD scenario
    print("\n8. Real-world CRUD operations scenario:")
    print("   Scenario: Managing customer data across legal entities")
    print()

    key = {"dataAreaId": "USMF", "CustomerAccount": "US-001"}

    # GET operation
    get_url = QueryBuilder.build_entity_url(base_url, "CustomersV3", key)
    print(f"   GET (retrieve):   {get_url}")

    # UPDATE operation (uses same URL building)
    update_url = QueryBuilder.build_entity_url(base_url, "CustomersV3", key)
    print(f"   PATCH (update):   {update_url}")

    # DELETE operation (uses same URL building)
    delete_url = QueryBuilder.build_entity_url(base_url, "CustomersV3", key)
    print(f"   DELETE (remove):  {delete_url}")

    print()
    print("   ✓ All CRUD operations automatically include cross-company parameter")

    # Example 9: Explicit control when needed
    print("\n9. Explicit cross-company control (advanced):")
    print("   You can explicitly enable cross-company even without dataAreaId:")
    key = {"CustomerAccount": "CUST001"}
    url = QueryBuilder.build_entity_url(
        base_url, "CustomersV3", key, add_cross_company=True
    )
    print(f"   Key: {key}")
    print(f"   URL: {url}")
    print("   ✓ Explicit add_cross_company=True parameter")

    # Example 10: Comparison with filter-based cross-company
    print("\n10. Comparison: Keys vs Filters")
    print("    Both scenarios now support cross-company:")
    print()

    # Filter-based (existing functionality)
    from d365fo_client.models import QueryOptions

    options = QueryOptions(filter="dataAreaId eq 'USMF'")
    query_string = QueryBuilder.build_query_string(options)
    print("    Collection query with filter:")
    print(f"    /data/CustomersV3{query_string}")
    print("    → Adds cross-company via filter detection")
    print()

    # Key-based (new functionality)
    key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
    url = QueryBuilder.build_entity_url(base_url, "CustomersV3", key)
    print("    Single entity with composite key:")
    print(f"    {url}")
    print("    → Adds cross-company via key detection")

    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Cross-company is auto-added when dataAreaId is in composite keys")
    print("  • Works for GET, UPDATE, DELETE, and entity-bound ACTIONS")
    print("  • Detection is case-insensitive (dataAreaId, DataAreaId, DATAAREAID)")
    print("  • No changes needed to existing code - it's automatic!")
    print("  • Complements existing filter-based cross-company support")
    print("=" * 80)


if __name__ == "__main__":
    main()
