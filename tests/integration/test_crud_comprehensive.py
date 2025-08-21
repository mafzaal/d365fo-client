"""Comprehensive CRUD operation tests for integration coverage.

This module provides extensive CRUD operation tests to improve integration test coverage
specifically focusing on create, update, and delete entity operations as requested.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any
from d365fo_client import FOClient
from d365fo_client.models import QueryOptions
from . import skip_if_not_level


@skip_if_not_level('mock')
class TestCreateEntityOperations:
    """Comprehensive tests for entity creation operations."""
    
    @pytest.mark.asyncio
    async def test_create_customer_basic(self, mock_client: FOClient, entity_validator):
        """Test basic customer creation."""
        new_customer = {
            'CustomerAccount': 'CREATE-001',
            'CustomerName': 'Basic Test Customer',
            'CustomerGroupId': 'BASIC',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net30'
        }
        
        result = await mock_client.create_entity('Customers', new_customer)
        
        assert entity_validator['customer'](result)
        assert result['CustomerAccount'] == 'CREATE-001'
        assert result['CustomerName'] == 'Basic Test Customer'
        assert 'CreatedDateTime' in result
    
    @pytest.mark.asyncio
    async def test_create_customer_minimal_data(self, mock_client: FOClient):
        """Test creating customer with minimal required data."""
        minimal_customer = {
            'CustomerAccount': 'MIN-001',
            'CustomerName': 'Minimal Customer'
        }
        
        result = await mock_client.create_entity('Customers', minimal_customer)
        
        assert result['CustomerAccount'] == 'MIN-001'
        assert result['CustomerName'] == 'Minimal Customer'
        assert 'CreatedDateTime' in result
    
    @pytest.mark.asyncio
    async def test_create_customer_full_data(self, mock_client: FOClient):
        """Test creating customer with full data set."""
        full_customer = {
            'CustomerAccount': 'FULL-001',
            'CustomerName': 'Full Data Customer Inc',
            'CustomerGroupId': 'PREMIUM',
            'CurrencyCode': 'EUR',
            'PaymentTerms': 'Net45',
            'CreditLimit': 100000.00,
            'TaxGroup': 'STANDARD',
            'DeliveryTerms': 'FOB',
            'ModeOfDelivery': 'TRUCK',
            'Address': '123 Business St, Enterprise City, EC 12345',
            'Phone': '+1-555-123-4567',
            'Email': 'contact@fulldatacustomer.com'
        }
        
        result = await mock_client.create_entity('Customers', full_customer)
        
        assert result['CustomerAccount'] == 'FULL-001'
        assert result['CustomerName'] == 'Full Data Customer Inc'
        assert result['CurrencyCode'] == 'EUR'
        assert result['PaymentTerms'] == 'Net45'
    
    @pytest.mark.asyncio
    async def test_create_vendor_entity(self, mock_client: FOClient, entity_validator):
        """Test creating vendor entity to test different entity types."""
        new_vendor = {
            'VendorAccount': 'VEND-001',
            'VendorName': 'Test Vendor Company',
            'VendorGroupId': 'SUPPLIER',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net60'
        }
        
        result = await mock_client.create_entity('Vendors', new_vendor)
        
        assert entity_validator['vendor'](result)
        assert result['VendorAccount'] == 'VEND-001'
        assert result['VendorName'] == 'Test Vendor Company'
    
    @pytest.mark.asyncio
    async def test_create_entity_with_special_characters(self, mock_client: FOClient):
        """Test creating entity with special characters in data."""
        special_customer = {
            'CustomerAccount': 'SPEC-001',
            'CustomerName': 'Spéciál Cháracters & Symbols Inc.',
            'CustomerGroupId': 'SPECIAL',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net30',
            'Address': 'Straße 123, München, 80331 Deutschland'
        }
        
        result = await mock_client.create_entity('Customers', special_customer)
        
        assert result['CustomerAccount'] == 'SPEC-001'
        assert result['CustomerName'] == 'Spéciál Cháracters & Symbols Inc.'
        assert result['Address'] == 'Straße 123, München, 80331 Deutschland'
    
    @pytest.mark.asyncio
    async def test_create_entity_error_invalid_entity(self, mock_client: FOClient):
        """Test error handling for invalid entity set."""
        test_data = {
            'TestField': 'TestValue'
        }
        
        with pytest.raises(Exception) as exc_info:
            await mock_client.create_entity('NonExistentEntity', test_data)
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_multiple_entities_sequential(self, mock_client: FOClient):
        """Test creating multiple entities sequentially."""
        customers = []
        for i in range(3):
            customer_data = {
                'CustomerAccount': f'SEQ-{i:03d}',
                'CustomerName': f'Sequential Customer {i}',
                'CustomerGroupId': 'SEQUENTIAL',
                'CurrencyCode': 'USD',
                'PaymentTerms': 'Net30'
            }
            
            result = await mock_client.create_entity('Customers', customer_data)
            customers.append(result)
        
        assert len(customers) == 3
        for i, customer in enumerate(customers):
            assert customer['CustomerAccount'] == f'SEQ-{i:03d}'
            assert customer['CustomerName'] == f'Sequential Customer {i}'
    
    @pytest.mark.asyncio
    async def test_create_entity_data_types(self, mock_client: FOClient):
        """Test creating entity with various data types."""
        typed_customer = {
            'CustomerAccount': 'TYPE-001',
            'CustomerName': 'Data Types Customer',
            'CustomerGroupId': 'TYPES',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net30',
            'CreditLimit': 50000.99,  # Float
            'IsActive': True,  # Boolean
            'Priority': 5,  # Integer
            'Notes': None  # Null value
        }
        
        result = await mock_client.create_entity('Customers', typed_customer)
        
        assert result['CustomerAccount'] == 'TYPE-001'
        assert result['CreditLimit'] == 50000.99
        assert result['IsActive'] is True
        assert result['Priority'] == 5


@skip_if_not_level('mock')
class TestUpdateEntityOperations:
    """Comprehensive tests for entity update operations."""
    
    @pytest.mark.asyncio
    async def test_update_customer_patch(self, mock_client: FOClient):
        """Test updating customer with PATCH method."""
        update_data = {
            'CustomerName': 'PATCH Updated Customer',
            'PaymentTerms': 'Net60'
        }
        
        result = await mock_client.update_entity('Customers', 'US-001', update_data, method='PATCH')
        
        assert result['CustomerName'] == 'PATCH Updated Customer'
        assert result['PaymentTerms'] == 'Net60'
        assert result['CustomerAccount'] == 'US-001'  # Key unchanged
    
    @pytest.mark.asyncio
    async def test_update_customer_put(self, mock_client: FOClient):
        """Test updating customer with PUT method."""
        update_data = {
            'CustomerAccount': 'US-001',  # Include key in PUT
            'CustomerName': 'PUT Updated Customer',
            'CustomerGroupId': 'UPDATED',
            'CurrencyCode': 'EUR',
            'PaymentTerms': 'Net90'
        }
        
        result = await mock_client.update_entity('Customers', 'US-001', update_data, method='PUT')
        
        assert result['CustomerName'] == 'PUT Updated Customer'
        assert result['CurrencyCode'] == 'EUR'
        assert result['PaymentTerms'] == 'Net90'
    
    @pytest.mark.asyncio
    async def test_update_customer_partial_fields(self, mock_client: FOClient):
        """Test partial update of customer fields."""
        # Only update specific fields
        partial_update = {
            'PaymentTerms': 'Net15',
            'CreditLimit': 75000.00
        }
        
        result = await mock_client.update_entity('Customers', 'US-001', partial_update)
        
        assert result['PaymentTerms'] == 'Net15'
        assert result['CreditLimit'] == 75000.00
        # Other fields should remain unchanged
        assert result['CustomerAccount'] == 'US-001'
    
    @pytest.mark.asyncio
    async def test_update_vendor_entity(self, mock_client: FOClient):
        """Test updating vendor entity to test different entity types."""
        vendor_update = {
            'VendorName': 'Updated Vendor Name',
            'PaymentTerms': 'Net45'
        }
        
        result = await mock_client.update_entity('Vendors', 'V-001', vendor_update)
        
        assert result['VendorName'] == 'Updated Vendor Name'
        assert result['PaymentTerms'] == 'Net45'
        assert result['VendorAccount'] == 'V-001'
    
    @pytest.mark.asyncio
    async def test_update_entity_special_characters(self, mock_client: FOClient):
        """Test updating entity with special characters."""
        special_update = {
            'CustomerName': 'Üpdated Nâme with Spëcial Characters',
            'Address': 'Røde Plads 1, København, 1200 Denmark'
        }
        
        result = await mock_client.update_entity('Customers', 'US-001', special_update)
        
        assert result['CustomerName'] == 'Üpdated Nâme with Spëcial Characters'
        assert result['Address'] == 'Røde Plads 1, København, 1200 Denmark'
    
    @pytest.mark.asyncio
    async def test_update_entity_data_types(self, mock_client: FOClient):
        """Test updating entity with various data types."""
        typed_update = {
            'CreditLimit': 99999.99,  # Float
            'IsActive': False,  # Boolean
            'Priority': 10,  # Integer
            'Notes': 'Updated notes'  # String
        }
        
        result = await mock_client.update_entity('Customers', 'US-001', typed_update)
        
        assert result['CreditLimit'] == 99999.99
        assert result['IsActive'] is False
        assert result['Priority'] == 10
        assert result['Notes'] == 'Updated notes'
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_entity_key(self, mock_client: FOClient):
        """Test error handling for updating non-existent entity key."""
        update_data = {
            'CustomerName': 'Should Fail'
        }
        
        with pytest.raises(Exception) as exc_info:
            await mock_client.update_entity('Customers', 'NON-EXISTENT', update_data)
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_invalid_entity_set(self, mock_client: FOClient):
        """Test error handling for updating invalid entity set."""
        update_data = {
            'SomeField': 'SomeValue'
        }
        
        with pytest.raises(Exception) as exc_info:
            await mock_client.update_entity('InvalidEntitySet', 'ANY-KEY', update_data)
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_multiple_entities_sequential(self, mock_client: FOClient):
        """Test updating multiple entities sequentially."""
        entities_to_update = ['US-001', 'US-002']
        
        for i, entity_key in enumerate(entities_to_update):
            update_data = {
                'CustomerName': f'Batch Updated Customer {i}',
                'PaymentTerms': f'Net{30 + i * 15}'
            }
            
            result = await mock_client.update_entity('Customers', entity_key, update_data)
            
            assert result['CustomerName'] == f'Batch Updated Customer {i}'
            assert result['PaymentTerms'] == f'Net{30 + i * 15}'
            assert result['CustomerAccount'] == entity_key
    
    @pytest.mark.asyncio
    async def test_update_empty_data(self, mock_client: FOClient):
        """Test updating entity with empty data."""
        empty_update = {}
        
        # Should not fail, but may return success or entity data
        result = await mock_client.update_entity('Customers', 'US-001', empty_update)
        
        # Should at least preserve the key
        assert result['CustomerAccount'] == 'US-001'


@skip_if_not_level('mock')
class TestDeleteEntityOperations:
    """Comprehensive tests for entity delete operations."""
    
    @pytest.mark.asyncio
    async def test_delete_customer_basic(self, mock_client: FOClient):
        """Test basic customer deletion."""
        result = await mock_client.delete_entity('Customers', 'US-002')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_vendor_entity(self, mock_client: FOClient):
        """Test deleting vendor entity to test different entity types."""
        result = await mock_client.delete_entity('Vendors', 'V-001')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity_key(self, mock_client: FOClient):
        """Test error handling for deleting non-existent entity key."""
        with pytest.raises(Exception) as exc_info:
            await mock_client.delete_entity('Customers', 'NON-EXISTENT-KEY')
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_delete_invalid_entity_set(self, mock_client: FOClient):
        """Test error handling for deleting from invalid entity set."""
        with pytest.raises(Exception) as exc_info:
            await mock_client.delete_entity('InvalidEntitySet', 'ANY-KEY')
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_delete_entity_with_special_key(self, mock_client: FOClient):
        """Test deleting entity with special characters in key."""
        # First create an entity with special key
        special_customer = {
            'CustomerAccount': 'SPËC-KEY',
            'CustomerName': 'Special Key Customer',
            'CustomerGroupId': 'SPECIAL',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net30'
        }
        
        # Create it first
        await mock_client.create_entity('Customers', special_customer)
        
        # Then delete it
        result = await mock_client.delete_entity('Customers', 'SPËC-KEY')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_multiple_entities_sequential(self, mock_client: FOClient):
        """Test deleting multiple entities sequentially."""
        # First create multiple entities
        for i in range(3):
            customer_data = {
                'CustomerAccount': f'DEL-{i:03d}',
                'CustomerName': f'Delete Test Customer {i}',
                'CustomerGroupId': 'DELETE_TEST',
                'CurrencyCode': 'USD',
                'PaymentTerms': 'Net30'
            }
            await mock_client.create_entity('Customers', customer_data)
        
        # Then delete them all
        for i in range(3):
            result = await mock_client.delete_entity('Customers', f'DEL-{i:03d}')
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_entity_twice(self, mock_client: FOClient):
        """Test deleting the same entity twice (should fail second time)."""
        # First delete should succeed
        result = await mock_client.delete_entity('Customers', 'US-001')
        assert result is True
        
        # Second delete should fail
        with pytest.raises(Exception) as exc_info:
            await mock_client.delete_entity('Customers', 'US-001')
        
        assert "not found" in str(exc_info.value).lower()


@skip_if_not_level('mock')
class TestCrudWorkflows:
    """Tests for complete CRUD workflows and combinations."""
    
    @pytest.mark.asyncio
    async def test_complete_crud_workflow(self, mock_client: FOClient):
        """Test complete Create -> Read -> Update -> Delete workflow."""
        entity_key = 'WORKFLOW-001'
        
        # 1. Create
        create_data = {
            'CustomerAccount': entity_key,
            'CustomerName': 'Workflow Test Customer',
            'CustomerGroupId': 'WORKFLOW',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net30'
        }
        
        created = await mock_client.create_entity('Customers', create_data)
        assert created['CustomerAccount'] == entity_key
        assert created['CustomerName'] == 'Workflow Test Customer'
        
        # 2. Read
        read_result = await mock_client.get_entity('Customers', entity_key)
        assert read_result['CustomerAccount'] == entity_key
        assert read_result['CustomerName'] == 'Workflow Test Customer'
        
        # 3. Update
        update_data = {
            'CustomerName': 'Updated Workflow Customer',
            'PaymentTerms': 'Net45'
        }
        
        updated = await mock_client.update_entity('Customers', entity_key, update_data)
        assert updated['CustomerAccount'] == entity_key
        assert updated['CustomerName'] == 'Updated Workflow Customer'
        assert updated['PaymentTerms'] == 'Net45'
        
        # 4. Verify update
        read_updated = await mock_client.get_entity('Customers', entity_key)
        assert read_updated['CustomerName'] == 'Updated Workflow Customer'
        assert read_updated['PaymentTerms'] == 'Net45'
        
        # 5. Delete
        deleted = await mock_client.delete_entity('Customers', entity_key)
        assert deleted is True
        
        # 6. Verify deletion
        with pytest.raises(Exception):
            await mock_client.get_entity('Customers', entity_key)
    
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, mock_client: FOClient, performance_metrics):
        """Test performance of bulk CRUD operations."""
        import time
        
        bulk_size = 5
        entity_keys = [f'BULK-{i:03d}' for i in range(bulk_size)]
        
        # Bulk Create
        start_time = time.time()
        for key in entity_keys:
            customer_data = {
                'CustomerAccount': key,
                'CustomerName': f'Bulk Customer {key}',
                'CustomerGroupId': 'BULK',
                'CurrencyCode': 'USD',
                'PaymentTerms': 'Net30'
            }
            await mock_client.create_entity('Customers', customer_data)
        
        create_duration = time.time() - start_time
        performance_metrics['timings']['bulk_create'] = create_duration
        
        # Bulk Update
        start_time = time.time()
        for key in entity_keys:
            update_data = {
                'CustomerName': f'Updated Bulk Customer {key}',
                'PaymentTerms': 'Net45'
            }
            await mock_client.update_entity('Customers', key, update_data)
        
        update_duration = time.time() - start_time
        performance_metrics['timings']['bulk_update'] = update_duration
        
        # Bulk Delete
        start_time = time.time()
        for key in entity_keys:
            await mock_client.delete_entity('Customers', key)
        
        delete_duration = time.time() - start_time
        performance_metrics['timings']['bulk_delete'] = delete_duration
        
        # Performance assertions
        assert create_duration < 10.0, f"Bulk create took too long: {create_duration}s"
        assert update_duration < 10.0, f"Bulk update took too long: {update_duration}s"
        assert delete_duration < 10.0, f"Bulk delete took too long: {delete_duration}s"
    
    @pytest.mark.asyncio
    async def test_create_update_with_query_options(self, mock_client: FOClient):
        """Test CRUD operations combined with query options."""
        entity_key = 'QUERY-001'
        
        # Create entity
        create_data = {
            'CustomerAccount': entity_key,
            'CustomerName': 'Query Options Customer',
            'CustomerGroupId': 'QUERY',
            'CurrencyCode': 'USD',
            'PaymentTerms': 'Net30'
        }
        
        created = await mock_client.create_entity('Customers', create_data)
        assert created['CustomerAccount'] == entity_key
        
        # Read with query options
        query_options = QueryOptions(select=['CustomerAccount', 'CustomerName'])
        read_result = await mock_client.get_entity('Customers', entity_key, query_options)
        
        assert 'CustomerAccount' in read_result
        assert 'CustomerName' in read_result
        # Other fields might or might not be present depending on server implementation
        
        # Clean up
        await mock_client.delete_entity('Customers', entity_key)