import asyncio
import logging
import os

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.models import DMFExecutionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    base_url = os.environ.get("D365FO_BASE_URL")
    if not base_url:
        logger.error("Please set D365FO_BASE_URL environment variable")
        return

    config = FOClientConfig(base_url=base_url)
    client = FOClient(config)

    try:
        logger.info("Initializing Data Management...")
        await client.initialize_data_management_async()

        # Export Example
        logger.info("Starting Export...")
        execution_id = await client.export_to_package_async(
            definition_group_id="CustomersExport",
            package_name="Customers_Backup",
            entity_list="CustTable",
        )
        logger.info(f"Export started with Execution ID: {execution_id}")

        # Monitor
        while True:
            status = await client.get_execution_summary_status(execution_id)
            status_enum = status.get("Status")
            logger.info(f"Status: {status_enum}")

            if status_enum in ["Succeeded", "PartiallySucceeded", "Failed", "Canceled"]:
                break

            await asyncio.sleep(5)

        if status_enum == "Succeeded":
            url = await client.get_exported_package_url(execution_id)
            logger.info(f"Download URL: {url}")
        else:
            errors = await client.get_execution_errors(execution_id)
            logger.error(f"Export failed: {errors}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
