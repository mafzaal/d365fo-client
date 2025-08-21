"""Tests for GetPlatformBuildVersion and GetApplicationBuildVersion action methods."""

import pytest
from unittest.mock import AsyncMock, patch
from d365fo_client import FOClient, FOClientConfig
from d365fo_client.exceptions import FOClientError


class TestGetPlatformBuildVersion:
    """Tests for get_platform_build_version method"""
    
    @pytest.mark.asyncio
    async def test_get_platform_build_version_success(self):
        """Test successful GetPlatformBuildVersion action call"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = "10.0.1985.137"
            
            async with FOClient(config) as client:
                result = await client.get_platform_build_version()
                
                assert result == "10.0.1985.137"
                
                mock_call.assert_called_once_with(
                    "GetPlatformBuildVersion",
                    parameters=None,
                    entity_name="DataManagementEntities"
                )

    @pytest.mark.asyncio
    async def test_get_platform_build_version_dict_response(self):
        """Test GetPlatformBuildVersion action call with dict response containing value"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = {"value": "10.0.1985.137"}
            
            async with FOClient(config) as client:
                result = await client.get_platform_build_version()
                
                assert result == "10.0.1985.137"

    @pytest.mark.asyncio
    async def test_get_platform_build_version_other_response(self):
        """Test GetPlatformBuildVersion action call with other response types"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        # Test with number response
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = 123
            
            async with FOClient(config) as client:
                result = await client.get_platform_build_version()
                
                assert result == "123"
        
        # Test with None response
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = None
            
            async with FOClient(config) as client:
                result = await client.get_platform_build_version()
                
                assert result == ""

    @pytest.mark.asyncio
    async def test_get_platform_build_version_error(self):
        """Test GetPlatformBuildVersion action call error handling"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.side_effect = Exception("Action failed")
            
            async with FOClient(config) as client:
                with pytest.raises(FOClientError, match="Failed to get platform build version"):
                    await client.get_platform_build_version()


class TestGetApplicationBuildVersion:
    """Tests for get_application_build_version method"""
    
    @pytest.mark.asyncio
    async def test_get_application_build_version_success(self):
        """Test successful GetApplicationBuildVersion action call"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = "10.0.1985.137"
            
            async with FOClient(config) as client:
                result = await client.get_application_build_version()
                
                assert result == "10.0.1985.137"
                
                mock_call.assert_called_once_with(
                    "GetApplicationBuildVersion",
                    parameters=None,
                    entity_name="DataManagementEntities"
                )

    @pytest.mark.asyncio
    async def test_get_application_build_version_dict_response(self):
        """Test GetApplicationBuildVersion action call with dict response containing value"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = {"value": "10.0.1985.137"}
            
            async with FOClient(config) as client:
                result = await client.get_application_build_version()
                
                assert result == "10.0.1985.137"

    @pytest.mark.asyncio
    async def test_get_application_build_version_other_response(self):
        """Test GetApplicationBuildVersion action call with other response types"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        # Test with number response
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = 123
            
            async with FOClient(config) as client:
                result = await client.get_application_build_version()
                
                assert result == "123"
        
        # Test with None response
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.return_value = None
            
            async with FOClient(config) as client:
                result = await client.get_application_build_version()
                
                assert result == ""

    @pytest.mark.asyncio
    async def test_get_application_build_version_error(self):
        """Test GetApplicationBuildVersion action call error handling"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            mock_call.side_effect = Exception("Action failed")
            
            async with FOClient(config) as client:
                with pytest.raises(FOClientError, match="Failed to get application build version"):
                    await client.get_application_build_version()


class TestVersionMethodsIntegration:
    """Integration tests for all version methods"""
    
    @pytest.mark.asyncio
    async def test_all_version_methods_available(self):
        """Test that all version methods are available on client"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        async with FOClient(config) as client:
            # Check methods exist
            assert hasattr(client, 'get_application_version')
            assert hasattr(client, 'get_platform_build_version')
            assert hasattr(client, 'get_application_build_version')
            
            # Check they are coroutine functions
            import inspect
            assert inspect.iscoroutinefunction(client.get_application_version)
            assert inspect.iscoroutinefunction(client.get_platform_build_version)
            assert inspect.iscoroutinefunction(client.get_application_build_version)

    @pytest.mark.asyncio
    async def test_all_version_methods_parallel(self):
        """Test calling all version methods in parallel"""
        config = FOClientConfig(base_url="https://test.dynamics.com")
        
        with patch.object(FOClient, 'call_action') as mock_call:
            # Set up different return values for each call
            mock_call.side_effect = [
                "10.0.1985.137",  # Application version
                "10.0.1985.137",  # Platform build version  
                "10.0.1985.137"   # Application build version
            ]
            
            async with FOClient(config) as client:
                import asyncio
                
                # Call all methods in parallel
                app_version, platform_version, app_build_version = await asyncio.gather(
                    client.get_application_version(),
                    client.get_platform_build_version(),
                    client.get_application_build_version()
                )
                
                assert app_version == "10.0.1985.137"
                assert platform_version == "10.0.1985.137"
                assert app_build_version == "10.0.1985.137"
                
                # Verify all calls were made
                assert mock_call.call_count == 3
                
                # Verify correct actions were called
                calls = mock_call.call_args_list
                assert calls[0][0][0] == "GetApplicationVersion"
                assert calls[1][0][0] == "GetPlatformBuildVersion"
                assert calls[2][0][0] == "GetApplicationBuildVersion"


@pytest.mark.asyncio
async def test_version_methods_integration():
    """Integration test for version methods (requires live connection)"""
    # This test would require actual F&O credentials and connection
    # Uncomment and configure if you want to test against a real environment
    
    # config = FOClientConfig(
    #     base_url="https://your-d365.dynamics.com",
    #     use_default_credentials=True,
    #     verify_ssl=False
    # )
    # 
    # async with FOClient(config) as client:
    #     app_version = await client.get_application_version()
    #     platform_version = await client.get_platform_build_version()
    #     app_build_version = await client.get_application_build_version()
    #     
    #     # Verify the results are non-empty strings
    #     assert isinstance(app_version, str) and len(app_version) > 0
    #     assert isinstance(platform_version, str) and len(platform_version) > 0
    #     assert isinstance(app_build_version, str) and len(app_build_version) > 0
    #     
    #     print(f"Application version: {app_version}")
    #     print(f"Platform build version: {platform_version}")
    #     print(f"Application build version: {app_build_version}")
    
    # Skip this test unless explicitly enabled
    pytest.skip("Integration test requires live F&O connection")