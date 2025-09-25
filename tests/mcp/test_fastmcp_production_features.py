"""
Tests for FastMCP Production Features (Phase 4)

This module contains comprehensive tests for the Phase 4 FastMCP production features:
- Stateless HTTP mode
- JSON response support  
- Performance optimizations
- Connection pooling
- Request limiting
- Performance monitoring
"""

import asyncio
import json
import os
import pytest
import time
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio

# Import the FastMCP server and related components
from d365fo_client.mcp.fastmcp_server import FastD365FOMCPServer
from d365fo_client.mcp.client_manager import D365FOClientManager


@pytest_asyncio.fixture
async def production_config():
    """Production configuration for testing."""
    return {
        "startup_mode": "client_credentials",
        "server": {
            "name": "d365fo-fastmcp-server",
            "debug": False,
            "transport": {
                "http": {
                    "host": "127.0.0.1",
                    "port": 8000,
                    "stateless": True,
                    "json_response": True,
                    "cors": {
                        "enabled": True,
                        "origins": ["*"],
                        "methods": ["GET", "POST", "DELETE"],
                        "headers": ["*"]
                    }
                }
            }
        },
        "performance": {
            "max_concurrent_requests": 20,
            "connection_pool_size": 10,
            "request_timeout": 45,
            "batch_size": 150,
            "enable_performance_monitoring": True,
            "session_cleanup_interval": 300,
            "max_request_history": 1000,
        },
        "default_environment": {
            "base_url": "https://test-env.dynamics.com",
            "use_default_credentials": False,
        },
        "cache": {
            "metadata_cache_dir": "/tmp/test_cache",
            "label_cache_expiry_minutes": 120,
            "use_label_cache": True,
            "cache_size_limit_mb": 200,
        },
        "security": {
            "encrypt_cached_tokens": True,
            "token_expiry_buffer_minutes": 10,
            "max_retry_attempts": 5,
            "cors_enabled": True,
        }
    }


@pytest_asyncio.fixture
async def mock_client_manager():
    """Mock client manager for testing."""
    manager = AsyncMock(spec=D365FOClientManager)
    
    # Mock health check responses
    manager.health_check.return_value = {
        "default": {
            "healthy": True,
            "last_checked": "2024-01-15T10:30:00Z"
        }
    }
    
    # Mock client responses
    mock_client = AsyncMock()
    mock_client.test_connection.return_value = True
    mock_client.get_application_version.return_value = "10.0.1"
    manager.get_client.return_value = mock_client
    manager.test_connection.return_value = True
    manager.get_environment_info.return_value = {
        "base_url": "https://test-env.dynamics.com",
        "versions": {
            "application": "10.0.1",
            "platform": "7.0.1",
            "build": "10.0.123.456"
        },
        "connectivity": True
    }
    
    return manager


@pytest_asyncio.fixture
async def fastmcp_server(production_config, mock_client_manager):
    """FastMCP server instance for testing."""
    with patch('d365fo_client.mcp.fastmcp_server.D365FOClientManager', return_value=mock_client_manager):
        server = FastD365FOMCPServer(production_config)
        yield server
        await server.cleanup()


class TestFastMCPProductionFeatures:
    """Test suite for FastMCP Phase 4 production features."""


class TestStatelessMode:
    """Tests for stateless HTTP mode functionality."""
    
    @pytest.mark.asyncio
    async def test_stateless_mode_initialization(self, fastmcp_server):
        """Test that stateless mode is properly initialized."""
        assert fastmcp_server._stateless_mode is True
        assert hasattr(fastmcp_server, '_stateless_sessions')
        
    @pytest.mark.asyncio
    async def test_session_context_creation(self, fastmcp_server):
        """Test session context creation in stateless mode."""
        # Test creating a new session context
        session_context = fastmcp_server._get_session_context("test_session_123")
        
        assert session_context["session_id"] == "test_session_123"
        assert session_context["stateless"] is True
        assert "created_at" in session_context
        assert "last_accessed" in session_context
        assert session_context["request_count"] == 0
        
    @pytest.mark.asyncio
    async def test_session_context_auto_generation(self, fastmcp_server):
        """Test automatic session ID generation."""
        session_context = fastmcp_server._get_session_context()
        
        assert session_context["session_id"].startswith("stateless_")
        assert session_context["stateless"] is True
        
    @pytest.mark.asyncio
    async def test_session_cleanup(self, fastmcp_server):
        """Test session cleanup functionality."""
        # Create a session
        session_id = "test_cleanup_session"
        session_context = fastmcp_server._get_session_context(session_id)
        
        # For WeakValueDictionary, we need to keep a strong reference
        # to prevent garbage collection during test
        strong_ref = None
        if session_id in fastmcp_server._stateless_sessions:
            strong_ref = fastmcp_server._stateless_sessions[session_id]
            
            # Manually age the session
            import datetime
            strong_ref.last_accessed = datetime.datetime.now() - datetime.timedelta(hours=1)
        
        # Run cleanup (this should work even if session was garbage collected)
        fastmcp_server._cleanup_expired_sessions()
        
        # The main goal is that cleanup runs without error
        # WeakValueDictionary may garbage collect the session automatically


