"""JSON Service Examples for d365fo-client

This module demonstrates how to use the JSON service functionality to call
D365 F&O JSON services using the /api/services endpoint pattern.
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta

from d365fo_client import FOClient
from d365fo_client.models import FOClientConfig, JsonServiceRequest


async def basic_json_service_example():
    """Example: Basic JSON service call without parameters."""
    
    # Configure client
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("=== Basic JSON Service Call Example ===")
        
        # Call GetAxSqlExecuting (no parameters required)
        response = await client.post_json_service(
            service_group="SysSqlDiagnosticService",
            service_name="SysSqlDiagnosticServiceOperations",
            operation_name="GetAxSqlExecuting"
        )
        
        if response.success:
            print(f"✓ Service call successful (HTTP {response.status_code})")
            print(f"  Found {len(response.data)} executing SQL statements")
            
            # Show first few results if any
            if response.data and len(response.data) > 0:
                print("  Sample executing statements:")
                for i, stmt in enumerate(response.data[:3]):
                    print(f"    {i+1}. Session: {stmt.get('session_id', 'N/A')}")
        else:
            print(f"✗ Service call failed: {response.error_message}")


async def json_service_with_parameters_example():
    """Example: JSON service call with parameters."""
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("\n=== JSON Service with Parameters Example ===")
        
        # Get SQL resource stats for the last 10 minutes
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=10)
        
        parameters = {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
        
        response = await client.post_json_service(
            service_group="SysSqlDiagnosticService",
            service_name="SysSqlDiagnosticServiceOperations",
            operation_name="GetAxSqlResourceStats",
            parameters=parameters
        )
        
        if response.success:
            print(f"✓ Resource stats retrieved (HTTP {response.status_code})")
            print(f"  Found {len(response.data)} resource statistics records")
            print(f"  Time range: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
            
            # Calculate total duration if data available
            if response.data:
                total_duration = sum(float(record.get('duration_ms', 0)) for record in response.data)
                print(f"  Total execution time: {total_duration:.2f}ms")
        else:
            print(f"✗ Service call failed: {response.error_message}")


async def json_service_request_object_example():
    """Example: Using JsonServiceRequest object."""
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("\n=== JsonServiceRequest Object Example ===")
        
        # Create service request object
        request = JsonServiceRequest(
            service_group="SysSqlDiagnosticService",
            service_name="SysSqlDiagnosticServiceOperations",
            operation_name="GetAxSqlBlocking"
        )
        
        print(f"  Service endpoint: {request.get_endpoint_path()}")
        
        # Call service using request object
        response = await client.call_json_service(request)
        
        if response.success:
            print(f"✓ Blocking info retrieved (HTTP {response.status_code})")
            print(f"  Found {len(response.data)} blocking situations")
            
            if response.data:
                print("  Active blocking sessions:")
                for block in response.data[:3]:  # Show first 3
                    blocker = block.get('blocking_session_id', 'N/A')
                    blocked = block.get('blocked_session_id', 'N/A')
                    print(f"    Session {blocker} blocking session {blocked}")
        else:
            print(f"✗ Service call failed: {response.error_message}")


async def multiple_sql_diagnostic_operations_example():
    """Example: Multiple SQL diagnostic operations."""
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("\n=== Multiple SQL Diagnostic Operations Example ===")
        
        operations = [
            ("GetAxSqlExecuting", "Currently executing SQL statements"),
            ("GetAxSqlBlocking", "SQL blocking situations"),
            ("GetAxSqlLockInfo", "SQL lock information"),
            ("GetAxSqlDisabledIndexes", "Disabled database indexes"),
        ]
        
        for operation_name, description in operations:
            try:
                response = await client.post_json_service(
                    service_group="SysSqlDiagnosticService",
                    service_name="SysSqlDiagnosticServiceOperations",
                    operation_name=operation_name
                )
                
                if response.success:
                    count = len(response.data) if isinstance(response.data, list) else 1
                    print(f"  ✓ {operation_name}: {count} records ({description})")
                else:
                    print(f"  ✗ {operation_name}: Failed - {response.error_message}")
                    
            except Exception as e:
                print(f"  ✗ {operation_name}: Exception - {e}")


async def custom_service_example():
    """Example: Calling a custom/different service (template)."""
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("\n=== Custom Service Example (Template) ===")
        
        # Template for calling other JSON services
        # Replace these with actual service details
        service_group = "YourServiceGroup"
        service_name = "YourServiceName"  
        operation_name = "YourOperationName"
        
        # Optional parameters
        parameters = {
            "parameter1": "value1",
            "parameter2": 12345,
            "parameter3": True
        }
        
        print(f"  Service: {service_group}/{service_name}/{operation_name}")
        print(f"  Endpoint: /api/services/{service_group}/{service_name}/{operation_name}")
        
        # Note: This will fail with the template values - replace with real service details
        try:
            response = await client.post_json_service(
                service_group=service_group,
                service_name=service_name,
                operation_name=operation_name,
                parameters=parameters
            )
            
            if response.success:
                print(f"  ✓ Custom service call successful (HTTP {response.status_code})")
                print(f"  Response data type: {type(response.data)}")
            else:
                print(f"  ✗ Custom service call failed: {response.error_message}")
                
        except Exception as e:
            print(f"  ✗ Custom service exception: {e}")
        
        print("  Note: Replace service details with actual values for your custom service")


async def error_handling_example():
    """Example: Error handling patterns."""
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("\n=== Error Handling Example ===")
        
        # Test with non-existent operation
        response = await client.post_json_service(
            service_group="SysSqlDiagnosticService",
            service_name="SysSqlDiagnosticServiceOperations",
            operation_name="NonExistentOperation"
        )
        
        print("  Testing error handling with invalid operation:")
        if response.success:
            print("  ✗ Unexpected: Call should have failed")
        else:
            print(f"  ✓ Expected failure (HTTP {response.status_code})")
            print(f"  Error message: {response.error_message}")
            
        # Test with completely invalid service
        response = await client.post_json_service(
            service_group="InvalidService",
            service_name="InvalidOperations", 
            operation_name="InvalidOperation"
        )
        
        print("  Testing error handling with invalid service:")
        if response.success:
            print("  ✗ Unexpected: Call should have failed")
        else:
            print(f"  ✓ Expected failure (HTTP {response.status_code})")
            print(f"  Error message: {response.error_message}")


async def performance_example():
    """Example: Performance monitoring of JSON service calls."""
    
    config = FOClientConfig(
        base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
        verify_ssl=False,
    )

    async with FOClient(config) as client:
        print("\n=== Performance Monitoring Example ===")
        
        import time
        
        operations = [
            "GetAxSqlExecuting",
            "GetAxSqlBlocking",
            "GetAxSqlLockInfo",
        ]
        
        performance_results = []
        
        for operation in operations:
            start_time = time.time()
            
            response = await client.post_json_service(
                service_group="SysSqlDiagnosticService",
                service_name="SysSqlDiagnosticServiceOperations",
                operation_name=operation
            )
            
            duration = time.time() - start_time
            
            result = {
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "success": response.success,
                "status_code": response.status_code,
                "record_count": len(response.data) if isinstance(response.data, list) else 0
            }
            
            performance_results.append(result)
            
            print(f"  {operation}: {result['duration_ms']}ms, "
                  f"{result['record_count']} records, "
                  f"HTTP {result['status_code']}")
        
        # Summary
        total_time = sum(r['duration_ms'] for r in performance_results)
        avg_time = total_time / len(performance_results)
        
        print(f"  Summary: {len(operations)} operations in {total_time:.2f}ms "
              f"(avg: {avg_time:.2f}ms)")


async def main():
    """Run all JSON service examples."""
    print("D365 F&O JSON Service Examples")
    print("=" * 50)
    
    examples = [
        basic_json_service_example,
        json_service_with_parameters_example,
        json_service_request_object_example,
        multiple_sql_diagnostic_operations_example,
        custom_service_example,
        error_handling_example,
        performance_example,
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\n✗ Example {example.__name__} failed: {e}")
        
    print("\n" + "=" * 50)
    print("Examples completed. Check output above for results.")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())