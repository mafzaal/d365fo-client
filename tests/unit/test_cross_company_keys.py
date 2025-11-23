"""Unit tests for cross-company parameter when dataAreaId is in composite keys."""

from src.d365fo_client.query import QueryBuilder


class TestCrossCompanyInKeys:
    """Test automatic addition of cross-company=true when dataAreaId is in entity keys."""

    def test_has_data_area_id_in_dict_key(self):
        """Test detection of dataAreaId in dictionary keys."""
        key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
        assert QueryBuilder.has_data_area_id_in_key(key) is True

    def test_has_data_area_id_case_insensitive(self):
        """Test case-insensitive detection of dataAreaId."""
        test_cases = [
            {"dataAreaId": "USMF"},
            {"DataAreaId": "USMF"},
            {"DATAAREAID": "USMF"},
            {"dataareaId": "USMF"},
        ]
        for key in test_cases:
            assert (
                QueryBuilder.has_data_area_id_in_key(key) is True
            ), f"Failed for key: {key}"

    def test_has_no_data_area_id_in_dict_key(self):
        """Test no detection when dataAreaId is not in key."""
        key = {"CustomerAccount": "CUST001", "InvoiceId": "INV001"}
        assert QueryBuilder.has_data_area_id_in_key(key) is False

    def test_has_data_area_id_simple_key_returns_false(self):
        """Test that simple string keys return False."""
        key = "CUST001"
        assert QueryBuilder.has_data_area_id_in_key(key) is False

    def test_build_entity_url_with_dataareaId_adds_cross_company(self):
        """Test that build_entity_url adds cross-company when dataAreaId is in key."""
        key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3", key)

        assert "cross-company=true" in url
        assert (
            url
            == "https://example.com/data/CustomersV3(dataAreaId='USMF',CustomerAccount='CUST001')?cross-company=true"
        )

    def test_build_entity_url_without_dataareaId_no_cross_company(self):
        """Test that build_entity_url doesn't add cross-company when dataAreaId is not in key."""
        key = {"CustomerAccount": "CUST001", "InvoiceId": "INV001"}
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3", key)

        assert "cross-company" not in url

    def test_build_entity_url_simple_key_no_cross_company(self):
        """Test that simple keys don't trigger cross-company."""
        key = "CUST001"
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3", key)

        assert "cross-company" not in url
        assert url == "https://example.com/data/CustomersV3('CUST001')"

    def test_build_entity_url_no_key_no_cross_company(self):
        """Test that URLs without keys don't have cross-company."""
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3")

        assert "cross-company" not in url
        assert url == "https://example.com/data/CustomersV3"

    def test_build_action_url_with_dataareaId_adds_cross_company(self):
        """Test that build_action_url adds cross-company when dataAreaId is in entity key."""
        key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
        url = QueryBuilder.build_action_url(
            "https://example.com", "TestAction", "CustomersV3", key
        )

        assert "cross-company=true" in url
        assert (
            url
            == "https://example.com/data/CustomersV3(dataAreaId='USMF',CustomerAccount='CUST001')/Microsoft.Dynamics.DataEntities.TestAction?cross-company=true"
        )

    def test_build_action_url_without_dataareaId_no_cross_company(self):
        """Test that build_action_url doesn't add cross-company when dataAreaId is not in key."""
        key = {"CustomerAccount": "CUST001"}
        url = QueryBuilder.build_action_url(
            "https://example.com", "TestAction", "CustomersV3", key
        )

        assert "cross-company" not in url

    def test_build_action_url_entity_set_bound_no_cross_company(self):
        """Test that entity set bound actions don't get cross-company."""
        url = QueryBuilder.build_action_url(
            "https://example.com", "TestAction", "CustomersV3"
        )

        assert "cross-company" not in url
        assert (
            url
            == "https://example.com/data/CustomersV3/Microsoft.Dynamics.DataEntities.TestAction"
        )

    def test_build_action_url_unbound_no_cross_company(self):
        """Test that unbound actions don't get cross-company."""
        url = QueryBuilder.build_action_url("https://example.com", "TestAction")

        assert "cross-company" not in url
        assert (
            url == "https://example.com/data/Microsoft.Dynamics.DataEntities.TestAction"
        )

    def test_multiple_key_fields_with_dataareaId(self):
        """Test composite keys with multiple fields including dataAreaId."""
        key = {
            "dataAreaId": "USMF",
            "CustomerAccount": "CUST001",
            "InvoiceId": "INV001",
            "LineNumber": "1",
        }
        url = QueryBuilder.build_entity_url(
            "https://example.com", "SalesInvoiceLines", key
        )

        assert "cross-company=true" in url
        # Check that all key parts are present
        assert "dataAreaId='USMF'" in url
        assert "CustomerAccount='CUST001'" in url
        assert "InvoiceId='INV001'" in url
        assert "LineNumber='1'" in url

    def test_dataareaId_uppercase_in_key(self):
        """Test that DATAAREAID (uppercase) is detected properly."""
        key = {"DATAAREAID": "USMF", "CustomerAccount": "CUST001"}
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3", key)

        assert "cross-company=true" in url

    def test_mixed_case_dataareaId_in_key(self):
        """Test various case combinations of dataAreaId."""
        test_cases = [
            {"DataAreaId": "USMF"},
            {"dataareaid": "USMF"},
            {"DataAreaID": "USMF"},
            {"DATAAREAId": "USMF"},
        ]

        for key in test_cases:
            url = QueryBuilder.build_entity_url(
                "https://example.com", "CustomersV3", key
            )
            assert (
                "cross-company=true" in url
            ), f"Failed to add cross-company for key: {key}"

    def test_explicit_add_cross_company_true(self):
        """Test explicit cross-company addition even without dataAreaId."""
        key = {"CustomerAccount": "CUST001"}
        url = QueryBuilder.build_entity_url(
            "https://example.com", "CustomersV3", key, add_cross_company=True
        )

        assert "cross-company=true" in url

    def test_explicit_add_cross_company_with_dataareaId(self):
        """Test that explicit flag works with dataAreaId present."""
        key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}
        url = QueryBuilder.build_entity_url(
            "https://example.com", "CustomersV3", key, add_cross_company=True
        )

        assert "cross-company=true" in url
        # Should only appear once
        assert url.count("cross-company=true") == 1

    def test_merge_query_strings_both_empty(self):
        """Test merging empty query strings."""
        result = QueryBuilder.merge_query_strings("", "")
        assert result == ""

    def test_merge_query_strings_first_empty(self):
        """Test merging when first is empty."""
        result = QueryBuilder.merge_query_strings("", "?param=value")
        assert result == "?param=value"

    def test_merge_query_strings_second_empty(self):
        """Test merging when second is empty."""
        result = QueryBuilder.merge_query_strings("?param=value", "")
        assert result == "?param=value"

    def test_merge_query_strings_both_with_question_mark(self):
        """Test merging both strings with question marks."""
        result = QueryBuilder.merge_query_strings("?param1=value1", "?param2=value2")
        assert result == "?param1=value1&param2=value2"

    def test_merge_query_strings_no_question_marks(self):
        """Test merging strings without question marks."""
        result = QueryBuilder.merge_query_strings("param1=value1", "param2=value2")
        assert result == "?param1=value1&param2=value2"

    def test_merge_query_strings_mixed(self):
        """Test merging with mixed question marks."""
        result = QueryBuilder.merge_query_strings("?param1=value1", "param2=value2")
        assert result == "?param1=value1&param2=value2"

    def test_real_world_scenario_composite_key_with_options(self):
        """Test real-world scenario: composite key with dataAreaId and query options."""
        # This simulates what happens in get_entity when both key and options are present
        key = {"dataAreaId": "USMF", "CustomerAccount": "CUST001"}

        # Build entity URL (will add cross-company)
        url = QueryBuilder.build_entity_url("https://example.com", "CustomersV3", key)
        assert "?cross-company=true" in url

        # Simulate appending query options (like in get_entity)
        from src.d365fo_client.models import QueryOptions

        options = QueryOptions(select=["Name", "Phone"], top=10)
        query_string = QueryBuilder.build_query_string(options)

        # Merge properly
        if "?" in url:
            final_url = url + query_string.replace("?", "&")
        else:
            final_url = url + query_string

        # Should have both cross-company and the other parameters
        assert "cross-company=true" in final_url
        # Check for either URL-encoded or non-encoded versions
        assert (
            "$select=Name,Phone" in final_url or "%24select=Name%2CPhone" in final_url
        )
        assert "$top=10" in final_url or "%24top=10" in final_url
        # Should have proper separators
        assert "?cross-company=true&" in final_url
