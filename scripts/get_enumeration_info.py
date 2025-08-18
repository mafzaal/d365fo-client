#!/usr/bin/env python3
"""
Get detailed information for a specific enumeration in D365 Finance & Operations

This script retrieves detailed information for a specific enumeration using 
the d365fo-client Python API since enumeration support is not yet available in the CLI.
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


async def get_enumeration_info(
    enumeration_name: str,
    output_format: str = "table",
    resolve_labels: bool = True,
    language: str = "en-US",
    base_url: Optional[str] = None,
    profile: Optional[str] = None,
    verbose: bool = False
):
    """Get detailed information for a specific enumeration."""
    
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
                print(f"Getting information for enumeration: '{enumeration_name}'")
            
            # Get enumeration info
            enum_info = await client.get_public_enumeration_info(
                enumeration_name=enumeration_name,
                resolve_labels=resolve_labels,
                language=language
            )
            
            if not enum_info:
                print(f"Enumeration '{enumeration_name}' not found", file=sys.stderr)
                sys.exit(1)
            
            # Format output
            if output_format == "json":
                enum_dict = {
                    "name": enum_info.name,
                    "members": []
                }
                
                if enum_info.members:
                    for member in enum_info.members:
                        member_dict = {
                            "name": member.name,
                            "value": member.value,
                            "label": getattr(member, 'label', None)
                        }
                        enum_dict["members"].append(member_dict)
                
                print(json.dumps(enum_dict, indent=2))
            
            elif output_format == "table":
                print(f"Enumeration: {enum_info.name}")
                print("=" * 50)
                
                if enum_info.members:
                    print(f"{'Name':<30} {'Value':<10} {'Label':<30}")
                    print("-" * 70)
                    for member in enum_info.members:
                        label = getattr(member, 'label', '') or ''
                        print(f"{member.name:<30} {member.value:<10} {label:<30}")
                    print(f"\nTotal members: {len(enum_info.members)}")
                else:
                    print("No members found")
            
            elif output_format == "csv":
                print("Name,Value,Label")
                if enum_info.members:
                    for member in enum_info.members:
                        label = getattr(member, 'label', '') or ''
                        print(f"{member.name},{member.value},{label}")
            
            else:
                # Default to simple list
                print(f"Enumeration: {enum_info.name}")
                if enum_info.members:
                    for member in enum_info.members:
                        print(f"  {member.name} = {member.value}")
                else:
                    print("  No members found")
    
    except FOClientError as e:
        print(f"Error getting enumeration info: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Get detailed information for a specific enumeration in D365 Finance & Operations"
    )
    
    parser.add_argument(
        "enumeration_name",
        help="Name of the enumeration to get information for"
    )
    
    parser.add_argument(
        "--output", "-o",
        choices=["json", "table", "csv", "list"],
        default="table",
        help="Output format (default: table)"
    )
    
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Don't resolve labels (faster but less detailed)"
    )
    
    parser.add_argument(
        "--language",
        default="en-US",
        help="Language for label resolution (default: en-US)"
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
    asyncio.run(get_enumeration_info(
        enumeration_name=args.enumeration_name,
        output_format=args.output,
        resolve_labels=not args.no_labels,
        language=args.language,
        base_url=args.base_url,
        profile=args.profile,
        verbose=args.verbose
    ))


if __name__ == "__main__":
    main()