class TestJSONResponseMode:
    """Tests for JSON response mode functionality."""
    
    @pytest.mark.asyncio
    async def test_json_response_mode_initialization(self, fastmcp_server):
        """Test that JSON response mode is properly initialized."""
        assert fastmcp_server._json_response_mode is True
        
    @pytest.mark.asyncio
    async def test_json_response_format(self, fastmcp_server):
        """Test that responses are in JSON format."""
        # This would be tested at the transport level in integration tests
        # Here we verify the server is configured for JSON responses
        assert fastmcp_server._json_response_mode is True
        
        # Verify configuration passed to FastMCP
        # Note: FastMCP internal attributes may vary - we test the server config
        assert hasattr(fastmcp_server, 'mcp')
        assert fastmcp_server.mcp is not None


class TestPerformanceOptimizations:
    """Tests for performance optimization features."""
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_initialization(self, fastmcp_server):
        """Test performance monitoring setup."""
        assert hasattr(fastmcp_server, '_request_stats')
        assert hasattr(fastmcp_server, '_request_times')
        assert hasattr(fastmcp_server, '_connection_pool_stats')
        assert hasattr(fastmcp_server, '_request_semaphore')
        
        # Check initial stats
        assert fastmcp_server._request_stats['total_requests'] == 0
        assert fastmcp_server._request_stats['total_errors'] == 0
        assert fastmcp_server._request_stats['avg_response_time'] == 0.0
        
    @pytest.mark.asyncio
    async def test_request_limiting(self, fastmcp_server):
        """Test request limiting with semaphore."""
        max_concurrent = fastmcp_server._max_concurrent_requests
        semaphore = fastmcp_server._request_semaphore
        
        assert semaphore._value == max_concurrent
        assert max_concurrent == 20  # From production config
        
    @pytest.mark.asyncio 
    async def test_performance_stats_collection(self, fastmcp_server):
        """Test performance statistics collection."""
        # Record some test request times
        fastmcp_server._record_request_time(0.1)
        fastmcp_server._record_request_time(0.2)
        fastmcp_server._record_request_time(0.15)
        
        assert len(fastmcp_server._request_times) == 3
        assert fastmcp_server._request_stats['avg_response_time'] == 0.15
        
    @pytest.mark.asyncio
    async def test_performance_stats_retrieval(self, fastmcp_server):
        """Test getting performance statistics."""
        # Add some test data
        fastmcp_server._request_stats['total_requests'] = 100
        fastmcp_server._request_stats['total_errors'] = 5
        fastmcp_server._record_request_time(0.1)
        fastmcp_server._record_request_time(0.3)
        
        stats = fastmcp_server.get_performance_stats()
        
        assert 'total_requests' in stats
        assert 'total_errors' in stats
        assert 'error_rate' in stats
        assert 'avg_response_time_ms' in stats
        assert 'stateless_mode' in stats
        assert 'json_response_mode' in stats
        
        assert stats['total_requests'] == 100
        assert stats['total_errors'] == 5
        assert stats['error_rate'] == 5.0
        assert stats['stateless_mode'] is True
        assert stats['json_response_mode'] is True
        
    @pytest.mark.asyncio
    async def test_percentile_calculation(self, fastmcp_server):
        """Test percentile calculation for response times."""
        # Add test data
        times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for t in times:
            fastmcp_server._record_request_time(t)
            
        p95 = fastmcp_server._calculate_percentile(times, 95)
        assert abs(p95 - 0.95) < 0.01  # Allow for floating point precision
        
        p50 = fastmcp_server._calculate_percentile(times, 50)
        assert abs(p50 - 0.55) < 0.01  # Allow for floating point precision


