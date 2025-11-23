from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client.dmf_operations import DmfOperations
from d365fo_client.exceptions import DMFError


@pytest.fixture
def mock_session_manager():
    manager = MagicMock()
    manager.get_session = AsyncMock()
    return manager


@pytest.fixture
def dmf_ops(mock_session_manager):
    return DmfOperations(mock_session_manager, "https://test.dynamics.com")


@pytest.mark.asyncio
async def test_export_to_package(dmf_ops, mock_session_manager):
    # Setup
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = "exec-123"

    # Fix: session.post should be a MagicMock that returns an async context manager
    session = MagicMock()
    post_ctx = AsyncMock()
    post_ctx.__aenter__.return_value = mock_response
    session.post.return_value = post_ctx

    mock_session_manager.get_session.return_value = session

    # Execute
    result = await dmf_ops.export_to_package(
        definition_group_id="TestGroup",
        package_name="TestPackage",
        legal_entity_id="USMF",
    )

    # Verify
    assert result == "exec-123"
    session.post.assert_called_once()
    args, kwargs = session.post.call_args
    assert "ExportToPackage" in args[0]
    assert kwargs["json"]["definitionGroupId"] == "TestGroup"
    assert kwargs["json"]["packageName"] == "TestPackage"
    assert kwargs["json"]["legalEntityId"] == "USMF"


@pytest.mark.asyncio
async def test_export_to_package_async(dmf_ops, mock_session_manager):
    # Setup
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = "exec-async-123"

    session = MagicMock()
    post_ctx = AsyncMock()
    post_ctx.__aenter__.return_value = mock_response
    session.post.return_value = post_ctx

    mock_session_manager.get_session.return_value = session

    # Execute
    result = await dmf_ops.export_to_package_async(
        definition_group_id="TestGroup",
        package_name="TestPackage",
        entity_list="CustTable,VendTable",
    )

    # Verify
    assert result == "exec-async-123"
    session.post.assert_called_once()
    _, kwargs = session.post.call_args
    assert kwargs["json"]["entityList"] == "CustTable,VendTable"


@pytest.mark.asyncio
async def test_import_from_package(dmf_ops, mock_session_manager):
    # Setup
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = "exec-import-123"

    session = MagicMock()
    post_ctx = AsyncMock()
    post_ctx.__aenter__.return_value = mock_response
    session.post.return_value = post_ctx

    mock_session_manager.get_session.return_value = session

    # Execute
    result = await dmf_ops.import_from_package(
        package_url="https://blob.storage/package.zip",
        definition_group_id="ImportGroup",
    )

    # Verify
    assert result == "exec-import-123"
    _, kwargs = session.post.call_args
    assert kwargs["json"]["packageUrl"] == "https://blob.storage/package.zip"


@pytest.mark.asyncio
async def test_get_execution_summary_status(dmf_ops, mock_session_manager):
    # Setup
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"ExecutionId": "exec-123", "Status": "Succeeded"}

    session = MagicMock()
    post_ctx = AsyncMock()
    post_ctx.__aenter__.return_value = mock_response
    session.post.return_value = post_ctx

    mock_session_manager.get_session.return_value = session

    # Execute
    result = await dmf_ops.get_execution_summary_status("exec-123")

    # Verify
    assert result["Status"] == "Succeeded"
    _, kwargs = session.post.call_args
    assert kwargs["json"]["executionId"] == "exec-123"


@pytest.mark.asyncio
async def test_get_azure_write_url(dmf_ops, mock_session_manager):
    # Setup
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = "https://blob.storage/upload?sas=token"

    session = MagicMock()
    post_ctx = AsyncMock()
    post_ctx.__aenter__.return_value = mock_response
    session.post.return_value = post_ctx

    mock_session_manager.get_session.return_value = session

    # Execute
    result = await dmf_ops.get_azure_write_url("test.zip")

    # Verify
    assert result == "https://blob.storage/upload?sas=token"
    _, kwargs = session.post.call_args
    assert kwargs["json"]["uniqueFileName"] == "test.zip"


@pytest.mark.asyncio
async def test_error_handling(dmf_ops, mock_session_manager):
    # Setup
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Internal Server Error"

    session = MagicMock()
    post_ctx = AsyncMock()
    post_ctx.__aenter__.return_value = mock_response
    session.post.return_value = post_ctx

    mock_session_manager.get_session.return_value = session

    # Execute & Verify
    with pytest.raises(DMFError) as excinfo:
        await dmf_ops.initialize_data_management()

    assert "500" in str(excinfo.value)
    assert "Internal Server Error" in str(excinfo.value)
