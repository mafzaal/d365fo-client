"""Tests for composite key handling in query utilities."""

import pytest

from src.d365fo_client.query import QueryBuilder


class TestCompositeKeyHandling:
    """Test cases for composite key handling."""

    def test_encode_simple_key(self):
        """Test encoding of simple string keys."""
        key = "CUST001"
        encoded = QueryBuilder.encode_key(key)
        assert encoded == "CUST001"

    def test_encode_simple_key_with_special_characters(self):
        """Test encoding of simple keys with special characters."""
        key = "CUST/001 & Co."
        encoded = QueryBuilder.encode_key(key)
        assert "CUST%2F001%20%26%20Co." == encoded

    def test_encode_composite_key(self):
        """Test encoding of composite dictionary keys."""
        key = {"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"}
        encoded = QueryBuilder.encode_key(key)
        assert encoded == "dataAreaId='usmf',CustomerAccount='MAFZAAL001'"

    def test_encode_composite_key_with_special_characters(self):
        """Test encoding of composite keys with special characters."""
        key = {"dataAreaId": "us/mf", "CustomerAccount": "CUST & CO"}
        encoded = QueryBuilder.encode_key(key)
        assert encoded == "dataAreaId='us%2Fmf',CustomerAccount='CUST%20%26%20CO'"

    def test_build_entity_url_simple_key(self):
        """Test building entity URL with simple key."""
        url = QueryBuilder.build_entity_url(
            "https://example.com", "CustomersV3", "CUST001"
        )
        assert url == "https://example.com/data/CustomersV3('CUST001')"

    def test_build_entity_url_composite_key(self):
        """Test building entity URL with composite key."""
        key = {"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"}
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3", key)
        # Should now include cross-company=true because dataAreaId is in the key
        assert (
            url
            == "https://example.com/data/CustomersV3(dataAreaId='usmf',CustomerAccount='MAFZAAL001')?cross-company=true"
        )

    def test_build_entity_url_no_key(self):
        """Test building entity URL without key."""
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3")
        assert url == "https://example.com/data/CustomersV3"

    def test_build_action_url_simple_key(self):
        """Test building action URL with simple key."""
        url = QueryBuilder.build_action_url(
            "https://example.com", "TestAction", "CustomersV3", "CUST001"
        )
        assert (
            url
            == "https://example.com/data/CustomersV3('CUST001')/Microsoft.Dynamics.DataEntities.TestAction"
        )

    def test_build_action_url_composite_key(self):
        """Test building action URL with composite key."""
        key = {"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"}
        url = QueryBuilder.build_action_url(
            "https://example.com", "TestAction", "CustomersV3", key
        )
        # Should now include cross-company=true because dataAreaId is in the key
        assert (
            url
            == "https://example.com/data/CustomersV3(dataAreaId='usmf',CustomerAccount='MAFZAAL001')/Microsoft.Dynamics.DataEntities.TestAction?cross-company=true"
        )

    def test_build_action_url_entity_set_bound(self):
        """Test building action URL bound to entity set."""
        url = QueryBuilder.build_action_url(
            "https://example.com", "TestAction", "CustomersV3"
        )
        assert (
            url
            == "https://example.com/data/CustomersV3/Microsoft.Dynamics.DataEntities.TestAction"
        )

    def test_build_action_url_unbound(self):
        """Test building unbound action URL."""
        url = QueryBuilder.build_action_url("https://example.com", "TestAction")
        assert (
            url == "https://example.com/data/Microsoft.Dynamics.DataEntities.TestAction"
        )

    def test_real_world_composite_key_case(self):
        """Test the exact case from the original error."""
        key = {"dataAreaId": "usmf", "CustomerAccount": "MAFZAAL001"}

        url = QueryBuilder.build_entity_url(
            "https://usnconeboxax1aos.cloud.onebox.dynamics.com", "CustomersV3", key
        )

        # The URL should NOT contain the problematic string representation
        assert "'{'dataAreaId': 'usmf', 'CustomerAccount': 'MAFZAAL001'}'" not in url

        # The URL should be properly formatted and include cross-company=true
        expected = "https://usnconeboxax1aos.cloud.onebox.dynamics.com/data/CustomersV3(dataAreaId='usmf',CustomerAccount='MAFZAAL001')?cross-company=true"
        assert url == expected

    def test_multiple_composite_keys(self):
        """Test encoding of composite keys with multiple fields."""
        key = {
            "dataAreaId": "usmf",
            "CustomerAccount": "MAFZAAL001",
            "InvoiceId": "INV-001",
            "LineNumber": "1",
        }
        encoded = QueryBuilder.encode_key(key)

        # Check that all fields are included
        assert "dataAreaId='usmf'" in encoded
        assert "CustomerAccount='MAFZAAL001'" in encoded
        assert "InvoiceId='INV-001'" in encoded
        assert "LineNumber='1'" in encoded

        # Check formatting
        parts = encoded.split(",")
        assert len(parts) == 4
        for part in parts:
            assert "=" in part
            assert part.count("'") == 2  # Each part should have exactly 2 quotes
