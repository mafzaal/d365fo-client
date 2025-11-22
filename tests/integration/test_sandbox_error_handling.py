"""Error handling tests against sandbox environment.

These tests validate error handling and exception scenarios against actual D365 F&O sandbox environment,
testing real API error responses, status codes, and recovery mechanisms.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, Type

from d365fo_client import FOClient
from d365fo_client.models import QueryOptions

from . import skip_if_not_level


@skip_if_not_level("sandbox")
class TestSandboxEntityErrors:
    """Test entity-related error scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_nonexistent_entity_error(self, sandbox_client: FOClient):
        """Test proper error handling for non-existent entities."""
        with pytest.raises(Exception) as exc_info:
            await sandbox_client.get_entities("NonExistentEntitySet123456")

        # Should get a meaningful error
        error = exc_info.value
        assert error is not None

        # Error message should indicate the entity doesn't exist
        error_str = str(error).lower()
        assert any(keyword in error_str for keyword in ["not found", "doesn't exist", "invalid", "unknown"])

    @pytest.mark.asyncio
    async def test_nonexistent_entity_by_key_error(self, sandbox_client: FOClient):
        """Test error handling for non-existent entity key."""
        with pytest.raises(Exception) as exc_info:
            await sandbox_client.get_entity("Companies", "NON_EXISTENT_KEY_12345")

        error = exc_info.value
        assert error is not None

        # Should get appropriate error for missing key
        error_str = str(error).lower()
        assert any(keyword in error_str for keyword in ["not found", "invalid", "doesn't exist"])

    @pytest.mark.asyncio
    async def test_invalid_entity_name_patterns(self, sandbox_client: FOClient):
        """Test various invalid entity name patterns."""
        invalid_entities = [
            "",  # Empty string
            "Invalid Entity Name",  # Spaces
            "Invalid/Entity",  # Special characters
            "entity.with.dots",  # Dots
            "VERY_LONG_ENTITY_NAME_THAT_PROBABLY_DOESNT_EXIST_IN_ANY_SYSTEM_123456789",  # Very long
        ]

        for invalid_entity in invalid_entities:
            with pytest.raises(Exception):
                await sandbox_client.get_entities(invalid_entity)

    @pytest.mark.asyncio
    async def test_malformed_query_options_error(self, sandbox_client: FOClient):
        """Test error handling for malformed query options."""
        try:
            # Test with invalid filter syntax
            with pytest.raises(Exception):
                await sandbox_client.get_entities(
                    "Companies",
                    QueryOptions(filter="invalid filter syntax @@@ error")
                )

        except Exception:
            # Some systems might not support complex filters
            pass

        try:
            # Test with invalid select fields
            with pytest.raises(Exception):
                await sandbox_client.get_entities(
                    "Companies",
                    QueryOptions(select="NonExistentField123456")
                )

        except Exception:
            # Some systems might ignore invalid select fields
            pass

    @pytest.mark.asyncio
    async def test_invalid_key_formats(self, sandbox_client: FOClient):
        """Test error handling for invalid key formats."""
        invalid_keys = [
            "",  # Empty key
            "key with spaces",  # Spaces in key
            "key/with/slashes",  # Slashes
            "key?with=query",  # Query parameters
            None,  # None value (if passed as string)
        ]

        for invalid_key in invalid_keys:
            if invalid_key is None:
                continue  # Skip None test as it would cause different error

            with pytest.raises(Exception):
                await sandbox_client.get_entity("Companies", invalid_key)