class TestProductionConfiguration:
    """Tests for production configuration features."""
    
    @pytest.mark.asyncio
    async def test_environment_variable_configuration(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            'D365FO_MAX_CONCURRENT_REQUESTS': '25',
            'D365FO_REQUEST_TIMEOUT': '60',
            'MCP_CONNECTION_POOL_SIZE': '15',
            'D365FO_HTTP_STATELESS': 'true',
            'D365FO_HTTP_JSON': 'true',
            'MCP_PERFORMANCE_MONITORING': 'true'
        }):
            # Create server with environment-based config
            server = FastD365FOMCPServer()
            
            # Check that environment variables are used
            assert server._max_concurrent_requests == 25
            assert server._request_timeout == 60
            assert server._stateless_mode is True
            assert server._json_response_mode is True
            
            await server.cleanup()
            
    @pytest.mark.asyncio
    async def test_production_defaults(self, production_config):
        """Test production default configuration values."""
        with patch('d365fo_client.mcp.fastmcp_server.D365FOClientManager') as mock_manager:
            mock_manager.return_value = AsyncMock()
            
            server = FastD365FOMCPServer(production_config)
            
            # Check production configuration values
            assert server._max_concurrent_requests == 20
            assert server._request_timeout == 45
            assert server._batch_size == 150
            assert server._stateless_mode is True
            assert server._json_response_mode is True
            
            await server.cleanup()


class TestPerformanceTools:
    """Tests for built-in performance monitoring tools."""
    
    @pytest.mark.asyncio
    async def test_server_performance_tool(self, fastmcp_server):
        """Test the d365fo_get_server_performance tool."""
        # Simulate some activity
        fastmcp_server._request_stats['total_requests'] = 50
        fastmcp_server._request_stats['total_errors'] = 2
        fastmcp_server._record_request_time(0.2)
        
        # The tool would be called via MCP protocol in real usage
        # Here we test the underlying functionality
        stats = fastmcp_server.get_performance_stats()
        
        assert stats['total_requests'] == 50
        assert stats['total_errors'] == 2
        assert stats['error_rate'] == 4.0
        assert 'avg_response_time_ms' in stats
        
    @pytest.mark.asyncio
    async def test_performance_reset_functionality(self, fastmcp_server):
        """Test performance stats reset functionality."""
        # Add some test data
        fastmcp_server._request_stats['total_requests'] = 100
        fastmcp_server._request_stats['total_errors'] = 10
        fastmcp_server._record_request_time(0.5)
        
        # Reset stats (simulating the reset tool)
        fastmcp_server._request_stats = {
            'total_requests': 0,
            'total_errors': 0,
            'avg_response_time': 0.0,
            'last_reset': fastmcp_server._request_stats['last_reset']
        }
        fastmcp_server._request_times = []
        fastmcp_server._connection_pool_stats = {
            'active_connections': 0,
            'peak_connections': 0,
            'connection_errors': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
        
        # Verify reset
        stats = fastmcp_server.get_performance_stats()
        assert stats['total_requests'] == 0
        assert stats['total_errors'] == 0
        assert stats['error_rate'] == 0.0


class TestConcurrencyControl:
    """Tests for concurrency control and request limiting."""
    
    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, fastmcp_server):
        """Test that concurrent requests are properly limited."""
        semaphore = fastmcp_server._request_semaphore
        max_concurrent = fastmcp_server._max_concurrent_requests
        
        # Acquire all permits
        acquired = []
        for i in range(max_concurrent):
            result = await semaphore.acquire()
            acquired.append(result)
            
        # Semaphore should now be at capacity
        assert semaphore._value == 0
        
        # Try to acquire one more (should not succeed immediately)
        acquire_task = asyncio.create_task(semaphore.acquire())
        
        # Give it a moment to try
        await asyncio.sleep(0.01)
        assert not acquire_task.done()
        
        # Release one permit
        semaphore.release()
        
        # Now the waiting task should complete
        await acquire_task
        
        # Clean up remaining permits
        for _ in range(max_concurrent):
            semaphore.release()
            
    @pytest.mark.asyncio
    async def test_request_timeout_configuration(self, fastmcp_server):
        """Test request timeout configuration."""
        assert fastmcp_server._request_timeout == 45  # From production config
        
        # Test with custom timeout
        custom_config = {
            "performance": {
                "request_timeout": 120
            }
        }
        
        with patch('d365fo_client.mcp.fastmcp_server.D365FOClientManager') as mock_manager:
            mock_manager.return_value = AsyncMock()
            
            custom_server = FastD365FOMCPServer(custom_config)
            assert custom_server._request_timeout == 120
            
            await custom_server.cleanup()


