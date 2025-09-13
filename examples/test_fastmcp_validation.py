#!/usr/bin/env python3
"""
FastMCP Validation Test Script
Comprehensive validation of the FastD365FOMCPServer migration.
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any

def run_mcp_request(request: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """Send an MCP request to the FastMCP server via stdio.
    
    Args:
        request: MCP request dictionary
        timeout: Request timeout in seconds
        
    Returns:
        MCP response dictionary
    """
    # Convert request to JSON
    request_json = json.dumps(request)
    print(f"Sending request: {request_json}")
    
    # Run the FastMCP server with stdio transport using uv directly
    cmd = [
        "uv", "run", "d365fo-fastmcp-server", "--debug"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Send request and get response
        stdout, stderr = process.communicate(input=request_json, timeout=timeout)
        
        print(f"STDERR (first 500 chars): {stderr[:500]}")
        print(f"STDOUT (first 500 chars): {stdout[:500]}")
        
        # Try to parse JSON response from stdout
        lines = stdout.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    response = json.loads(line)
                    return response
                except json.JSONDecodeError:
                    continue
                
        return {"error": "No valid JSON response found", "stdout": stdout[:200], "stderr": stderr[:200]}
        
    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}


def test_tools_list():
    """Test the tools/list MCP method."""
    print("\n=== Testing tools/list ===")
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    response = run_mcp_request(request)
    print(f"Response: {json.dumps(response, indent=2)}")
    
    if "result" in response and "tools" in response["result"]:
        tools = response["result"]["tools"]
        print(f"✅ Found {len(tools)} tools")
        
        # Check for key tools
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "d365fo_test_connection",
            "d365fo_query_entities", 
            "d365fo_search_entities",
            "d365fo_create_entity_record",
            "d365fo_get_label"
        ]
        
        for expected in expected_tools:
            if expected in tool_names:
                print(f"✅ {expected} found")
            else:
                print(f"❌ {expected} missing")
                
        return True
    else:
        print(f"❌ Invalid response format: {response}")
        return False


def test_resources_list():
    """Test the resources/list MCP method."""
    print("\n=== Testing resources/list ===")
    
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "resources/list",
        "params": {}
    }
    
    response = run_mcp_request(request)
    print(f"Response: {json.dumps(response, indent=2)}")
    
    if "result" in response and "resources" in response["result"]:
        resources = response["result"]["resources"]
        print(f"✅ Found {len(resources)} resources")
        
        # Check for key resources
        resource_uris = [res["uri"] for res in resources]
        expected_resources = [
            "d365fo://environment/status",
            "d365fo://metadata/entities",
            "d365fo://database/schema"
        ]
        
        for expected in expected_resources:
            if expected in resource_uris:
                print(f"✅ {expected} found")
            else:
                print(f"❌ {expected} missing")
                
        return True
    else:
        print(f"❌ Invalid response format: {response}")
        return False


def test_prompts_list():
    """Test the prompts/list MCP method."""
    print("\n=== Testing prompts/list ===")
    
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "prompts/list",
        "params": {}
    }
    
    response = run_mcp_request(request)
    print(f"Response: {json.dumps(response, indent=2)}")
    
    if "result" in response and "prompts" in response["result"]:
        prompts = response["result"]["prompts"]
        print(f"✅ Found {len(prompts)} prompts")
        
        # Check for expected prompts
        prompt_names = [prompt["name"] for prompt in prompts]
        expected_prompts = [
            "d365fo_sequence_analysis",
            "d365fo_action_execution"
        ]
        
        for expected in expected_prompts:
            if expected in prompt_names:
                print(f"✅ {expected} found")
            else:
                print(f"❌ {expected} missing")
                
        return True
    else:
        print(f"❌ Invalid response format: {response}")
        return False


def main():
    """Run comprehensive FastMCP validation tests."""
    print("🚀 FastMCP Validation Test Suite")
    print("=================================")
    
    # Test results
    results = []
    
    # Test tools/list
    results.append(("tools/list", test_tools_list()))
    
    # Test resources/list
    results.append(("resources/list", test_resources_list()))
    
    # Test prompts/list
    results.append(("prompts/list", test_prompts_list()))
    
    # Summary
    print("\n=== Test Results Summary ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All FastMCP validation tests PASSED!")
        return 0
    else:
        print("⚠️  Some tests failed - check implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())