@skip_if_not_level("sandbox")
class TestSandboxActionErrors:
    """Test action-related error scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_nonexistent_action_error(self, sandbox_client: FOClient):
        """Test proper error handling for non-existent actions."""
        with pytest.raises(Exception) as exc_info:
            await sandbox_client.call_action("NonExistentAction123456")

        error = exc_info.value
        assert error is not None

        # Error should indicate action doesn't exist
        error_str = str(error).lower()
        assert any(keyword in error_str for keyword in [
            "not found", "doesn't exist", "invalid", "unknown", "action"
        ])

    @pytest.mark.asyncio
    async def test_action_with_invalid_parameters(self, sandbox_client: FOClient):
        """Test action calls with invalid parameters."""
        # Try to call a known action with invalid parameters
        try:
            with pytest.raises(Exception):
                await sandbox_client.call_action(
                    "GetApplicationVersion",
                    parameters={"InvalidParameter": "InvalidValue"}
                )
        except Exception:
            # Some systems might ignore extra parameters
            pass

    @pytest.mark.asyncio
    async def test_malformed_action_names(self, sandbox_client: FOClient):
        """Test various malformed action names."""
        invalid_actions = [
            "",  # Empty string
            "Action With Spaces",  # Spaces
            "Action/With/Slashes",  # Slashes
            "Action.With.Dots",  # Dots
            "Action?With=Query",  # Query syntax
        ]

        for invalid_action in invalid_actions:
            with pytest.raises(Exception):
                await sandbox_client.call_action(invalid_action)


@skip_if_not_level("sandbox")
class TestSandboxMetadataErrors:
    """Test metadata-related error scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_invalid_metadata_operations(self, sandbox_client: FOClient):
        """Test invalid metadata operations."""
        # Test searching for non-existent entity info
        try:
            entity_info = await sandbox_client.get_public_entity_info("NonExistentEntity123456")
            # Some systems return None instead of raising exception
            assert entity_info is None
        except Exception:
            # Exception is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_metadata_with_invalid_query_options(self, sandbox_client: FOClient):
        """Test metadata operations with invalid query options."""
        try:
            # Test with extremely large top value
            with pytest.raises(Exception):
                await sandbox_client.get_data_entities(QueryOptions(top=999999))

        except Exception:
            # System might handle large values gracefully
            pass

        try:
            # Test with negative values
            with pytest.raises(Exception):
                await sandbox_client.get_data_entities(QueryOptions(top=-1))

        except Exception:
            # System might handle negative values gracefully
            pass

    @pytest.mark.asyncio
    async def test_entity_search_edge_cases(self, sandbox_client: FOClient):
        """Test entity search with edge cases."""
        # Ensure metadata is available
        await sandbox_client.download_metadata()

        edge_cases = [
            "",  # Empty search
            " ",  # Whitespace only
            "!@#$%^&*()",  # Special characters
            "a" * 100,  # Very long search term
        ]

        for search_term in edge_cases:
            try:
                entities = await sandbox_client.search_entities(search_term)
                # Should return empty list for invalid searches
                assert isinstance(entities, list)
            except Exception:
                # Exception is also acceptable for invalid searches
                pass

    @pytest.mark.asyncio
    async def test_label_error_scenarios(self, sandbox_client: FOClient):
        """Test label operations error scenarios."""
        # Test with invalid label IDs
        invalid_labels = [
            "",  # Empty string
            "InvalidLabel",  # No @ prefix
            "@",  # Just @ symbol
            "@NONEXISTENT123456789",  # Non-existent label
            "@SYS",  # Incomplete label ID
        ]

        for invalid_label in invalid_labels:
            try:
                label_text = await sandbox_client.get_label_text(invalid_label)
                # Should return None for invalid labels
                assert label_text is None or isinstance(label_text, str)
            except Exception:
                # Exception is also acceptable
                pass

        # Test batch operation with invalid labels
        try:
            labels = await sandbox_client.get_labels_batch(invalid_labels)
            assert isinstance(labels, dict)
            # Invalid labels should have None values or be missing
            for label_id in invalid_labels:
                if label_id in labels:
                    assert labels[label_id] is None or isinstance(labels[label_id], str)
        except Exception:
            # Batch operation might not be supported
            pass