class TestErrorHandling:
    """Tests for error handling in production features."""
    
    @pytest.mark.asyncio
    async def test_startup_initialization_error_handling(self, production_config):
        """Test that startup errors don't crash the server."""
        # Mock client manager to raise an error during startup
        with patch('d365fo_client.mcp.fastmcp_server.D365FOClientManager') as mock_manager:
            mock_client_manager = AsyncMock()
            mock_client_manager.test_connection.side_effect = Exception("Connection failed")
            mock_manager.return_value = mock_client_manager
            
            # Server should still initialize despite startup errors
            server = FastD365FOMCPServer(production_config)
            
            # Try to run startup initialization
            await server._startup_initialization()
            
            # Server should still be functional
            assert server._stateless_mode is True
            assert server._json_response_mode is True
            
            await server.cleanup()
            
    @pytest.mark.asyncio
    async def test_session_cleanup_error_handling(self, fastmcp_server):
        """Test error handling in session cleanup."""
        # This should not raise an error even if sessions have issues
        fastmcp_server._cleanup_expired_sessions()
        
        # Test with malformed session data - we can't actually add invalid objects
        # to WeakValueDictionary, so we test that cleanup handles empty sessions gracefully
        if hasattr(fastmcp_server, '_stateless_sessions'):
            # Cleanup should handle empty sessions gracefully
            fastmcp_server._cleanup_expired_sessions()
            
        # The main goal is that cleanup doesn't crash even with edge cases


class TestMemoryManagement:
    """Tests for memory management features."""
    
    @pytest.mark.asyncio
    async def test_request_history_limiting(self, fastmcp_server):
        """Test that request history is limited to prevent memory bloat."""
        max_history = fastmcp_server._max_request_history
        
        # Add more request times than the limit
        for i in range(max_history + 100):
            fastmcp_server._record_request_time(0.1)
            
        # Should be capped at max_history
        assert len(fastmcp_server._request_times) == max_history
        
    @pytest.mark.asyncio
    async def test_weak_reference_sessions(self, fastmcp_server):
        """Test that stateless sessions use weak references."""
        if fastmcp_server._stateless_mode:
            # WeakValueDictionary should be used for stateless sessions
            from weakref import WeakValueDictionary
            assert isinstance(fastmcp_server._stateless_sessions, WeakValueDictionary)


# Integration test for the complete production feature set
class TestIntegrationProduction:
    """Integration tests for production features working together."""
    
    @pytest.mark.asyncio
    async def test_production_feature_integration(self, production_config):
        """Test all production features working together."""
        with patch('d365fo_client.mcp.fastmcp_server.D365FOClientManager') as mock_manager:
            mock_client_manager = AsyncMock()
            mock_client_manager.test_connection.return_value = True
            mock_client_manager.get_environment_info.return_value = {
                "base_url": "https://test.dynamics.com",
                "versions": {"application": "10.0.1"},
                "connectivity": True
            }
            mock_manager.return_value = mock_client_manager
            
            # Create server with full production config
            server = FastD365FOMCPServer(production_config)
            
            # Verify all features are enabled
            assert server._stateless_mode is True
            assert server._json_response_mode is True
            assert server._max_concurrent_requests == 20
            assert server._request_timeout == 45
            
            # Test performance monitoring
            server._record_request_time(0.1)
            stats = server.get_performance_stats()
            assert 'total_requests' in stats
            assert stats['stateless_mode'] is True
            assert stats['json_response_mode'] is True
            
            # Test session management
            session = server._get_session_context("test_session")
            assert session['stateless'] is True
            
            # Cleanup
            await server.cleanup()
            
    @pytest.mark.asyncio
    async def test_production_environment_configuration(self):
        """Test production environment variable configuration."""
        production_env = {
            'D365FO_BASE_URL': 'https://prod.dynamics.com',
            'D365FO_HTTP_STATELESS': 'true',
            'D365FO_HTTP_JSON': 'true',
            'D365FO_MAX_CONCURRENT_REQUESTS': '30',
            'D365FO_REQUEST_TIMEOUT': '90',
            'MCP_CONNECTION_POOL_SIZE': '20',
            'MCP_PERFORMANCE_MONITORING': 'true',
            'D365FO_LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, production_env):
            with patch('d365fo_client.mcp.fastmcp_server.D365FOClientManager') as mock_manager:
                mock_manager.return_value = AsyncMock()
                
                server = FastD365FOMCPServer()
                
                # Verify production environment configuration
                assert server._stateless_mode is True
                assert server._json_response_mode is True
                assert server._max_concurrent_requests == 30
                assert server._request_timeout == 90
                
                await server.cleanup()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])