"""Tests for metadata API operations."""

import pytest
from unittest.mock import AsyncMock, Mock
import json

from src.d365fo_client.metadata_api import MetadataAPIOperations
from src.d365fo_client.models import (
    QueryOptions, DataEntityInfo, PublicEntityInfo, EnumerationInfo
)


@pytest.fixture
def mock_session_manager():
    """Mock session manager"""
    session_manager = Mock()
    session = AsyncMock()
    session_manager.get_session = AsyncMock(return_value=session)
    return session_manager, session


@pytest.fixture
def mock_label_ops():
    """Mock label operations"""
    label_ops = AsyncMock()
    label_ops.get_label_text.return_value = "Test Label"
    label_ops.get_labels_batch.return_value = {
        "@TEST123": "Test Label",
        "@SYS456": "System Label"
    }
    return label_ops


@pytest.fixture
def metadata_api_ops(mock_session_manager, mock_label_ops):
    """Create MetadataAPIOperations instance with mocks"""
    session_manager, _ = mock_session_manager
    return MetadataAPIOperations(
        session_manager=session_manager,
        metadata_url="https://test.dynamics.com/Metadata",
        label_ops=mock_label_ops
    )


class TestDataEntitiesAPI:
    """Tests for DataEntities API operations"""
    
    @pytest.mark.asyncio
    async def test_get_data_entities_success(self, metadata_api_ops, mock_session_manager):
        """Test successful retrieval of data entities"""
        _, session = mock_session_manager
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "@odata.context": "test",
            "value": [
                {
                    "Name": "TestEntity",
                    "PublicEntityName": "Test",
                    "PublicCollectionName": "Tests",
                    "LabelId": "@TEST123",
                    "DataServiceEnabled": True,
                    "DataManagementEnabled": True,
                    "EntityCategory": "Master",
                    "IsReadOnly": False
                }
            ]
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        options = QueryOptions(top=10)
        result = await metadata_api_ops.get_data_entities(options)
        
        # Assertions
        assert result["@odata.context"] == "test"
        assert len(result["value"]) == 1
        assert result["value"][0]["Name"] == "TestEntity"
        
        # Verify session.get was called with correct URL and params
        session.get.assert_called_once()
        call_args = session.get.call_args
        assert call_args[0][0] == "https://test.dynamics.com/Metadata/DataEntities"
        assert call_args[1]["params"]["$top"] == "10"
    
    @pytest.mark.asyncio
    async def test_search_data_entities_with_filters(self, metadata_api_ops, mock_session_manager):
        """Test searching data entities with various filters"""
        _, session = mock_session_manager
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "Name": "CustomerEntity",
                    "PublicEntityName": "Customer",
                    "PublicCollectionName": "Customers",
                    "LabelId": "@CUS123",
                    "DataServiceEnabled": True,
                    "DataManagementEnabled": True,
                    "EntityCategory": "Master",
                    "IsReadOnly": False
                }
            ]
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test with multiple filters
        result = await metadata_api_ops.search_data_entities(
            pattern="customer",
            entity_category="Master",
            data_service_enabled=True,
            is_read_only=False
        )
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], DataEntityInfo)
        assert result[0].name == "CustomerEntity"
        assert result[0].entity_category == "Master"
        
        # Verify the filter was constructed correctly
        call_args = session.get.call_args
        params = call_args[1]["params"]
        filter_expr = params["$filter"]
        assert "contains(tolower(Name), 'customer')" in filter_expr
        assert "EntityCategory eq Microsoft.Dynamics.Metadata.EntityCategory'Master'" in filter_expr
        assert "DataServiceEnabled eq true" in filter_expr
        assert "IsReadOnly eq false" in filter_expr
    
    @pytest.mark.asyncio
    async def test_get_data_entity_info_with_labels(self, metadata_api_ops, mock_session_manager, mock_label_ops):
        """Test getting specific data entity info with label resolution"""
        _, session = mock_session_manager
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "Name": "TestEntity",
            "PublicEntityName": "Test",
            "PublicCollectionName": "Tests",
            "LabelId": "@TEST123",
            "DataServiceEnabled": True,
            "DataManagementEnabled": True,
            "EntityCategory": "Master",
            "IsReadOnly": False
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        result = await metadata_api_ops.get_data_entity_info("TestEntity")
        
        # Assertions
        assert isinstance(result, DataEntityInfo)
        assert result.name == "TestEntity"
        assert result.label_text == "Test Label"  # From mock_label_ops
        
        # Verify label resolution was called
        mock_label_ops.get_label_text.assert_called_once_with("@TEST123", "en-US")
    
    @pytest.mark.asyncio
    async def test_get_data_entity_info_not_found(self, metadata_api_ops, mock_session_manager):
        """Test getting data entity info for non-existent entity"""
        _, session = mock_session_manager
        
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        result = await metadata_api_ops.get_data_entity_info("NonExistentEntity")
        
        # Assertions
        assert result is None


