"""Example demonstrating profile management functionality."""

import asyncio
import json

from d365fo_client.mcp.server import D365FOMCPServer
from d365fo_client.profile_manager import ProfileManager


async def main():
    """Demonstrate profile management capabilities."""
    print("=== D365FO Profile Management Demo ===\n")

    # Initialize profile manager
    profile_manager = ProfileManager()

    print("1. Creating sample profiles...")

    # Create a production profile
    success = profile_manager.create_profile(
        name="production",
        base_url="https://prod-d365fo.contoso.com",
        auth_mode="client_credentials",
        client_id="your-prod-client-id",
        client_secret="your-prod-client-secret",
        tenant_id="your-tenant-id",
        description="Production environment",
    )
    print(f"   Production profile created: {success}")

    # Create a sandbox profile
    success = profile_manager.create_profile(
        name="sandbox",
        base_url="https://sandbox-d365fo.contoso.com",
        auth_mode="default",
        description="Sandbox environment for testing",
    )
    print(f"   Sandbox profile created: {success}")

    # Create a development profile
    success = profile_manager.create_profile(
        name="development",
        base_url="https://dev-d365fo.contoso.com",
        auth_mode="default",
        use_label_cache=False,  # Disable cache for dev
        timeout=30,
        description="Development environment",
    )
    print(f"   Development profile created: {success}")

    print("\n2. Listing all profiles...")
    profiles = profile_manager.list_profiles()
    for name, profile in profiles.items():
        print(f"   - {name}: {profile.base_url} ({profile.auth_mode})")

    print("\n3. Setting default profile...")
    success = profile_manager.set_default_profile("sandbox")
    print(f"   Default profile set to 'sandbox': {success}")

    default_profile = profile_manager.get_default_profile()
    if default_profile:
        print(f"   Current default: {default_profile.name}")

    print("\n4. Validating profiles...")
    for name in profile_manager.get_profile_names():
        profile = profile_manager.get_profile(name)
        if profile:
            errors = profile_manager.validate_profile(profile)
            status = "✓ Valid" if not errors else f"✗ Errors: {', '.join(errors)}"
            print(f"   {name}: {status}")

    print("\n5. Testing MCP server with profiles...")
    try:
        # Initialize MCP server
        server = D365FOMCPServer()

        # The profile tools will be available through the MCP interface
        profile_tools = server.profile_tools

        # Simulate MCP tool calls
        print("   Testing list profiles tool...")
        result = await profile_tools.execute_list_profiles({})
        response = json.loads(result[0].text)
        print(f"   Found {response['totalCount']} profiles")

        print("   Testing get profile tool...")
        result = await profile_tools.execute_get_profile({"profileName": "sandbox"})
        response = json.loads(result[0].text)
        print(f"   Sandbox profile: {response.get('baseUrl', 'N/A')}")

        print("   Testing profile validation...")
        result = await profile_tools.execute_validate_profile(
            {"profileName": "production"}
        )
        response = json.loads(result[0].text)
        print(f"   Production profile valid: {response['isValid']}")

    except Exception as e:
        print(f"   MCP server test error: {e}")

    print("\n6. Export and import demo...")

    # Export profiles
    export_file = "profiles_backup.yaml"
    success = profile_manager.export_profiles(export_file)
    print(f"   Profiles exported to {export_file}: {success}")

    # Clean up test profiles for demo
    for profile_name in ["production", "sandbox", "development"]:
        success = profile_manager.delete_profile(profile_name)
        print(f"   Deleted {profile_name}: {success}")

    # Import profiles back
    results = profile_manager.import_profiles(export_file, overwrite=True)
    print(f"   Import results: {results}")

    print("\n=== Demo Complete ===")
    print("\nProfile management features:")
    print("• Create, read, update, delete profiles")
    print("• Set and get default profile")
    print("• Validate profile configurations")
    print("• Export/import profiles")
    print("• MCP tools for AI assistant integration")
    print("• Seamless integration with CLI")
    print("\nMCP Tools Available:")
    print("• d365fo_list_profiles")
    print("• d365fo_get_profile")
    print("• d365fo_create_profile")
    print("• d365fo_update_profile")
    print("• d365fo_delete_profile")
    print("• d365fo_set_default_profile")
    print("• d365fo_get_default_profile")
    print("• d365fo_validate_profile")
    print("• d365fo_test_profile_connection")


if __name__ == "__main__":
    asyncio.run(main())
