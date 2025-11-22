"""Performance tests against sandbox environment.

These tests validate performance characteristics against actual D365 F&O sandbox environment,
testing real network latency, throughput, and system behavior under load.
"""

import asyncio
import time
from typing import Any, Dict, List

import pytest
import pytest_asyncio

from d365fo_client import FOClient
from d365fo_client.models import QueryOptions

from . import skip_if_not_level


@skip_if_not_level("sandbox")
class TestSandboxConnectionPerformance:
    """Test connection performance characteristics against sandbox."""

    @pytest.mark.asyncio
    async def test_connection_establishment_time(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test time required to establish connections."""
        operations = [
            ("test_connection", sandbox_client.test_connection),
            ("test_metadata_connection", sandbox_client.test_metadata_connection),
        ]

        for name, operation in operations:
            times = []

            # Test multiple connection attempts
            for _ in range(3):
                start_time = time.time()
                result = await operation()
                duration = time.time() - start_time

                assert result is True
                times.append(duration)

            avg_time = sum(times) / len(times)
            performance_metrics["timings"][f"connection_{name}_avg"] = avg_time

            # Connection should establish within reasonable time
            assert avg_time < 10.0, f"Connection {name} too slow: {avg_time}s average"

    @pytest.mark.asyncio
    async def test_authentication_performance(self, performance_metrics):
        """Test authentication performance with fresh clients."""
        import os

        from d365fo_client import FOClientConfig

        if not os.getenv("D365FO_SANDBOX_BASE_URL"):
            pytest.skip("Sandbox URL not configured")

        config = FOClientConfig(
            base_url=os.getenv("D365FO_SANDBOX_BASE_URL"),
            credential_source=None,  # Use Azure Default Credentials
            verify_ssl=False,
            timeout=60,
        )

        auth_times = []

        # Test authentication with fresh clients
        for _ in range(2):
            start_time = time.time()

            async with FOClient(config) as client:
                # First operation triggers authentication
                await client.test_connection()

            duration = time.time() - start_time
            auth_times.append(duration)

        avg_auth_time = sum(auth_times) / len(auth_times)
        performance_metrics["timings"]["authentication_avg"] = avg_auth_time

        # Authentication should complete within reasonable time
        assert (
            avg_auth_time < 30.0
        ), f"Authentication too slow: {avg_auth_time}s average"

    @pytest.mark.asyncio
    async def test_connection_reuse_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance benefits of connection reuse."""
        operations = [
            sandbox_client.test_connection,
            sandbox_client.get_application_version,
            sandbox_client.test_connection,
        ]

        start_time = time.time()

        # Execute operations on same client (reusing connection)
        for operation in operations:
            await operation()

        total_duration = time.time() - start_time
        performance_metrics["timings"]["connection_reuse_total"] = total_duration

        # Multiple operations should complete quickly with connection reuse
        assert total_duration < 15.0, f"Connection reuse too slow: {total_duration}s"


@skip_if_not_level("sandbox")
class TestSandboxDataOperationPerformance:
    """Test data operation performance against sandbox."""

    @pytest.mark.asyncio
    async def test_simple_query_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance of simple data queries."""
        entity_tests = [
            ("Companies", QueryOptions(top=1)),
            ("Companies", QueryOptions(top=5)),
            ("LegalEntities", QueryOptions(top=1)),
        ]

        for entity, options in entity_tests:
            times = []

            # Run multiple iterations
            for _ in range(3):
                start_time = time.time()

                try:
                    result = await sandbox_client.get_entities(entity, options)
                    duration = time.time() - start_time

                    assert "value" in result
                    times.append(duration)

                except Exception:
                    # Entity might not be available
                    continue

            if times:
                avg_time = sum(times) / len(times)
                performance_metrics["timings"][
                    f"query_{entity}_top{options.top}_avg"
                ] = avg_time

                # Simple queries should be fast
                assert avg_time < 10.0, f"Query {entity} too slow: {avg_time}s average"

    @pytest.mark.asyncio
    async def test_large_dataset_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance with larger datasets."""
        dataset_sizes = [10, 50, 100]

        for size in dataset_sizes:
            start_time = time.time()

            try:
                result = await sandbox_client.get_entities(
                    "Companies", QueryOptions(top=size)
                )

                duration = time.time() - start_time
                actual_count = len(result["value"]) if "value" in result else 0

                performance_metrics["timings"][f"large_dataset_top{size}"] = duration
                performance_metrics["call_counts"][
                    f"large_dataset_top{size}_actual"
                ] = actual_count

                # Performance should scale reasonably
                assert (
                    duration < 30.0
                ), f"Large dataset query (top={size}) too slow: {duration}s"

            except Exception as e:
                performance_metrics["errors"].append(
                    {"operation": f"large_dataset_top{size}", "error": str(e)}
                )

    @pytest.mark.asyncio
    async def test_pagination_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test pagination performance characteristics."""
        page_size = 10
        max_pages = 3

        page_times = []

        for page in range(max_pages):
            start_time = time.time()

            try:
                result = await sandbox_client.get_entities(
                    "Companies", QueryOptions(top=page_size, skip=page * page_size)
                )

                duration = time.time() - start_time
                page_times.append(duration)

                if not result.get("value"):
                    break  # No more data

            except Exception:
                break

        if page_times:
            avg_page_time = sum(page_times) / len(page_times)
            performance_metrics["timings"]["pagination_avg_per_page"] = avg_page_time

            # Pagination should maintain consistent performance
            assert (
                avg_page_time < 10.0
            ), f"Pagination too slow: {avg_page_time}s per page"

            # Performance shouldn't degrade significantly across pages
            if len(page_times) > 1:
                first_page_time = page_times[0]
                last_page_time = page_times[-1]
                degradation_ratio = last_page_time / first_page_time

                assert (
                    degradation_ratio < 3.0
                ), f"Pagination performance degraded significantly: {degradation_ratio}x"

    @pytest.mark.asyncio
    async def test_entity_by_key_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance of entity retrieval by key."""
        # First get a valid key
        companies = await sandbox_client.get_entities("Companies", QueryOptions(top=1))

        if companies.get("value"):
            company_id = companies["value"][0]["DataArea"]

            times = []
            for _ in range(3):
                start_time = time.time()

                company = await sandbox_client.get_entity("Companies", company_id)

                duration = time.time() - start_time
                times.append(duration)

                assert company["DataArea"] == company_id

            avg_time = sum(times) / len(times)
            performance_metrics["timings"]["entity_by_key_avg"] = avg_time

            # Key-based retrieval should be fast
            assert (
                avg_time < 5.0
            ), f"Entity by key retrieval too slow: {avg_time}s average"


@skip_if_not_level("sandbox")
class TestSandboxConcurrentPerformance:
    """Test concurrent operation performance against sandbox."""

    @pytest.mark.asyncio
    async def test_concurrent_simple_operations(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance of concurrent simple operations."""
        task_count = 5

        # Create concurrent tasks
        tasks = [
            sandbox_client.test_connection(),
            sandbox_client.get_application_version(),
            sandbox_client.test_metadata_connection(),
            sandbox_client.get_entities("Companies", QueryOptions(top=1)),
            sandbox_client.get_entities("LegalEntities", QueryOptions(top=1)),
        ]

        start_time = time.time()

        # Execute concurrently
        results = await asyncio.gather(*tasks[:task_count], return_exceptions=True)

        total_duration = time.time() - start_time
        performance_metrics["timings"]["concurrent_simple_total"] = total_duration

        # Count successful operations
        successful = sum(1 for r in results if not isinstance(r, Exception))
        performance_metrics["call_counts"]["concurrent_simple_successful"] = successful

        # Concurrent operations should complete reasonably quickly
        assert (
            total_duration < 20.0
        ), f"Concurrent operations too slow: {total_duration}s"

        # Most operations should succeed
        success_rate = successful / len(results)
        assert (
            success_rate >= 0.6
        ), f"Low success rate in concurrent operations: {success_rate}"

    @pytest.mark.asyncio
    async def test_concurrent_data_queries(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance of concurrent data queries."""
        # Create multiple concurrent data queries
        tasks = [
            sandbox_client.get_entities("Companies", QueryOptions(top=5)),
            sandbox_client.get_entities("Companies", QueryOptions(top=3, skip=3)),
            sandbox_client.get_entities("LegalEntities", QueryOptions(top=2)),
        ]

        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_duration = time.time() - start_time
        performance_metrics["timings"]["concurrent_queries_total"] = total_duration

        # Analyze results
        successful_results = [
            r for r in results if not isinstance(r, Exception) and "value" in r
        ]
        total_records = sum(len(r["value"]) for r in successful_results)

        performance_metrics["call_counts"][
            "concurrent_queries_total_records"
        ] = total_records

        # Concurrent queries should complete efficiently
        assert total_duration < 25.0, f"Concurrent queries too slow: {total_duration}s"

        # Should get some data
        assert total_records > 0, "No data retrieved from concurrent queries"

    @pytest.mark.asyncio
    async def test_high_concurrency_stress(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test system behavior under higher concurrency."""
        concurrency_level = 10

        # Create many concurrent lightweight operations
        tasks = [sandbox_client.test_connection() for _ in range(concurrency_level)]

        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_duration = time.time() - start_time
        performance_metrics["timings"]["high_concurrency_total"] = total_duration

        # Analyze results
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful

        performance_metrics["call_counts"]["high_concurrency_successful"] = successful
        performance_metrics["call_counts"]["high_concurrency_failed"] = failed

        # High concurrency should still work reasonably
        assert (
            total_duration < 60.0
        ), f"High concurrency took too long: {total_duration}s"

        # Most operations should succeed (allowing for some failures under stress)
        success_rate = successful / len(results)
        assert (
            success_rate >= 0.5
        ), f"High concurrency success rate too low: {success_rate}"


@skip_if_not_level("sandbox")
class TestSandboxMetadataPerformance:
    """Test metadata operation performance against sandbox."""

    @pytest.mark.asyncio
    async def test_metadata_download_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test metadata download performance."""
        # Test cold download (forced refresh)
        start_time = time.time()
        result = await sandbox_client.download_metadata(force_refresh=True)
        cold_duration = time.time() - start_time

        assert result is True
        performance_metrics["timings"]["metadata_download_cold"] = cold_duration

        # Test warm download (use cache)
        start_time = time.time()
        result = await sandbox_client.download_metadata(force_refresh=False)
        warm_duration = time.time() - start_time

        assert result is True
        performance_metrics["timings"]["metadata_download_warm"] = warm_duration

        # Metadata operations should complete in reasonable time
        assert (
            cold_duration < 500.0
        ), f"Cold metadata download too slow: {cold_duration}s"
        assert (
            warm_duration < 30.0
        ), f"Warm metadata download too slow: {warm_duration}s"

    @pytest.mark.asyncio
    async def test_metadata_query_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test metadata query performance."""
        # Ensure metadata is available
        await sandbox_client.download_metadata()

        operations = [
            (
                "data_entities",
                lambda: sandbox_client.get_data_entities(QueryOptions(top=20)),
            ),
            (
                "public_entities",
                lambda: sandbox_client.get_public_entities(QueryOptions(top=20)),
            ),
            (
                "public_enumerations",
                lambda: sandbox_client.get_public_enumerations(QueryOptions(top=10)),
            ),
        ]

        for name, operation in operations:
            times = []

            # Run multiple iterations
            for _ in range(2):
                start_time = time.time()

                try:
                    result = await operation()
                    duration = time.time() - start_time

                    times.append(duration)

                    # Validate we got results
                    assert "value" in result
                    assert isinstance(result["value"], list)

                except Exception as e:
                    performance_metrics["errors"].append(
                        {"operation": f"metadata_{name}", "error": str(e)}
                    )
                    continue

            if times:
                avg_time = sum(times) / len(times)
                performance_metrics["timings"][f"metadata_{name}_avg"] = avg_time

                # Metadata queries should be reasonably fast
                assert (
                    avg_time < 15.0
                ), f"Metadata {name} query too slow: {avg_time}s average"

    @pytest.mark.asyncio
    async def test_entity_search_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test entity search performance."""
        # Ensure metadata is available
        await sandbox_client.download_metadata()

        search_terms = ["Customer", "Company", "Legal", "Number"]

        search_times = []

        for term in search_terms:
            start_time = time.time()

            try:
                entities = await sandbox_client.search_entities(term)
                duration = time.time() - start_time

                search_times.append(duration)

                # Validate search results
                assert isinstance(entities, list)

            except Exception:
                # Search might fail for some terms
                continue

        if search_times:
            avg_search_time = sum(search_times) / len(search_times)
            performance_metrics["timings"]["entity_search_avg"] = avg_search_time

            # Entity search should be fast (metadata is already loaded)
            assert (
                avg_search_time < 5.0
            ), f"Entity search too slow: {avg_search_time}s average"


@skip_if_not_level("sandbox")
class TestSandboxVersionMethodPerformance:
    """Test version method performance against sandbox."""

    @pytest.mark.asyncio
    async def test_version_methods_individual_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test individual version method performance."""
        version_methods = [
            ("application_version", sandbox_client.get_application_version),
            ("platform_version", sandbox_client.get_platform_build_version),
            ("application_build_version", sandbox_client.get_application_build_version),
        ]

        for name, method in version_methods:
            times = []

            for _ in range(3):
                start_time = time.time()

                version = await method()
                duration = time.time() - start_time

                times.append(duration)

                # Validate version response
                assert isinstance(version, str)
                assert len(version) > 0

            avg_time = sum(times) / len(times)
            performance_metrics["timings"][f"version_{name}_avg"] = avg_time

            # Version methods should be fast
            assert (
                avg_time < 8.0
            ), f"Version method {name} too slow: {avg_time}s average"

    @pytest.mark.asyncio
    async def test_version_methods_parallel_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test parallel version method performance."""
        start_time = time.time()

        # Call all version methods in parallel
        versions = await asyncio.gather(
            sandbox_client.get_application_version(),
            sandbox_client.get_platform_build_version(),
            sandbox_client.get_application_build_version(),
        )

        parallel_duration = time.time() - start_time
        performance_metrics["timings"]["version_methods_parallel"] = parallel_duration

        # Validate all responses
        for version in versions:
            assert isinstance(version, str)
            assert len(version) > 0

        # Parallel execution should be efficient
        assert (
            parallel_duration < 15.0
        ), f"Parallel version methods too slow: {parallel_duration}s"

        # Should be faster than sequential execution (though not always guaranteed)
        # This is more of a sanity check
        assert parallel_duration < 30.0, "Parallel version methods unreasonably slow"


@skip_if_not_level("sandbox")
class TestSandboxOverallPerformance:
    """Test overall system performance characteristics."""

    @pytest.mark.asyncio
    async def test_typical_workflow_performance(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test performance of a typical user workflow."""
        start_time = time.time()

        # Typical workflow: connection -> version info -> data browsing
        workflow_steps = [
            ("connection_test", sandbox_client.test_connection()),
            ("version_info", sandbox_client.get_application_version()),
            (
                "data_browse",
                sandbox_client.get_entities("Companies", QueryOptions(top=5)),
            ),
            ("metadata_check", sandbox_client.test_metadata_connection()),
        ]

        for step_name, operation in workflow_steps:
            step_start = time.time()

            try:
                await operation
                step_duration = time.time() - step_start
                performance_metrics["timings"][f"workflow_{step_name}"] = step_duration

            except Exception as e:
                performance_metrics["errors"].append(
                    {"operation": f"workflow_{step_name}", "error": str(e)}
                )

        total_workflow_time = time.time() - start_time
        performance_metrics["timings"]["workflow_total"] = total_workflow_time

        # Complete workflow should finish in reasonable time
        assert (
            total_workflow_time < 45.0
        ), f"Typical workflow too slow: {total_workflow_time}s"

    @pytest.mark.asyncio
    async def test_performance_consistency(
        self, sandbox_client: FOClient, performance_metrics
    ):
        """Test that performance remains consistent across multiple runs."""
        operation = lambda: sandbox_client.get_entities(
            "Companies", QueryOptions(top=3)
        )

        run_times = []

        # Run the same operation multiple times
        for i in range(5):
            start_time = time.time()

            try:
                await operation()
                duration = time.time() - start_time
                run_times.append(duration)

            except Exception:
                # Operation might fail, skip this run
                continue

        if len(run_times) >= 3:
            avg_time = sum(run_times) / len(run_times)
            max_time = max(run_times)
            min_time = min(run_times)

            performance_metrics["timings"]["consistency_avg"] = avg_time
            performance_metrics["timings"]["consistency_max"] = max_time
            performance_metrics["timings"]["consistency_min"] = min_time

            # Performance should be reasonably consistent
            variance_ratio = max_time / min_time if min_time > 0 else float("inf")

            # Allow for some variance but not extreme outliers
            assert (
                variance_ratio < 5.0
            ), f"Performance too inconsistent: {variance_ratio}x variance"
            assert avg_time < 10.0, f"Average performance too slow: {avg_time}s"
