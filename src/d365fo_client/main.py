"""Main module for d365fo-client package with example usage."""

import argparse
import asyncio
import sys

from .client import FOClient, create_client
from .models import FOClientConfig, QueryOptions


async def example_usage():
    """Example usage of the F&O client with label functionality"""
    config = FOClientConfig(
        base_url="https://usnconeboxax1aos.cloud.onebox.dynamics.com",
        use_default_credentials=True,
        verify_ssl=False,
        use_label_cache=True,
        label_cache_expiry_minutes=60,
    )

    async with FOClient(config) as client:
        # Test connections
        print("🔗 Testing connections...")
        if await client.test_connection():
            print("✅ Connected to F&O OData successfully")

        if await client.test_metadata_connection():
            print("✅ Connected to F&O Metadata API successfully")

        # Download metadata
        print("\n📥 Downloading metadata...")
        await client.download_metadata()

        # Search entities
        print("\n🔍 Searching entities...")
        customer_entities = await client.search_entities("customer")
        print(f"Found {len(customer_entities)} customer-related entities")
        for entity in customer_entities[:5]:  # Show first 5
            print(f"  - {entity}")

        # Get entity info with labels
        print("\n📊 Getting entity information...")
        customers_info = await client.get_entity_info_with_labels("Customer")
        if customers_info:
            print(f"Customers entity: {customers_info.name}")
            if customers_info.label_text:
                print(f"Entity label: '{customers_info.label_text}'")
            print(f"Has {len(customers_info.properties)} properties")

            # Show properties with labels
            labeled_props = [p for p in customers_info.properties if p.label_text][:5]
            if labeled_props:
                print("Properties with labels:")
                for prop in labeled_props:
                    print(f"  {prop.name}: '{prop.label_text}'")

        # Test label operations
        print("\n🏷️ Label Operations:")

        # Get specific labels
        test_labels = ["@SYS78125", "@SYS9490", "@GLS63332"]
        print("Fetching specific labels:")
        for label_id in test_labels:
            text = await client.get_label_text(label_id)
            print(f"  {label_id}: '{text}'")

        # Show cache info
        cache_info = client.get_label_cache_info()
        print(f"Label cache: {cache_info}")

        # Get entities with query options
        print("\n📋 Querying entities...")
        query_options = QueryOptions(
            select=["CustomerAccount", "Name", "SalesCurrencyCode"],
            top=5,
            orderby=["Name"],
        )

        try:
            customers = await client.get_entities("Customers", query_options)
            print(f"Retrieved {len(customers.get('value', []))} customers")
            for customer in customers.get("value", [])[:3]:  # Show first 3
                print(f"  - {customer.get('CustomerAccount')}: {customer.get('Name')}")
        except Exception as e:
            print(f"Error querying customers: {e}")

        # Search and call actions
        print("\n⚡ Searching actions...")
        calc_actions = await client.search_actions("calculate")
        print(f"Found {len(calc_actions)} calculation actions")
        for action in calc_actions[:5]:  # Show first 5
            print(f"  - {action}")

        print("\n🔧 Calling actions...")

        # Use the new dedicated methods for version information
        print("Getting version information using dedicated methods...")
        try:
            app_version = await client.get_application_version()
            print(f"Application Version: {app_version}")
        except Exception as e:
            print(f"Error getting application version: {e}")

        try:
            platform_build_version = await client.get_platform_build_version()
            print(f"Platform Build Version: {platform_build_version}")
        except Exception as e:
            print(f"Error getting platform build version: {e}")

        try:
            app_build_version = await client.get_application_build_version()
            print(f"Application Build Version: {app_build_version}")
        except Exception as e:
            print(f"Error getting application build version: {e}")

        # Call other actions using generic call_action
        entity_actions = {
            "DocumentRoutingClientApps": ["GetPlatformVersion"],
        }

        for entity in entity_actions:
            for action in entity_actions[entity]:
                print(f"Calling action '{action}' on entity '{entity}'...")
                result = await client.call_action(action, entity_name=entity)
                print(f"Action '{action}' result: {result}")

        # New Metadata APIs demonstration
        print("\n🆕 New Metadata APIs:")

        # Data Entities API
        print("\n📊 Data Entities API:")
        data_entities = await client.search_data_entities(
            "customer", entity_category="Master"
        )
        print(f"Found {len(data_entities)} customer Master data entities")
        if data_entities:
            entity = data_entities[0]
            print(f"  Example: {entity.name} -> {entity.public_collection_name}")
            print(f"    Category: {entity.entity_category}")
            print(f"    Label: {entity.label_text or entity.label_id}")

        # Public Entities API
        print("\n📋 Public Entities API:")
        public_entities = await client.search_public_entities("customer")
        print(f"Found {len(public_entities)} customer public entities")
        if public_entities:
            # Get detailed info for first entity
            entity_detail = await client.get_public_entity_info(public_entities[0].name)
            if entity_detail:
                print(
                    f"  {entity_detail.name}: {len(entity_detail.properties)} properties"
                )
                key_props = [p.name for p in entity_detail.properties if p.is_key]
                print(f"    Keys: {', '.join(key_props)}")

        # Public Enumerations API
        print("\n🔢 Public Enumerations API:")
        enumerations = await client.search_public_enumerations("payment")
        print(f"Found {len(enumerations)} payment-related enumerations")
        if enumerations:
            # Get detailed info for first enumeration
            enum_detail = await client.get_public_enumeration_info(enumerations[0].name)
            if enum_detail:
                print(f"  {enum_detail.name}: {len(enum_detail.members)} values")
                print(f"    Label: {enum_detail.label_text or enum_detail.label_id}")
                if enum_detail.members:
                    print(
                        f"    Sample values: {', '.join([f'{m.name}={m.value}' for m in enum_detail.members[:3]])}"
                    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the enhanced argument parser with all CLI commands."""
    from . import __author__, __email__, __version__

    parser = argparse.ArgumentParser(
        description="Microsoft Dynamics 365 Finance & Operations Client",
        prog="d365fo-client",
    )

    # Global options (available for all commands)
    parser.add_argument(
        "--version",
        action="version",
        version=f"d365fo-client {__version__} by {__author__} ({__email__})",
    )
    parser.add_argument("--base-url", help="D365 F&O environment URL")
    parser.add_argument(
        "--auth-mode",
        choices=["default", "explicit", "interactive"],
        default="default",
        help="Authentication mode (default: default)",
    )
    parser.add_argument("--client-id", help="Azure AD client ID")
    parser.add_argument("--client-secret", help="Azure AD client secret")
    parser.add_argument("--tenant-id", help="Azure AD tenant ID")
    parser.add_argument(
        "--verify-ssl", type=bool, default=True, help="SSL verification (default: true)"
    )
    parser.add_argument(
        "--output",
        choices=["json", "table", "csv", "yaml"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-essential output"
    )
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--profile", help="Configuration profile to use")
    parser.add_argument(
        "--label-cache",
        type=bool,
        default=True,
        help="Enable label caching (default: true)",
    )
    parser.add_argument(
        "--label-expiry",
        type=int,
        default=60,
        help="Label cache expiry in minutes (default: 60)",
    )

    # Legacy option for backward compatibility
    parser.add_argument(
        "--demo", action="store_true", help="Run the demo/example usage"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command subparsers
    _add_test_command(subparsers)
    _add_version_command(subparsers)
    _add_metadata_commands(subparsers)
    _add_entity_commands(subparsers)
    _add_action_commands(subparsers)
    _add_config_commands(subparsers)

    return parser


def _add_test_command(subparsers) -> None:
    """Add test connectivity command."""
    test_parser = subparsers.add_parser(
        "test", help="Test connectivity to D365 F&O environment"
    )
    test_parser.add_argument(
        "--odata-only", action="store_true", help="Test only OData API connectivity"
    )
    test_parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Test only Metadata API connectivity",
    )
    test_parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Connection timeout in seconds (default: 30)",
    )


def _add_version_command(subparsers) -> None:
    """Add version information command."""
    version_parser = subparsers.add_parser(
        "version", help="Get environment version information"
    )
    version_parser.add_argument(
        "--application", action="store_true", help="Get application version"
    )
    version_parser.add_argument(
        "--platform", action="store_true", help="Get platform build version"
    )
    version_parser.add_argument(
        "--build", action="store_true", help="Get application build version"
    )
    version_parser.add_argument(
        "--all", action="store_true", help="Get all version information"
    )


def _add_metadata_commands(subparsers) -> None:
    """Add metadata operation commands."""
    metadata_parser = subparsers.add_parser("metadata", help="Metadata operations")
    metadata_subs = metadata_parser.add_subparsers(
        dest="metadata_subcommand", help="Metadata subcommands"
    )

    # sync subcommand
    sync_parser = metadata_subs.add_parser("sync", help="Sync metadata to cache")
    sync_parser.add_argument(
        "--force", action="store_true", help="Force refresh of metadata cache"
    )

    # search subcommand
    search_parser = metadata_subs.add_parser(
        "search", help="Search metadata by pattern"
    )
    search_parser.add_argument("pattern", help="Search pattern")
    search_parser.add_argument(
        "--type",
        choices=["entities", "actions", "all"],
        default="entities",
        help="Type of metadata to search (default: entities)",
    )
    search_parser.add_argument("--limit", type=int, help="Maximum number of results")

    # info subcommand
    info_parser = metadata_subs.add_parser("info", help="Get entity metadata details")
    info_parser.add_argument("entity_name", help="Entity name")
    info_parser.add_argument(
        "--properties", action="store_true", help="Include property details"
    )
    info_parser.add_argument(
        "--keys", action="store_true", help="Include key information"
    )
    info_parser.add_argument(
        "--labels", action="store_true", help="Include label information"
    )


def _add_entity_commands(subparsers) -> None:
    """Add entity operation commands."""
    entity_parser = subparsers.add_parser("entity", help="Entity operations")
    entity_subs = entity_parser.add_subparsers(
        dest="entity_subcommand", help="Entity subcommands"
    )

    # get subcommand
    get_parser = entity_subs.add_parser("get", help="Get entity data")
    get_parser.add_argument("entity_name", help="Entity name")
    get_parser.add_argument(
        "key", nargs="?", help="Entity key (optional, for single record)"
    )
    get_parser.add_argument("--select", help="Fields to select (comma-separated)")
    get_parser.add_argument("--filter", help="OData filter expression")
    get_parser.add_argument("--top", type=int, help="Maximum number of records")
    get_parser.add_argument("--orderby", help="Order by fields (comma-separated)")

    # create subcommand
    create_parser = entity_subs.add_parser("create", help="Create entity record")
    create_parser.add_argument("entity_name", help="Entity name")
    create_parser.add_argument("--data", help="Entity data as JSON string")
    create_parser.add_argument(
        "--file", help="Path to JSON file containing entity data"
    )

    # update subcommand
    update_parser = entity_subs.add_parser("update", help="Update entity record")
    update_parser.add_argument("entity_name", help="Entity name")
    update_parser.add_argument("key", help="Entity key")
    update_parser.add_argument("--data", help="Entity data as JSON string")
    update_parser.add_argument(
        "--file", help="Path to JSON file containing entity data"
    )

    # delete subcommand
    delete_parser = entity_subs.add_parser("delete", help="Delete entity record")
    delete_parser.add_argument("entity_name", help="Entity name")
    delete_parser.add_argument("key", help="Entity key")
    delete_parser.add_argument(
        "--confirm", action="store_true", help="Skip confirmation prompt"
    )


def _add_action_commands(subparsers) -> None:
    """Add action operation commands."""
    action_parser = subparsers.add_parser("action", help="Action operations")
    action_subs = action_parser.add_subparsers(
        dest="action_subcommand", help="Action subcommands"
    )

    # list subcommand
    list_parser = action_subs.add_parser("list", help="List available actions")
    list_parser.add_argument(
        "pattern", nargs="?", default="", help="Search pattern (optional)"
    )
    list_parser.add_argument("--entity", help="Filter actions for specific entity")

    # call subcommand
    call_parser = action_subs.add_parser("call", help="Call OData action")
    call_parser.add_argument("action_name", help="Action name")
    call_parser.add_argument(
        "--entity", help="Entity name (if action is entity-specific)"
    )
    call_parser.add_argument("--parameters", help="Action parameters as JSON string")


def _add_config_commands(subparsers) -> None:
    """Add configuration management commands."""
    config_parser = subparsers.add_parser(
        "config", help="Manage configuration profiles"
    )
    config_subs = config_parser.add_subparsers(
        dest="config_subcommand", help="Configuration subcommands"
    )

    # list subcommand
    config_subs.add_parser("list", help="List all configuration profiles")

    # show subcommand
    show_parser = config_subs.add_parser("show", help="Show profile configuration")
    show_parser.add_argument("profile_name", help="Profile name")

    # create subcommand
    create_parser = config_subs.add_parser("create", help="Create new profile")
    create_parser.add_argument("profile_name", help="Profile name")
    create_parser.add_argument(
        "--base-url", required=True, help="D365 F&O environment URL"
    )
    create_parser.add_argument(
        "--auth-mode",
        choices=["default", "explicit", "interactive"],
        default="default",
        help="Authentication mode",
    )
    create_parser.add_argument("--client-id", help="Azure AD client ID")
    create_parser.add_argument("--client-secret", help="Azure AD client secret")
    create_parser.add_argument("--tenant-id", help="Azure AD tenant ID")
    create_parser.add_argument(
        "--verify-ssl", type=bool, default=True, help="SSL verification"
    )
    create_parser.add_argument(
        "--output-format",
        choices=["json", "table", "csv", "yaml"],
        default="table",
        help="Default output format",
    )
    create_parser.add_argument(
        "--label-cache", type=bool, default=True, help="Enable label caching"
    )
    create_parser.add_argument(
        "--label-expiry", type=int, default=60, help="Label cache expiry in minutes"
    )
    create_parser.add_argument("--language", default="en-US", help="Language code")

    # update subcommand (placeholder)
    update_parser = config_subs.add_parser("update", help="Update existing profile")
    update_parser.add_argument("profile_name", help="Profile name")

    # delete subcommand
    delete_parser = config_subs.add_parser("delete", help="Delete profile")
    delete_parser.add_argument("profile_name", help="Profile name")

    # set-default subcommand
    default_parser = config_subs.add_parser("set-default", help="Set default profile")
    default_parser.add_argument("profile_name", help="Profile name")


def main() -> None:
    """Enhanced main entry point with CLI support."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Handle legacy demo mode or no arguments
    if (
        args.demo
        or (not hasattr(args, "command") or not args.command)
        and len(sys.argv) == 1
    ):
        # Run demo if --demo specified or no arguments provided
        print("Microsoft Dynamics 365 Finance & Operations Client")
        print("=" * 50)

        try:
            asyncio.run(example_usage())
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
        except Exception as e:
            print(f"\n\nError: {e}")
        return

    # If no command specified but other arguments provided, show help
    if not hasattr(args, "command") or not args.command:
        parser.print_help()
        return

    # Create and run CLI manager
    from .cli import CLIManager

    cli_manager = CLIManager()

    try:
        exit_code = asyncio.run(cli_manager.execute_command(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        else:
            print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
