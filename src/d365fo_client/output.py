"""Output formatting module for d365fo-client CLI."""

import csv
import io
import json
from typing import Any, Dict, List, Optional, Union

import yaml
from tabulate import tabulate


class OutputFormatter:
    """Handles formatting of output data in various formats."""

    SUPPORTED_FORMATS = ["json", "table", "csv", "yaml"]

    def __init__(self, format_type: str = "table"):
        """Initialize the output formatter.

        Args:
            format_type: Output format type (json, table, csv, yaml)
        """
        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format_type}. Supported: {self.SUPPORTED_FORMATS}"
            )

        self.format_type = format_type

    def format_output(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format data according to the specified output format.

        Args:
            data: Data to format
            headers: Optional headers for table format

        Returns:
            Formatted string output
        """
        if data is None:
            return ""

        if self.format_type == "json":
            return self._format_json(data)
        elif self.format_type == "table":
            return self._format_table(data, headers)
        elif self.format_type == "csv":
            return self._format_csv(data, headers)
        elif self.format_type == "yaml":
            return self._format_yaml(data)
        else:
            # Fallback to JSON
            return self._format_json(data)

    def _format_json(self, data: Any) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)

    def _format_yaml(self, data: Any) -> str:
        """Format data as YAML."""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, indent=2)

    def _format_table(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format data as a table using tabulate."""
        if not data:
            return "No data to display."

        # Handle different data types
        if isinstance(data, dict):
            # For single record or key-value pairs
            if headers:
                # If headers provided, try to extract those fields
                rows = [[data.get(h, "") for h in headers]]
                return tabulate(rows, headers=headers, tablefmt="grid")
            else:
                # Show as key-value pairs
                rows = [[k, v] for k, v in data.items()]
                return tabulate(rows, headers=["Property", "Value"], tablefmt="grid")

        elif isinstance(data, list):
            if not data:
                return "No data to display."

            # For list of records
            if isinstance(data[0], dict):
                # Extract headers from first item if not provided
                if not headers:
                    headers = list(data[0].keys())

                # Extract rows
                rows = []
                for item in data:
                    row = []
                    for header in headers:
                        value = item.get(header, "")
                        # Handle nested objects/lists by converting to string
                        if isinstance(value, (dict, list)):
                            value = str(value)
                        row.append(value)
                    rows.append(row)

                return tabulate(rows, headers=headers, tablefmt="grid")
            else:
                # List of simple values
                rows = [[item] for item in data]
                return tabulate(rows, headers=["Value"], tablefmt="grid")

        else:
            # Single value
            return str(data)

    def _format_csv(self, data: Any, headers: Optional[List[str]] = None) -> str:
        """Format data as CSV."""
        if not data:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)

        if isinstance(data, dict):
            # Single record
            if headers:
                writer.writerow(headers)
                writer.writerow([data.get(h, "") for h in headers])
            else:
                # Key-value pairs
                writer.writerow(["Property", "Value"])
                for k, v in data.items():
                    writer.writerow([k, v])

        elif isinstance(data, list):
            if not data:
                return ""

            if isinstance(data[0], dict):
                # List of records
                if not headers:
                    headers = list(data[0].keys())

                writer.writerow(headers)
                for item in data:
                    row = []
                    for header in headers:
                        value = item.get(header, "")
                        # Handle nested objects by converting to JSON string
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, default=str)
                        row.append(value)
                    writer.writerow(row)
            else:
                # List of simple values
                writer.writerow(["Value"])
                for item in data:
                    writer.writerow([item])

        else:
            # Single value
            writer.writerow(["Value"])
            writer.writerow([data])

        return output.getvalue()


def format_success_message(message: str) -> str:
    """Format a success message with checkmark."""
    return f"✅ {message}"


def format_error_message(message: str) -> str:
    """Format an error message with X mark."""
    return f"❌ {message}"


def format_info_message(message: str) -> str:
    """Format an info message with info icon."""
    return f"ℹ️  {message}"


def format_warning_message(message: str) -> str:
    """Format a warning message with warning icon."""
    return f"⚠️  {message}"
