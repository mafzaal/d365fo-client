
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from d365fo_client import FOClient, FOClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def inspect_response(client: FOClient, action: str, **kwargs):
    """Call a DMF action and print the raw response."""
    logger.info(f"--- Calling {action} ---")
    logger.info(f"Parameters: {json.dumps(kwargs, indent=2)}")
    
    try:
        # We access the dmf_ops directly to get the raw response if possible,
        # but the current implementation returns parsed results.
        # So we will use the public methods and print the result.
        # To get truly raw responses, we might need to hook into the session or logger,
        # but seeing the parsed return value is a good start.
        
        method = getattr(client.dmf_ops, action)
        result = await method(**kwargs)
        
        print(f"\nResponse from {action}:")
        if isinstance(result, (dict, list)):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result)
        print("-" * 50 + "\n")
        return result
        
    except Exception as e:
        logger.error(f"Error calling {action}: {e}")
        return None

async def main():
    base_url = os.environ.get("D365FO_BASE_URL")
    if not base_url:
        logger.error("D365FO_BASE_URL environment variable not set.")
        return

    config = FOClientConfig(base_url=base_url)
    client = FOClient(config)

    try:
        logger.info("Initializing Data Management...")
        await inspect_response(client, "initialize_data_management")

        # 1. Export to Package (Preview)
        # We use a preview export as it's usually faster and less resource intensive
        logger.info("Testing Export...")
        execution_id = await inspect_response(
            client, 
            "export_to_package_preview",
            definition_group_id="CustomersExport", # Replace with a valid group if known
            package_name="DebugExport",
            # entity_list="CustTable", # Not supported in preview
            export_preview_count=10
        )

        if execution_id:
            # 2. Get Execution Summary Status
            logger.info("Testing Status...")
            status = await inspect_response(
                client,
                "get_execution_summary_status",
                execution_id=execution_id
            )
            
            # 3. Get Execution Errors (if any)
            logger.info("Testing Errors...")
            await inspect_response(
                client,
                "get_execution_errors",
                execution_id=execution_id
            )
            
            # 4. Get Package URL (if succeeded)
            if status and status.get("Status") == "Succeeded":
                logger.info("Testing Get URL...")
                await inspect_response(
                    client,
                    "get_exported_package_url",
                    execution_id=execution_id
                )

        # 5. Test a utility method
        logger.info("Testing Azure Write URL...")
        await inspect_response(
            client,
            "get_azure_write_url",
            unique_file_name=f"debug_upload_{int(datetime.now().timestamp())}.zip"
        )

        # 5. Test Entity Sequence (Utility)
        logger.info("Testing Entity Sequence...")
        await inspect_response(
            client,
            "get_entity_sequence",
            list_of_data_entities="CustTable,VendTable"
        )

        # 6. Test Status with dummy ID (to check response format)
        logger.info("Testing Status (Dummy ID)...")
        await inspect_response(
            client,
            "get_execution_summary_status",
            execution_id="DUMMY-EXEC-ID"
        )

        # 7. Test Errors with dummy ID
        logger.info("Testing Errors (Dummy ID)...")
        await inspect_response(
            client,
            "get_execution_errors",
            execution_id="DUMMY-EXEC-ID"
        )

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
