"""
Demonstration of automatic cross-company query parameter functionality.

This example shows how the QueryBuilder automatically adds cross-company=true
when filtering by dataAreaId, enabling queries across multiple legal entities
in D365 Finance & Operations.
"""

from d365fo_client.models import QueryOptions
from d365fo_client.query import QueryBuilder


def main():
    print("=" * 70)
    print("Cross-Company Query Parameter Demo")
    print("=" * 70)

    # Example 1: Simple dataAreaId filter
    print("\n1. Simple dataAreaId filter:")
    print("   Input: filter=\"dataAreaId eq 'USMF'\"")
    options = QueryOptions(filter="dataAreaId eq 'USMF'")
    query_string = QueryBuilder.build_query_string(options)
    print(f"   Output: {query_string}")
    print("   ✓ Automatically added 'cross-company=true' for cross-company access")

    # Example 2: Complex filter with dataAreaId
    print("\n2. Complex filter with dataAreaId:")
    print("   Input: filter=\"dataAreaId eq 'USMF' and CustomerAccount eq 'US-001'\"")
    options = QueryOptions(
        filter="dataAreaId eq 'USMF' and CustomerAccount eq 'US-001'",
        select=["CustomerAccount", "Name", "Phone"],
        top=10,
    )
    params = QueryBuilder.build_query_params(options)
    print("   Output parameters:")
    for key, value in params.items():
        print(f"     {key}: {value}")
    print("   ✓ Added 'cross-company=true' while preserving other parameters")

    # Example 3: Multiple dataAreaId values with OR
    print("\n3. Multiple legal entities (OR condition):")
    print("   Input: filter=\"dataAreaId eq 'USMF' or dataAreaId eq 'USSI'\"")
    options = QueryOptions(filter="dataAreaId eq 'USMF' or dataAreaId eq 'USSI'")
    query_string = QueryBuilder.build_query_string(options)
    print(f"   Output: {query_string}")
    print("   ✓ Enables querying data from multiple legal entities")

    # Example 4: Case-insensitive detection
    print("\n4. Case-insensitive detection:")
    print("   Input: filter=\"DATAAREAID eq 'USMF'\" (uppercase)")
    options = QueryOptions(filter="DATAAREAID eq 'USMF'")
    params = QueryBuilder.build_query_params(options)
    print(f"   Output: cross-company={params.get('cross-company', 'not set')}")
    print("   ✓ Works regardless of dataAreaId field case")

    # Example 5: No dataAreaId - no cross-company parameter
    print("\n5. Query without dataAreaId:")
    print("   Input: filter=\"CustomerAccount eq 'US-001'\"")
    options = QueryOptions(filter="CustomerAccount eq 'US-001'")
    query_string = QueryBuilder.build_query_string(options)
    print(f"   Output: {query_string}")
    print("   ✓ No 'cross-company' parameter added (not needed)")

    # Example 6: Practical use case
    print("\n6. Practical use case - Get invoices from specific companies:")
    print("   Scenario: Query sales invoices from USMF and USSI legal entities")
    options = QueryOptions(
        filter="(dataAreaId eq 'USMF' or dataAreaId eq 'USSI') and InvoiceDate ge 2024-01-01",
        select=["InvoiceId", "CustomerAccount", "InvoiceAmount", "dataAreaId"],
        orderby=["InvoiceDate desc"],
        top=50,
    )
    query_string = QueryBuilder.build_query_string(options)
    print(f"   Query: /data/SalesInvoices{query_string}")
    print("   ✓ Ready to query invoices across multiple legal entities")

    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
