#!/usr/bin/env python3
"""
Search for enumerations in D365 Finance & Operations

This script searches for enumerations using the d365fo-client Python API
since enumeration support is not yet available in the CLI.
"""

import asyncio
import argparse
import os
import sys
import json
from typing import Optional

# Add the src directory to the path to import d365fo_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from d365fo_client import FOClient, FOClientConfig
from d365fo_client.exceptions import FOClientError


async def search_enumerations(
    pattern: str = "",
    output_format: str = "table",
    limit: Optional[int] = None,
    base_url: Optional[str] = None,
    profile: Optional[str] = None,
    verbose: bool = False
):
    """Search for enumerations in D365 F&O."""
    
    # Configure client
    if base_url:
        config = FOClientConfig(
            base_url=base_url,
            use_default_credentials=True,
            use_label_cache=True
        )
    else:
        # Use environment variables or default configuration
        config = FOClientConfig(
            base_url=os.getenv('D365FO_BASE_URL', 'https://usnconeboxax1aos.cloud.onebox.dynamics.com'),
            use_default_credentials=True,
            use_label_cache=True
        )
    
    try:
        async with FOClient(config=config) as client:
            if verbose:
                print(f"Searching for enumerations with pattern: '{pattern}'")
            
            # Search for enumerations
            enumerations = await client.search_public_enumerations(pattern)
            
            # Apply limit if specified
            if limit and len(enumerations) > limit:
                enumerations = enumerations[:limit]
            
            if not enumerations:
                print(f"No enumerations found matching pattern: '{pattern}'")
                return
            
            # Format output
            if output_format == "json":
                enum_data = []
                for enum_info in enumerations:
                    enum_dict = {
                        "name": enum_info.name,
                        "members_count": len(enum_info.members) if enum_info.members else 0
                    }
                    enum_data.append(enum_dict)
                print(json.dumps(enum_data, indent=2))
            
            elif output_format == "table":
                print(f"{'Name':<40} {'Members Count':<15}")
                print("-" * 55)
                for enum_info in enumerations:
                    members_count = len(enum_info.members) if enum_info.members else 0
                    print(f"{enum_info.name:<40} {members_count:<15}")
            
            elif output_format == "csv":
                print("Name,MembersCount")
                for enum_info in enumerations:
                    members_count = len(enum_info.members) if enum_info.members else 0
                    print(f"{enum_info.name},{members_count}")
            
            else:
                # Default to simple list
                for enum_info in enumerations:
                    print(enum_info.name)
            
            if verbose:
                print(f"\nFound {len(enumerations)} enumerations")
    
    except FOClientError as e:
        print(f"Error searching enumerations: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Search for enumerations in D365 Finance & Operations"
    )
    
    parser.add_argument(
        "pattern",
        nargs="?",
        default="",
        help="Search pattern for enumeration names (supports regex)"
    )
    
    parser.add_argument(
        "--output", "-o",
        choices=["json", "table", "csv", "list"],
        default="table",
        help="Output format (default: table)"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of results to return"
    )
    
    parser.add_argument(
        "--base-url",
        help="D365 F&O environment URL"
    )
    
    parser.add_argument(
        "--profile",
        help="Configuration profile to use (not yet implemented)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Run the async function
    asyncio.run(search_enumerations(
        pattern=args.pattern,
        output_format=args.output,
        limit=args.limit,
        base_url=args.base_url,
        profile=args.profile,
        verbose=args.verbose
    ))


if __name__ == "__main__":
    main()