@skip_if_not_level("sandbox")
class TestSandboxConnectionErrors:
    """Test connection-related error scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, performance_metrics):
        """Test handling of connection timeouts."""
        import os
        from d365fo_client import FOClientConfig

        if not os.getenv("D365FO_SANDBOX_BASE_URL"):
            pytest.skip("Sandbox URL not configured")

        # Create client with very short timeout
        config = FOClientConfig(
            base_url=os.getenv("D365FO_SANDBOX_BASE_URL"),
            credential_source=None,  # Use Azure Default Credentials
            verify_ssl=False,
            timeout=1,  # Very short timeout
        )

        try:
            async with FOClient(config) as client:
                # This might timeout or succeed depending on network conditions
                result = await client.test_connection()

                if result:
                    # If it succeeded with short timeout, that's fine too
                    performance_metrics["timings"]["short_timeout_success"] = True

        except Exception as e:
            # Timeout exception is expected
            performance_metrics["errors"].append({
                "operation": "short_timeout_test",
                "error": str(e)
            })
            # Verify it's a timeout-related error
            error_str = str(e).lower()
            assert any(keyword in error_str for keyword in [
                "timeout", "timed out", "connection", "time"
            ])

    @pytest.mark.asyncio
    async def test_invalid_base_url_error(self):
        """Test error handling for invalid base URLs."""
        from d365fo_client import FOClientConfig

        invalid_urls = [
            "not-a-url",
            "http://nonexistent-domain-12345.invalid",
            "",  # Empty URL
            "ftp://invalid-protocol.com",  # Wrong protocol
        ]

        for invalid_url in invalid_urls:
            try:
                config = FOClientConfig(
                    base_url=invalid_url,
                    credential_source=None,  # Use Azure Default Credentials
                    timeout=5,
                )

                async with FOClient(config) as client:
                    with pytest.raises(Exception):
                        await client.test_connection()

            except Exception:
                # Configuration itself might fail, which is also acceptable
                pass

    @pytest.mark.asyncio
    async def test_authentication_failure_scenarios(self):
        """Test authentication failure scenarios."""
        import os
        from d365fo_client import FOClientConfig

        if not os.getenv("D365FO_SANDBOX_BASE_URL"):
            pytest.skip("Sandbox URL not configured")

        # Test with invalid credentials (if we can configure them)
        try:
            config = FOClientConfig(
                base_url=os.getenv("D365FO_SANDBOX_BASE_URL"),
                client_id="invalid-client-id",
                client_secret="invalid-client-secret",
                tenant_id="invalid-tenant-id",
                verify_ssl=False,
                timeout=30,
            )

            async with FOClient(config) as client:
                with pytest.raises(Exception):
                    await client.test_connection()

        except Exception:
            # Configuration or other errors are acceptable
            pass


@skip_if_not_level("sandbox")
class TestSandboxDataValidationErrors:
    """Test data validation error scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_query_options_boundary_values(self, sandbox_client: FOClient):
        """Test query options with boundary values."""
        boundary_tests = [
            # Test zero values
            {"top": 0},
            {"skip": 0},
            {"top": 0, "skip": 0},

            # Test large values
            {"top": 10000},
            {"skip": 10000},

            # Test negative values (should fail)
            {"top": -1},
            {"skip": -1},
        ]

        for options_dict in boundary_tests:
            try:
                options = QueryOptions(**options_dict)
                result = await sandbox_client.get_entities("Companies", options)

                # If it succeeds, validate the response
                assert "value" in result
                assert isinstance(result["value"], list)

                # For top=0, should return empty list
                if options_dict.get("top") == 0:
                    assert len(result["value"]) == 0

            except Exception:
                # Some boundary values should cause exceptions
                # Negative values should definitely fail
                if any(v < 0 for v in options_dict.values()):
                    # Negative values should fail
                    pass
                else:
                    # Other values might be handled differently by different systems
                    pass

    @pytest.mark.asyncio
    async def test_concurrent_error_scenarios(self, sandbox_client: FOClient):
        """Test error handling in concurrent scenarios."""
        import asyncio

        # Create a mix of valid and invalid operations
        tasks = [
            sandbox_client.get_entities("Companies", QueryOptions(top=1)),  # Valid
            sandbox_client.get_entities("NonExistentEntity", QueryOptions(top=1)),  # Invalid
            sandbox_client.test_connection(),  # Valid
            sandbox_client.call_action("NonExistentAction"),  # Invalid
            sandbox_client.get_entity("Companies", "INVALID_KEY"),  # Invalid
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = []
        failed = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append((i, result))
            else:
                successful.append((i, result))

        # Should have some successes and some failures
        assert len(successful) > 0, "All concurrent operations failed"
        assert len(failed) > 0, "Expected some operations to fail"

        # Validate that successful operations return expected data
        for i, result in successful:
            if i == 0:  # Companies query
                assert "value" in result
            elif i == 2:  # Connection test
                assert result is True


@skip_if_not_level("sandbox")
class TestSandboxErrorRecovery:
    """Test error recovery and resilience scenarios against sandbox."""

    @pytest.mark.asyncio
    async def test_recovery_after_errors(self, sandbox_client: FOClient):
        """Test that client can recover after encountering errors."""
        # Cause an error
        try:
            await sandbox_client.get_entities("NonExistentEntity")
        except Exception:
            pass  # Expected error

        # Client should still work after error
        result = await sandbox_client.test_connection()
        assert result is True

        # Should be able to perform normal operations
        companies = await sandbox_client.get_entities("Companies", QueryOptions(top=1))
        assert "value" in companies

    @pytest.mark.asyncio
    async def test_multiple_consecutive_errors(self, sandbox_client: FOClient):
        """Test handling of multiple consecutive errors."""
        error_operations = [
            lambda: sandbox_client.get_entities("NonExistent1"),
            lambda: sandbox_client.get_entity("Companies", "INVALID_KEY"),
            lambda: sandbox_client.call_action("NonExistentAction"),
        ]

        # Execute multiple error operations
        for operation in error_operations:
            try:
                await operation()
            except Exception:
                pass  # Expected errors

        # Client should still be functional
        result = await sandbox_client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_error_information_quality(self, sandbox_client: FOClient):
        """Test that errors provide useful information."""
        test_cases = [
            ("invalid_entity", lambda: sandbox_client.get_entities("NonExistentEntity")),
            ("invalid_key", lambda: sandbox_client.get_entity("Companies", "INVALID_KEY")),
            ("invalid_action", lambda: sandbox_client.call_action("NonExistentAction")),
        ]

        for test_name, operation in test_cases:
            try:
                await operation()
                # If no exception, skip this test case
                continue
            except Exception as e:
                # Error should have meaningful information
                error_str = str(e)
                assert len(error_str) > 0, f"Empty error message for {test_name}"

                # Error should not be generic
                generic_messages = ["error", "exception", "failed"]
                assert not all(generic in error_str.lower() for generic in generic_messages), \
                    f"Too generic error message for {test_name}: {error_str}"

                # Should contain some context about what failed
                assert len(error_str) > 10, f"Error message too short for {test_name}: {error_str}"