class TestPublicEntitiesAPI:
    """Tests for PublicEntities API operations"""
    
    @pytest.mark.asyncio
    async def test_search_public_entities(self, metadata_api_ops, mock_session_manager):
        """Test searching public entities"""
        _, session = mock_session_manager
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "Name": "Customer",
                    "EntitySetName": "Customers",
                    "LabelId": "@CUS123",
                    "IsReadOnly": False,
                    "ConfigurationEnabled": True
                }
            ]
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        result = await metadata_api_ops.search_public_entities("customer")
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], PublicEntityInfo)
        assert result[0].name == "Customer"
        assert result[0].entity_set_name == "Customers"
    
    @pytest.mark.asyncio
    async def test_get_public_entity_info_with_properties(self, metadata_api_ops, mock_session_manager, mock_label_ops):
        """Test getting detailed public entity info with properties"""
        _, session = mock_session_manager
        
        # Mock response with properties
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "Name": "Customer",
            "EntitySetName": "Customers",
            "LabelId": "@CUS123",
            "IsReadOnly": False,
            "ConfigurationEnabled": True,
            "Properties": [
                {
                    "Name": "CustomerAccount",
                    "TypeName": "Edm.String",
                    "DataType": "String",
                    "LabelId": "@SYS456",
                    "IsKey": True,
                    "IsMandatory": True,
                    "ConfigurationEnabled": True,
                    "AllowEdit": False,
                    "AllowEditOnCreate": True,
                    "IsDimension": False,
                    "DimensionRelation": None,
                    "IsDynamicDimension": False,
                    "DimensionLegalEntityProperty": None,
                    "DimensionTypeProperty": None
                }
            ],
            "NavigationProperties": [],
            "PropertyGroups": [],
            "Actions": []
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        result = await metadata_api_ops.get_public_entity_info("Customer")
        
        # Assertions
        assert isinstance(result, PublicEntityInfo)
        assert result.name == "Customer"
        assert len(result.properties) == 1
        
        prop = result.properties[0]
        assert prop.name == "CustomerAccount"
        assert prop.is_key is True
        assert prop.is_mandatory is True
        assert prop.label_text == "System Label"  # From mock_label_ops batch


class TestPublicEnumerationsAPI:
    """Tests for PublicEnumerations API operations"""
    
    @pytest.mark.asyncio
    async def test_search_public_enumerations(self, metadata_api_ops, mock_session_manager):
        """Test searching public enumerations"""
        _, session = mock_session_manager
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "Name": "PaymentType",
                    "LabelId": "@PAY123"
                }
            ]
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        result = await metadata_api_ops.search_public_enumerations("payment")
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], EnumerationInfo)
        assert result[0].name == "PaymentType"
    
    @pytest.mark.asyncio
    async def test_get_public_enumeration_info_with_members(self, metadata_api_ops, mock_session_manager, mock_label_ops):
        """Test getting detailed enumeration info with members"""
        _, session = mock_session_manager
        
        # Mock response with members
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "Name": "ABC",
            "LabelId": "@ABC123",
            "Members": [
                {
                    "Name": "A",
                    "LabelId": "@A123",
                    "Value": 1,
                    "ConfigurationEnabled": True
                },
                {
                    "Name": "B", 
                    "LabelId": "@B123",
                    "Value": 2,
                    "ConfigurationEnabled": True
                }
            ]
        }
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test
        result = await metadata_api_ops.get_public_enumeration_info("ABC")
        
        # Assertions
        assert isinstance(result, EnumerationInfo)
        assert result.name == "ABC"
        assert len(result.members) == 2
        
        member_a = result.members[0]
        assert member_a.name == "A"
        assert member_a.value == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, metadata_api_ops, mock_session_manager):
        """Test error handling for failed requests"""
        _, session = mock_session_manager
        
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        
        session.get.return_value.__aenter__.return_value = mock_response
        
        # Test that exception is raised
        with pytest.raises(Exception) as exc_info:
            await metadata_api_ops.get_data_entities()
        
        assert "Failed to get data entities: 500" in str(exc_info.value)


class TestQueryBuilder:
    """Test query parameter building"""
    
    def test_build_query_params_with_all_options(self):
        """Test building query parameters with all options"""
        from src.d365fo_client.query import QueryBuilder
        
        options = QueryOptions(
            select=["Name", "Id"],
            filter="Name eq 'Test'",
            expand=["Properties"],
            orderby=["Name asc"],
            top=10,
            skip=5,
            count=True,
            search="test"
        )
        
        params = QueryBuilder.build_query_params(options)
        
        assert params["$select"] == "Name,Id"
        assert params["$filter"] == "Name eq 'Test'"
        assert params["$expand"] == "Properties"
        assert params["$orderby"] == "Name asc"
        assert params["$top"] == "10"
        assert params["$skip"] == "5"
        assert params["$count"] == "true"
        assert params["$search"] == "test"
    
    def test_build_query_params_empty(self):
        """Test building query parameters with no options"""
        from src.d365fo_client.query import QueryBuilder
        
        params = QueryBuilder.build_query_params(None)
        assert params == {}
        
        params = QueryBuilder.build_query_params(QueryOptions())
        assert params == {}


if __name__ == "__main__":
    pytest.main([__file__])