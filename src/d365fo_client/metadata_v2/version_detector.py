"""Module-based version detection using GetInstalledModules action."""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from d365fo_client.metadata_api import MetadataAPIOperations

from ..exceptions import MetadataError
from ..models import EnvironmentVersionInfo, ModuleVersionInfo, VersionDetectionResult

logger = logging.getLogger(__name__)


class VersionDetectionError(MetadataError):
    """Raised when version detection fails"""

    pass


class ModuleVersionDetector:
    """Detects environment version using GetInstalledModules action"""

    def __init__(self, api_operations: "MetadataAPIOperations"):
        """Initialize with API operations instance

        Args:
            api_operations: Instance providing API access (e.g., MetadataAPIOperations)
        """
        self.api = api_operations
        self._cache_ttl = 300  # Cache version detection for 5 minutes
        self._cached_version: Optional[Tuple[EnvironmentVersionInfo, datetime]] = None

    async def get_environment_version(
        self, use_cache: bool = True
    ) -> VersionDetectionResult:
        """Get current environment version based on installed modules

        Args:
            use_cache: Whether to use cached version if available

        Returns:
            VersionDetectionResult with complete module details or error information
        """
        start_time = time.time()
        cache_hit = False

        try:
            # Check cache first
            if use_cache and self._cached_version:
                cached_version, cached_at = self._cached_version
                age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if age < self._cache_ttl:
                    logger.debug(f"Using cached version detection (age: {age:.1f}s)")
                    cache_hit = True
                    return VersionDetectionResult(
                        success=True,
                        version_info=cached_version,
                        detection_time_ms=(time.time() - start_time) * 1000,
                        modules_count=len(cached_version.modules),
                        cache_hit=True,
                    )

            logger.info("Detecting environment version using GetInstalledModules")

            # Use the get_installed_modules method from MetadataAPIOperations
            module_strings = await self.api.get_installed_modules()

            # Parse module information
            modules = self._parse_modules_list(module_strings)
            logger.debug(f"Successfully parsed {len(modules)} modules")

            # Get fallback version info
            app_version, platform_version = await self._get_fallback_versions()

            # Create version info
            version_info = EnvironmentVersionInfo(
                environment_id=0,  # Will be set by cache manager
                version_hash="",  # Will be computed in __post_init__
                modules_hash="",  # Will be computed in __post_init__
                application_version=app_version,
                platform_version=platform_version,
                modules=modules,
                computed_at=datetime.now(timezone.utc),
                is_active=True,
            )

            # Cache the result
            self._cached_version = (version_info, datetime.now(timezone.utc))

            detection_time = (time.time() - start_time) * 1000
            logger.info(
                f"Version detection complete: {len(modules)} modules, "
                f"hash: {version_info.version_hash}, time: {detection_time:.1f}ms"
            )

            return VersionDetectionResult(
                success=True,
                version_info=version_info,
                detection_time_ms=detection_time,
                modules_count=len(modules),
                cache_hit=cache_hit,
            )

        except Exception as e:
            detection_time = (time.time() - start_time) * 1000
            error_msg = f"Failed to detect environment version: {e}"
            logger.error(error_msg)

            return VersionDetectionResult(
                success=False,
                error_message=error_msg,
                detection_time_ms=detection_time,
                cache_hit=cache_hit,
            )

    def _parse_modules_list(self, module_strings: List[str]) -> List[ModuleVersionInfo]:
        """Parse list of module strings into ModuleVersionInfo objects

        Args:
            module_strings: List of module strings from GetInstalledModules

        Returns:
            List of ModuleVersionInfo objects

        Raises:
            VersionDetectionError: If parsing fails
        """
        try:
            if not isinstance(module_strings, list):
                raise VersionDetectionError("Invalid input: expected list of strings")

            if not module_strings:
                raise VersionDetectionError("No modules found in response")

            modules = []
            parse_errors = []

            for module_string in module_strings:
                try:
                    module = ModuleVersionInfo.parse_from_string(module_string)
                    modules.append(module)
                except ValueError as e:
                    parse_errors.append(f"Module parse error: {e}")
                    continue

            if not modules:
                error_msg = f"No valid modules found. Parse errors: {'; '.join(parse_errors[:5])}"
                raise VersionDetectionError(error_msg)

            if parse_errors:
                logger.warning(
                    f"Failed to parse {len(parse_errors)} module strings out of {len(module_strings)}"
                )

            logger.debug(
                f"Successfully parsed {len(modules)} modules from {len(module_strings)} strings"
            )
            return modules

        except Exception as e:
            if isinstance(e, VersionDetectionError):
                raise
            raise VersionDetectionError(f"Failed to parse modules list: {e}")

    def _parse_modules_response(self, response: Dict) -> List[ModuleVersionInfo]:
        """Parse GetInstalledModules response into ModuleVersionInfo objects

        Args:
            response: Response from GetInstalledModules action

        Returns:
            List of ModuleVersionInfo objects

        Raises:
            VersionDetectionError: If response format is invalid
        """
        try:
            if not response.get("success", False):
                raise VersionDetectionError("GetInstalledModules action failed")

            result = response.get("result", {})
            module_strings = result.get("value", [])

            if not isinstance(module_strings, list):
                raise VersionDetectionError(
                    "Invalid response format: expected list of strings"
                )

            if not module_strings:
                raise VersionDetectionError("No modules found in response")

            modules = []
            parse_errors = []

            for module_string in module_strings:
                try:
                    module = ModuleVersionInfo.parse_from_string(module_string)
                    modules.append(module)
                except ValueError as e:
                    parse_errors.append(f"Module parse error: {e}")
                    continue

            if not modules:
                error_msg = f"No valid modules found. Parse errors: {'; '.join(parse_errors[:5])}"
                raise VersionDetectionError(error_msg)

            if parse_errors:
                logger.warning(
                    f"Failed to parse {len(parse_errors)} module strings out of {len(module_strings)}"
                )

            logger.debug(
                f"Successfully parsed {len(modules)} modules from {len(module_strings)} strings"
            )
            return modules

        except Exception as e:
            if isinstance(e, VersionDetectionError):
                raise
            raise VersionDetectionError(f"Failed to parse modules response: {e}")

    async def _get_fallback_versions(self) -> Tuple[Optional[str], Optional[str]]:
        """Get fallback application and platform versions"""
        app_version = None
        platform_version = None

        try:
            app_version = await self.api.get_application_version()
            logger.debug(f"Got application version: {app_version}")
        except Exception as e:
            logger.warning(f"Failed to get application version: {e}")

        try:
            platform_version = await self.api.get_platform_build_version()
            logger.debug(f"Got platform version: {platform_version}")
        except Exception as e:
            logger.warning(f"Failed to get platform version: {e}")

        return app_version, platform_version

    async def compare_versions(
        self, version1: EnvironmentVersionInfo, version2: EnvironmentVersionInfo
    ) -> Dict[str, Any]:
        """Compare two environment versions and return differences

        Args:
            version1: First version to compare
            version2: Second version to compare

        Returns:
            Dictionary with comparison results including added, removed, and updated modules
        """
        comparison = {
            "identical": version1.modules_hash == version2.modules_hash,
            "hash_match": version1.version_hash == version2.version_hash,
            "module_count_diff": len(version2.modules) - len(version1.modules),
            "added_modules": [],
            "removed_modules": [],
            "updated_modules": [],
            "identical_modules": [],
        }

        # Create module dictionaries for comparison
        v1_modules = {m.module_id: m for m in version1.modules}
        v2_modules = {m.module_id: m for m in version2.modules}

        # Find differences
        for module_id, module in v2_modules.items():
            if module_id not in v1_modules:
                comparison["added_modules"].append(module.to_dict())
            elif v1_modules[module_id].version != module.version:
                comparison["updated_modules"].append(
                    {
                        "module_id": module_id,
                        "old_version": v1_modules[module_id].version,
                        "new_version": module.version,
                        "old_publisher": v1_modules[module_id].publisher,
                        "new_publisher": module.publisher,
                    }
                )
            else:
                comparison["identical_modules"].append(module_id)

        for module_id in v1_modules:
            if module_id not in v2_modules:
                comparison["removed_modules"].append(v1_modules[module_id].to_dict())

        # Add summary statistics
        comparison["summary"] = {
            "total_changes": len(comparison["added_modules"])
            + len(comparison["removed_modules"])
            + len(comparison["updated_modules"]),
            "modules_added": len(comparison["added_modules"]),
            "modules_removed": len(comparison["removed_modules"]),
            "modules_updated": len(comparison["updated_modules"]),
            "modules_unchanged": len(comparison["identical_modules"]),
        }

        return comparison

    def clear_cache(self):
        """Clear cached version detection"""
        self._cached_version = None
        logger.debug("Version detection cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached version"""
        if not self._cached_version:
            return {"cached": False}

        cached_version, cached_at = self._cached_version
        age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()

        return {
            "cached": True,
            "cache_age_seconds": age_seconds,
            "cache_expires_in_seconds": self._cache_ttl - age_seconds,
            "version_hash": cached_version.version_hash,
            "modules_count": len(cached_version.modules),
            "cached_at": cached_at.isoformat(),
        }


# Helper functions for version utilities
def compute_version_signature(modules: List[ModuleVersionInfo]) -> str:
    """Compute a compact signature for version identification

    Args:
        modules: List of module version info

    Returns:
        Compact version signature string
    """
    if not modules:
        return "empty"

    # Sort modules and create compact signature
    sorted_modules = sorted(modules, key=lambda m: m.module_id)

    # Use first 5 and last 5 modules for signature to keep it compact
    signature_modules = (
        sorted_modules[:5] + sorted_modules[-5:]
        if len(sorted_modules) > 10
        else sorted_modules
    )

    sig_parts = []
    for module in signature_modules:
        # Use module_id and version only
        sig_parts.append(f"{module.module_id[:10]}:{module.version}")

    signature = "|".join(sig_parts)
    return hashlib.sha256(signature.encode()).hexdigest()[:12]


def extract_core_modules(modules: List[ModuleVersionInfo]) -> List[ModuleVersionInfo]:
    """Extract core/essential modules for quick comparison

    Args:
        modules: Complete list of modules

    Returns:
        List of core modules
    """
    core_module_patterns = [
        "ApplicationPlatform",
        "ApplicationFoundation",
        "ApplicationSuite",
        "ApplicationCommon",
        "Directory",
        "DataManagement",
    ]

    core_modules = []
    for module in modules:
        if any(pattern in module.module_id for pattern in core_module_patterns):
            core_modules.append(module)

    return sorted(core_modules, key=lambda m: m.module_id)


def validate_modules_consistency(modules: List[ModuleVersionInfo]) -> Dict[str, Any]:
    """Validate consistency of module versions

    Args:
        modules: List of modules to validate

    Returns:
        Dictionary with validation results
    """
    validation = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "statistics": {
            "total_modules": len(modules),
            "unique_publishers": len(set(m.publisher for m in modules)),
            "unique_versions": len(set(m.version for m in modules)),
        },
    }

    # Check for duplicate module IDs
    module_ids = [m.module_id for m in modules]
    duplicates = [mid for mid in set(module_ids) if module_ids.count(mid) > 1]
    if duplicates:
        validation["valid"] = False
        validation["issues"].append(f"Duplicate module IDs found: {duplicates}")

    # Check for missing core modules
    core_patterns = ["ApplicationPlatform", "ApplicationFoundation"]
    found_core = [p for p in core_patterns if any(p in m.module_id for m in modules)]
    if len(found_core) < len(core_patterns):
        missing = [p for p in core_patterns if p not in found_core]
        validation["warnings"].append(f"Missing core modules: {missing}")

    # Check version consistency for related modules
    version_groups = {}
    for module in modules:
        # Group by major version
        major_version = (
            module.version.split(".")[0] if "." in module.version else module.version
        )
        if major_version not in version_groups:
            version_groups[major_version] = []
        version_groups[major_version].append(module.module_id)

    validation["statistics"]["version_groups"] = {
        k: len(v) for k, v in version_groups.items()
    }

    return validation
