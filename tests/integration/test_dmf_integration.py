import asyncio
import os

import pytest

from d365fo_client import FOClient, FOClientConfig


# Skip if no connection string
@pytest.mark.skipif(
    not os.environ.get("D365FO_BASE_URL"), reason="D365FO_BASE_URL not set"
)
@pytest.mark.asyncio
async def test_dmf_export_flow():
    # Setup
    config = FOClientConfig(
        base_url=os.environ["D365FO_BASE_URL"],
        credential_source=None,  # Uses default creds
    )
    client = FOClient(config)

    try:
        # 1. Initialize
        await client.initialize_data_management_async()

        # 2. Export (Preview)
        execution_id = await client.export_to_package_preview_async(
            definition_group_id="TestExportGroup",
            package_name="TestExportPackage",
            entity_list="CustTable",
            export_preview_count=10,
        )
        assert execution_id

        # 3. Monitor Status
        max_retries = 30
        for _ in range(max_retries):
            status = await client.get_execution_summary_status(execution_id)
            if status["Status"] in ["Succeeded", "PartiallySucceeded", "Failed"]:
                break
            await asyncio.sleep(2)

        assert status["Status"] in ["Succeeded", "PartiallySucceeded"]

        # 4. Get URL
        url = await client.get_exported_package_url(execution_id)
        assert url.startswith("http")

    finally:
        await client.close()


@pytest.mark.skipif(
    not os.environ.get("D365FO_BASE_URL"), reason="D365FO_BASE_URL not set"
)
@pytest.mark.asyncio
async def test_dmf_status_monitoring():
    config = FOClientConfig(base_url=os.environ["D365FO_BASE_URL"])
    client = FOClient(config)

    try:
        # Check a non-existent execution ID
        status = await client.get_execution_summary_status("non-existent-id")
        assert status
        # Should probably return unknown or error, depending on API behavior

    finally:
        await client.close()
