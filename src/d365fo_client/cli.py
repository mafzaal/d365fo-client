"""CLI manager for d365fo-client commands."""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, Optional

from .client import FOClient
from .config import ConfigManager
from .exceptions import FOClientError
from .models import FOClientConfig, QueryOptions
from .output import OutputFormatter, format_error_message, format_success_message
from .profiles import Profile


class CLIManager:
    """Main CLI command manager."""

    def __init__(self):
        """Initialize CLI manager."""
        self.config_manager = ConfigManager()
        self.output_formatter = None
        self.client = None

    async def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Setup output formatter
            output_format = getattr(args, "output", "table")
            self.output_formatter = OutputFormatter(output_format)

            # Handle legacy demo mode first
            if getattr(args, "demo", False):
                return await self._run_demo()

            # Handle configuration commands (no client needed)
            if getattr(args, "command", None) == "config":
                return await self._handle_config_commands(args)

            # For other commands, we need a base URL
            # Get effective configuration
            config = self.config_manager.get_effective_config(args)

            # Validate required configuration
            if not config.base_url:
                print(
                    format_error_message(
                        "Base URL is required. Use --base-url or configure a profile."
                    )
                )
                return 1

            # Create and initialize client
            async with FOClient(config) as client:
                self.client = client

                # Route to appropriate command handler
                return await self._route_command(args)

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return 130
        except Exception as e:
            self._handle_error(e, getattr(args, "verbose", False))
            return 1

    async def _run_demo(self) -> int:
        """Run the legacy demo mode."""
        from .main import example_usage

        print("Running demo mode...")
        try:
            await example_usage()
            return 0
        except Exception as e:
            print(f"Demo error: {e}")
            return 1

    async def _route_command(self, args: argparse.Namespace) -> int:
        """Route command to appropriate handler.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        command_handlers = {
            "test": self._handle_test_command,
            "version": self._handle_version_command,
            "metadata": self._handle_metadata_commands,
            "entity": self._handle_entity_commands,
            "action": self._handle_action_commands,
        }

        command = getattr(args, "command", None)
        handler = command_handlers.get(command)

        if handler:
            return await handler(args)
        else:
            print(format_error_message(f"Unknown command: {command}"))
            return 1

    async def _handle_test_command(self, args: argparse.Namespace) -> int:
        """Handle test connectivity command."""
        success = True

        # Test OData connection
        if not getattr(args, "metadata_only", False):
            try:
                if await self.client.test_connection():
                    print(format_success_message("OData API connection successful"))
                else:
                    print(format_error_message("OData API connection failed"))
                    success = False
            except Exception as e:
                print(format_error_message(f"OData API connection error: {e}"))
                success = False

        # Test metadata connection
        if not getattr(args, "odata_only", False):
            try:
                if await self.client.test_metadata_connection():
                    print(format_success_message("Metadata API connection successful"))
                else:
                    print(format_error_message("Metadata API connection failed"))
                    success = False
            except Exception as e:
                print(format_error_message(f"Metadata API connection error: {e}"))
                success = False

        return 0 if success else 1

    async def _handle_version_command(self, args: argparse.Namespace) -> int:
        """Handle version information command."""
        try:
            version_info = {}

            # Get different version types based on args
            if getattr(args, "application", False) or getattr(args, "all", False):
                version_info["application"] = (
                    await self.client.get_application_version()
                )

            if getattr(args, "platform", False) or getattr(args, "all", False):
                version_info["platform_build"] = (
                    await self.client.get_platform_build_version()
                )

            if getattr(args, "build", False) or getattr(args, "all", False):
                version_info["application_build"] = (
                    await self.client.get_application_build_version()
                )

            # If no specific version requested, get application version
            if not version_info:
                version_info["application"] = (
                    await self.client.get_application_version()
                )

            output = self.output_formatter.format_output(version_info)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error retrieving version information: {e}"))
            return 1

    async def _handle_metadata_commands(self, args: argparse.Namespace) -> int:
        """Handle metadata operations."""
        subcommand = getattr(args, "metadata_subcommand", None)

        if subcommand == "sync":
            return await self._handle_metadata_sync(args)
        elif subcommand == "search":
            return await self._handle_metadata_search(args)
        elif subcommand == "info":
            return await self._handle_metadata_info(args)
        else:
            print(format_error_message(f"Unknown metadata subcommand: {subcommand}"))
            return 1

    async def _handle_metadata_sync(self, args: argparse.Namespace) -> int:
        """Handle metadata sync command."""
        try:
            force_refresh = getattr(args, "force", False)
            success = await self.client.download_metadata(force_refresh=force_refresh)

            if success:
                print(format_success_message("Metadata synchronized successfully"))
                return 0
            else:
                print(format_error_message("Metadata synchronization failed"))
                return 1
        except Exception as e:
            print(format_error_message(f"Error syncing metadata: {e}"))
            return 1

    async def _handle_metadata_search(self, args: argparse.Namespace) -> int:
        """Handle metadata search command."""
        try:
            pattern = getattr(args, "pattern", "")
            search_type = getattr(args, "type", "entities")
            limit = getattr(args, "limit", None)

            results = []

            if search_type in ["entities", "all"]:
                entities = self.client.search_entities(pattern)
                if limit:
                    entities = entities[:limit]
                results.extend([{"type": "entity", "name": name} for name in entities])

            if search_type in ["actions", "all"]:
                actions = self.client.search_actions(pattern)
                if limit:
                    actions = actions[:limit]
                results.extend([{"type": "action", "name": name} for name in actions])

            if not results:
                print(f"No {search_type} found matching pattern: {pattern}")
                return 0

            # If table format and mixed types, show type column
            if self.output_formatter.format_type == "table" and search_type == "all":
                output = self.output_formatter.format_output(results, ["type", "name"])
            else:
                # For specific types or other formats, just show names
                names = [r["name"] for r in results]
                output = self.output_formatter.format_output(names)

            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error searching metadata: {e}"))
            return 1

    async def _handle_metadata_info(self, args: argparse.Namespace) -> int:
        """Handle metadata info command."""
        try:
            entity_name = getattr(args, "entity_name", "")

            entity_info = await self.client.get_entity_info_with_labels(entity_name)
            if not entity_info:
                print(format_error_message(f"Entity not found: {entity_name}"))
                return 1

            # Build info dictionary
            info = {
                "name": entity_info.name,
                "label": entity_info.label_text or entity_info.label_id,
                "properties_count": len(entity_info.enhanced_properties),
            }

            # Add properties if requested
            if getattr(args, "properties", False):
                properties = []
                for prop in entity_info.enhanced_properties:
                    prop_info = {
                        "name": prop.name,
                        "type": prop.type,
                        "label": prop.label_text or prop.label_id,
                    }
                    if getattr(args, "keys", False):
                        prop_info["is_key"] = prop.is_key
                    properties.append(prop_info)
                info["properties"] = properties

            output = self.output_formatter.format_output(info)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error getting entity info: {e}"))
            return 1

    async def _handle_entity_commands(self, args: argparse.Namespace) -> int:
        """Handle entity operations."""
        subcommand = getattr(args, "entity_subcommand", None)

        if subcommand == "get":
            return await self._handle_entity_get(args)
        elif subcommand == "create":
            return await self._handle_entity_create(args)
        elif subcommand == "update":
            return await self._handle_entity_update(args)
        elif subcommand == "delete":
            return await self._handle_entity_delete(args)
        else:
            print(format_error_message(f"Unknown entity subcommand: {subcommand}"))
            return 1

    async def _handle_entity_get(self, args: argparse.Namespace) -> int:
        """Handle entity get command."""
        try:
            entity_name = getattr(args, "entity_name", "")
            key = getattr(args, "key", None)

            # Build query options
            query_options = None
            if any(
                [
                    getattr(args, "select", None),
                    getattr(args, "filter", None),
                    getattr(args, "top", None),
                    getattr(args, "orderby", None),
                ]
            ):
                query_options = QueryOptions(
                    select=(
                        getattr(args, "select", "").split(",")
                        if getattr(args, "select", "")
                        else None
                    ),
                    filter=getattr(args, "filter", None),
                    top=getattr(args, "top", None),
                    orderby=(
                        getattr(args, "orderby", "").split(",")
                        if getattr(args, "orderby", "")
                        else None
                    ),
                )

            # Execute query
            if key:
                result = await self.client.get_entity(entity_name, key, query_options)
            else:
                result = await self.client.get_entities(entity_name, query_options)

            # Format and output
            if isinstance(result, dict) and "value" in result:
                # OData response format
                output = self.output_formatter.format_output(result["value"])
            else:
                output = self.output_formatter.format_output(result)

            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error getting entity data: {e}"))
            return 1

    async def _handle_entity_create(self, args: argparse.Namespace) -> int:
        """Handle entity create command."""
        try:
            entity_name = getattr(args, "entity_name", "")

            # Get data from args
            data_json = getattr(args, "data", None)
            data_file = getattr(args, "file", None)

            if data_json:
                data = json.loads(data_json)
            elif data_file:
                with open(data_file, "r") as f:
                    data = json.load(f)
            else:
                print(format_error_message("Either --data or --file must be provided"))
                return 1

            result = await self.client.create_entity(entity_name, data)

            print(format_success_message(f"Entity created successfully"))
            output = self.output_formatter.format_output(result)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error creating entity: {e}"))
            return 1

    async def _handle_entity_update(self, args: argparse.Namespace) -> int:
        """Handle entity update command."""
        try:
            entity_name = getattr(args, "entity_name", "")
            key = getattr(args, "key", "")

            # Get data from args
            data_json = getattr(args, "data", None)
            data_file = getattr(args, "file", None)

            if data_json:
                data = json.loads(data_json)
            elif data_file:
                with open(data_file, "r") as f:
                    data = json.load(f)
            else:
                print(format_error_message("Either --data or --file must be provided"))
                return 1

            result = await self.client.update_entity(entity_name, key, data)

            print(format_success_message(f"Entity updated successfully"))
            output = self.output_formatter.format_output(result)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error updating entity: {e}"))
            return 1

    async def _handle_entity_delete(self, args: argparse.Namespace) -> int:
        """Handle entity delete command."""
        try:
            entity_name = getattr(args, "entity_name", "")
            key = getattr(args, "key", "")

            # Check for confirmation if not provided
            if not getattr(args, "confirm", False):
                response = input(
                    f"Are you sure you want to delete {entity_name} with key '{key}'? (y/N): "
                )
                if response.lower() not in ["y", "yes"]:
                    print("Delete operation cancelled")
                    return 0

            success = await self.client.delete_entity(entity_name, key)

            if success:
                print(format_success_message(f"Entity deleted successfully"))
                return 0
            else:
                print(format_error_message("Delete operation failed"))
                return 1

        except Exception as e:
            print(format_error_message(f"Error deleting entity: {e}"))
            return 1

    async def _handle_action_commands(self, args: argparse.Namespace) -> int:
        """Handle action operations."""
        subcommand = getattr(args, "action_subcommand", None)

        if subcommand == "list":
            return await self._handle_action_list(args)
        elif subcommand == "call":
            return await self._handle_action_call(args)
        else:
            print(format_error_message(f"Unknown action subcommand: {subcommand}"))
            return 1

    async def _handle_action_list(self, args: argparse.Namespace) -> int:
        """Handle action list command."""
        try:
            pattern = getattr(args, "pattern", "")
            entity = getattr(args, "entity", None)

            actions = self.client.search_actions(pattern)

            if entity:
                # Filter actions for specific entity (this is a simplified approach)
                actions = [
                    action for action in actions if entity.lower() in action.lower()
                ]

            if not actions:
                print(f"No actions found matching pattern: {pattern}")
                return 0

            output = self.output_formatter.format_output(actions)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error listing actions: {e}"))
            return 1

    async def _handle_action_call(self, args: argparse.Namespace) -> int:
        """Handle action call command."""
        try:
            action_name = getattr(args, "action_name", "")
            entity_name = getattr(args, "entity", None)
            parameters_json = getattr(args, "parameters", None)

            parameters = {}
            if parameters_json:
                parameters = json.loads(parameters_json)

            result = await self.client.call_action(action_name, parameters, entity_name)

            print(
                format_success_message(f"Action '{action_name}' executed successfully")
            )
            output = self.output_formatter.format_output(result)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error calling action: {e}"))
            return 1

    async def _handle_config_commands(self, args: argparse.Namespace) -> int:
        """Handle configuration management commands."""
        subcommand = getattr(args, "config_subcommand", None)

        if subcommand == "list":
            return self._handle_config_list(args)
        elif subcommand == "show":
            return self._handle_config_show(args)
        elif subcommand == "create":
            return self._handle_config_create(args)
        elif subcommand == "update":
            return self._handle_config_update(args)
        elif subcommand == "delete":
            return self._handle_config_delete(args)
        elif subcommand == "set-default":
            return self._handle_config_set_default(args)
        else:
            print(format_error_message(f"Unknown config subcommand: {subcommand}"))
            return 1

    def _handle_config_list(self, args: argparse.Namespace) -> int:
        """Handle config list command."""
        try:
            profiles = self.config_manager.list_profiles()
            default_profile = self.config_manager.get_default_profile()

            if not profiles:
                print("No configuration profiles found")
                return 0

            profile_list = []
            for name, profile in profiles.items():
                profile_info = {
                    "name": name,
                    "base_url": profile.base_url,
                    "auth_mode": profile.auth_mode,
                    "default": (
                        "✓" if default_profile and default_profile.name == name else ""
                    ),
                }
                profile_list.append(profile_info)

            output = self.output_formatter.format_output(
                profile_list, ["name", "base_url", "auth_mode", "default"]
            )
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error listing profiles: {e}"))
            return 1

    def _handle_config_show(self, args: argparse.Namespace) -> int:
        """Handle config show command."""
        try:
            profile_name = getattr(args, "profile_name", "")
            profile = self.config_manager.get_profile(profile_name)

            if not profile:
                print(format_error_message(f"Profile not found: {profile_name}"))
                return 1

            # Convert profile to dict for display
            profile_dict = {
                "name": profile.name,
                "base_url": profile.base_url,
                "auth_mode": profile.auth_mode,
                "verify_ssl": profile.verify_ssl,
                "output_format": profile.output_format,
                "label_cache": profile.label_cache,
                "label_expiry": profile.label_expiry,
                "language": profile.language,
            }

            # Only show auth details if they exist
            if profile.client_id:
                profile_dict["client_id"] = profile.client_id
            if profile.tenant_id:
                profile_dict["tenant_id"] = profile.tenant_id

            output = self.output_formatter.format_output(profile_dict)
            print(output)
            return 0

        except Exception as e:
            print(format_error_message(f"Error showing profile: {e}"))
            return 1

    def _handle_config_create(self, args: argparse.Namespace) -> int:
        """Handle config create command."""
        try:
            profile_name = getattr(args, "profile_name", "")
            base_url = getattr(args, "base_url", "")

            if not base_url:
                print(
                    format_error_message(
                        "--base-url is required when creating a profile"
                    )
                )
                return 1

            # Check if profile already exists
            if self.config_manager.get_profile(profile_name):
                print(format_error_message(f"Profile already exists: {profile_name}"))
                return 1

            # Create new profile
            profile = Profile(
                name=profile_name,
                base_url=base_url,
                auth_mode=getattr(args, "auth_mode", "default"),
                client_id=getattr(args, "client_id", None),
                client_secret=getattr(args, "client_secret", None),
                tenant_id=getattr(args, "tenant_id", None),
                verify_ssl=getattr(args, "verify_ssl", True),
                output_format=getattr(args, "output_format", "table"),
                use_label_cache=getattr(args, "label_cache", True),
                label_cache_expiry_minutes=getattr(args, "label_expiry", 60),
                use_cache_first=getattr(args, "use_cache_first", True),
                timeout=getattr(args, "timeout", 60),
                language=getattr(args, "language", "en-US"),
            )

            self.config_manager.save_profile(profile)
            print(
                format_success_message(f"Profile '{profile_name}' created successfully")
            )
            return 0

        except Exception as e:
            print(format_error_message(f"Error creating profile: {e}"))
            return 1

    def _handle_config_update(self, args: argparse.Namespace) -> int:
        """Handle config update command."""
        # Similar to create but updates existing profile
        print(format_error_message("Config update not yet implemented"))
        return 1

    def _handle_config_delete(self, args: argparse.Namespace) -> int:
        """Handle config delete command."""
        try:
            profile_name = getattr(args, "profile_name", "")

            if not self.config_manager.get_profile(profile_name):
                print(format_error_message(f"Profile not found: {profile_name}"))
                return 1

            success = self.config_manager.delete_profile(profile_name)
            if success:
                print(
                    format_success_message(
                        f"Profile '{profile_name}' deleted successfully"
                    )
                )
                return 0
            else:
                print(format_error_message(f"Failed to delete profile: {profile_name}"))
                return 1

        except Exception as e:
            print(format_error_message(f"Error deleting profile: {e}"))
            return 1

    def _handle_config_set_default(self, args: argparse.Namespace) -> int:
        """Handle config set-default command."""
        try:
            profile_name = getattr(args, "profile_name", "")

            success = self.config_manager.set_default_profile(profile_name)
            if success:
                print(format_success_message(f"Default profile set to: {profile_name}"))
                return 0
            else:
                print(format_error_message(f"Profile not found: {profile_name}"))
                return 1

        except Exception as e:
            print(format_error_message(f"Error setting default profile: {e}"))
            return 1

    def _handle_error(self, error: Exception, verbose: bool = False) -> None:
        """Handle and display errors consistently.

        Args:
            error: Exception that occurred
            verbose: Whether to show detailed error information
        """
        if isinstance(error, FOClientError):
            print(format_error_message(str(error)))
        else:
            if verbose:
                import traceback

                traceback.print_exc()
            else:
                print(format_error_message(f"Unexpected error: {error}"))
