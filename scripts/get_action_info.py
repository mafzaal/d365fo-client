#!/usr/bin/env python3
"""
Get detailed information for a specific action in D365 Finance & Operations

This script retrieves detailed information for a specific action using
the d365fo-client Python API to provide more comprehensive action details
than what's available through the CLI.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

# Add the src directory to the path to import d365fo_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.exceptions import FOClientError


async def get_action_info(
    action_name: str,
    output_format: str = "table",
    base_url: Optional[str] = None,
    profile: Optional[str] = None,
    verbose: bool = False,
):
    """Get detailed information for a specific action."""

    # Configure client
    if base_url:
        config = FOClientConfig(
            base_url=base_url, use_default_credentials=True, use_label_cache=True
        )
    else:
        # Use environment variables or default configuration
        config = FOClientConfig(
            base_url=os.getenv(
                "D365FO_BASE_URL", "https://usnconeboxax1aos.cloud.onebox.dynamics.com"
            ),
            use_default_credentials=True,
            use_label_cache=True,
        )

    try:
        async with FOClient(config=config) as client:
            if verbose:
                print(f"Getting information for action: '{action_name}'")

            # Get action info from metadata
            action_info = await client.get_action_info(action_name)

            if not action_info:
                print(f"Action '{action_name}' not found", file=sys.stderr)
                sys.exit(1)

            # Format output
            if output_format == "json":
                action_dict = {
                    "name": action_info.get("name", action_name),
                    "type": action_info.get("type", "Unknown"),
                    "parameters": action_info.get("parameters", []),
                    "return_type": action_info.get("return_type", "Unknown"),
                    "description": action_info.get("description", ""),
                    "is_bound": action_info.get("is_bound", False),
                    "entity_set": action_info.get("entity_set", ""),
                }
                print(json.dumps(action_dict, indent=2))

            elif output_format == "table":
                print(f"Action: {action_info.get('name', action_name)}")
                print("=" * 50)
                print(f"Type: {action_info.get('type', 'Unknown')}")
                print(f"Bound: {action_info.get('is_bound', False)}")
                print(f"Entity Set: {action_info.get('entity_set', 'N/A')}")
                print(f"Return Type: {action_info.get('return_type', 'Unknown')}")

                description = action_info.get("description", "")
                if description:
                    print(f"Description: {description}")

                parameters = action_info.get("parameters", [])
                if parameters:
                    print("\nParameters:")
                    print(f"{'Name':<20} {'Type':<20} {'Required':<10}")
                    print("-" * 50)
                    for param in parameters:
                        param_name = param.get("name", "Unknown")
                        param_type = param.get("type", "Unknown")
                        required = param.get("required", False)
                        print(f"{param_name:<20} {param_type:<20} {required:<10}")
                else:
                    print("\nNo parameters")

            elif output_format == "csv":
                print("Property,Value")
                print(f"Name,{action_info.get('name', action_name)}")
                print(f"Type,{action_info.get('type', 'Unknown')}")
                print(f"Bound,{action_info.get('is_bound', False)}")
                print(f"EntitySet,{action_info.get('entity_set', 'N/A')}")
                print(f"ReturnType,{action_info.get('return_type', 'Unknown')}")

                parameters = action_info.get("parameters", [])
                if parameters:
                    print("Parameter,Type,Required")
                    for param in parameters:
                        param_name = param.get("name", "Unknown")
                        param_type = param.get("type", "Unknown")
                        required = param.get("required", False)
                        print(f"{param_name},{param_type},{required}")

            else:
                # Default to simple format
                print(f"Action: {action_info.get('name', action_name)}")
                print(f"  Type: {action_info.get('type', 'Unknown')}")
                print(f"  Bound: {action_info.get('is_bound', False)}")
                parameters = action_info.get("parameters", [])
                if parameters:
                    print("  Parameters:")
                    for param in parameters:
                        param_name = param.get("name", "Unknown")
                        param_type = param.get("type", "Unknown")
                        print(f"    {param_name} ({param_type})")

    except FOClientError as e:
        print(f"Error getting action info: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get detailed information for a specific action in D365 Finance & Operations"
    )

    parser.add_argument("action_name", help="Name of the action to get information for")

    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "table", "csv", "list"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument("--base-url", help="D365 F&O environment URL")

    parser.add_argument(
        "--profile", help="Configuration profile to use (not yet implemented)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Run the async function
    asyncio.run(
        get_action_info(
            action_name=args.action_name,
            output_format=args.output,
            base_url=args.base_url,
            profile=args.profile,
            verbose=args.verbose,
        )
    )


if __name__ == "__main__":
    main()
