"""Examples of using DMF operations with d365fo-client."""

import asyncio
import os

from d365fo_client import FOClient, FOClientConfig


async def export_example():
    """Example: Export data to package asynchronously."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        use_default_credentials=True,
    )

    async with FOClient(config) as client:
        print("=== Export Example ===")

        # Export data asynchronously
        execution_id = await client.export_to_package_async(
            definition_group_id="CustomerMasterData",
            package_name="Customers_2025-10-05",
            legal_entity_id="USMF",
        )

        print(f"Export started: {execution_id}")

        # Check status
        status = await client.get_execution_summary_status(execution_id)
        print(f"Status: {status}")

        # When complete, get download URL
        # url = await client.get_exported_package_url(execution_id)
        # print(f"Download: {url}")


async def import_example():
    """Example: Import data from package."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        use_default_credentials=True,
    )

    async with FOClient(config) as client:
        print("\n=== Import Example ===")

        # First, get Azure write URL to upload package
        file_name = "import_package_2025-10-05.zip"
        write_url = await client.get_azure_write_url(file_name)
        print(f"Azure write URL: {write_url}")

        # Upload package to Azure Blob Storage (using aiohttp or requests)
        # await upload_package_to_azure(write_url, local_package_path)

        # Import data from uploaded package
        execution_id = await client.import_from_package(
            package_url=write_url,  # or the blob URL after upload
            definition_group_id="CustomerMasterData",
            execute=True,
            overwrite=False,
            legal_entity_id="USMF",
        )

        print(f"Import started: {execution_id}")

        # Monitor status
        status = await client.get_execution_summary_status(execution_id)
        print(f"Status: {status}")


async def monitoring_example():
    """Example: Monitor execution and handle errors."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        use_default_credentials=True,
    )

    async with FOClient(config) as client:
        print("\n=== Monitoring Example ===")

        execution_id = "YOUR_EXECUTION_ID_HERE"

        # Get overall status
        summary_status = await client.get_execution_summary_status(execution_id)
        print(f"Execution summary: {summary_status}")

        # Get per-entity status
        entity_statuses = await client.get_entity_execution_summary_status_list(
            execution_id
        )
        print(f"Entity statuses: {entity_statuses}")

        # Get errors if any
        errors = await client.get_execution_errors(execution_id)
        if errors:
            print(f"Errors found: {errors}")

            # Get error file URLs for specific entity
            error_keys_url = await client.get_import_target_error_keys_file_url(
                execution_id, "Customers"
            )
            print(f"Error keys file: {error_keys_url}")


async def initialization_example():
    """Example: Initialize DMF."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        use_default_credentials=True,
    )

    async with FOClient(config) as client:
        print("\n=== Initialization Example ===")

        # Initialize DMF asynchronously
        await client.initialize_data_management_async()
        print("DMF initialized successfully")


async def utility_example():
    """Example: Utility operations."""
    config = FOClientConfig(
        base_url=os.getenv("D365FO_BASE_URL"),
        use_default_credentials=True,
    )

    async with FOClient(config) as client:
        print("\n=== Utility Example ===")

        # Get recommended entity sequence
        entity_list = "Customers,SalesOrders,SalesOrderLines"
        sequence = await client.get_entity_sequence(entity_list)
        print(f"Recommended sequence: {sequence}")

        # Reset version token for delta exports
        result = await client.reset_version_token(
            definition_group_id="CustomerMasterData",
            entity_name="Customers",
            source_name="D365FO",
        )
        print(f"Version token reset: {result}")


async def main():
    """Run all examples."""
    print("DMF Operations Examples\n")
    print("Note: Set D365FO_BASE_URL environment variable before running")
    print("=" * 60)

    # Uncomment the examples you want to run:

    # await export_example()
    # await import_example()
    # await monitoring_example()
    # await initialization_example()
    # await utility_example()

    print("\n" + "=" * 60)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
