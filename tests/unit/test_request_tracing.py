"""Unit tests for D365FO service request tracing.

Reference:
  https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/data-entities/service-request-tracing
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from d365fo_client.exceptions import ActionError, EntityError, FOClientError
from d365fo_client.models import FOClientConfig
from d365fo_client.session import SessionManager, _load_or_create_trace_client_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**kwargs) -> FOClientConfig:
    return FOClientConfig(base_url="https://test.dynamics.com", **kwargs)


def _make_session_manager(config: FOClientConfig) -> SessionManager:
    mock_auth = MagicMock()
    mock_auth.get_token = AsyncMock(return_value="mock-token")
    return SessionManager(config, mock_auth)


# ---------------------------------------------------------------------------
# 1. Per-request UUID is unique on every call
# ---------------------------------------------------------------------------


class TestTracingHeadersUniquePerCall:
    def test_each_call_returns_different_request_id(self):
        """get_tracing_headers() must return a fresh UUID on every invocation."""
        sm = _make_session_manager(_make_config(enable_request_tracing=True))

        h1 = sm.get_tracing_headers()
        h2 = sm.get_tracing_headers()
        h3 = sm.get_tracing_headers()

        # All three must have the header
        assert "x-ms-client-request-id" in h1
        assert "x-ms-client-request-id" in h2
        assert "x-ms-client-request-id" in h3

        # All three must be valid UUIDs
        for h in (h1, h2, h3):
            uuid.UUID(h["x-ms-client-request-id"])

        # All three must differ
        ids = {h1["x-ms-client-request-id"], h2["x-ms-client-request-id"], h3["x-ms-client-request-id"]}
        assert len(ids) == 3, "Expected three distinct request IDs"

    def test_header_value_is_valid_uuid4(self):
        sm = _make_session_manager(_make_config(enable_request_tracing=True))
        h = sm.get_tracing_headers()
        parsed = uuid.UUID(h["x-ms-client-request-id"])
        assert parsed.version == 4


# ---------------------------------------------------------------------------
# 2. Disabled tracing returns empty dict
# ---------------------------------------------------------------------------


class TestTracingDisabled:
    def test_disabled_returns_empty_headers(self):
        sm = _make_session_manager(_make_config(enable_request_tracing=False))
        assert sm.get_tracing_headers() == {}

    def test_disabled_no_trace_client_id(self):
        sm = _make_session_manager(_make_config(enable_request_tracing=False))
        assert sm.trace_client_id == ""

    @pytest.mark.asyncio
    async def test_disabled_no_session_header(self):
        """When tracing is off the x-ms-client-session-id must not be in session headers."""
        sm = _make_session_manager(_make_config(enable_request_tracing=False))

        captured_headers: dict = {}
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.headers = MagicMock()
        mock_session.headers.update = lambda h: captured_headers.update(h)

        with patch("aiohttp.TCPConnector"), patch("aiohttp.ClientTimeout"), \
             patch("aiohttp.ClientSession", return_value=mock_session):
            await sm.get_session()

        assert "x-ms-client-session-id" not in captured_headers


# ---------------------------------------------------------------------------
# 3. User-supplied trace_client_id is honoured
# ---------------------------------------------------------------------------


class TestCustomTraceClientId:
    CUSTOM_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    def test_custom_id_used_instead_of_generated(self, tmp_path):
        """If trace_client_id is set in config it must be used as-is."""
        config = _make_config(
            enable_request_tracing=True, trace_client_id=self.CUSTOM_ID
        )
        with patch(
            "d365fo_client.session._TRACE_CLIENT_ID_FILE",
            tmp_path / "trace_client_id",
        ):
            sm = _make_session_manager(config)

        assert sm.trace_client_id == self.CUSTOM_ID

    def test_load_or_create_returns_override_immediately(self, tmp_path):
        result = _load_or_create_trace_client_id(self.CUSTOM_ID)
        assert result == self.CUSTOM_ID


# ---------------------------------------------------------------------------
# 4. Stable trace_client_id – same per instance, persisted across calls
# ---------------------------------------------------------------------------


class TestStableTraceClientId:
    def test_same_instance_same_id(self):
        """The trace_client_id must not change within a session manager instance."""
        sm = _make_session_manager(_make_config(enable_request_tracing=True))
        id1 = sm.trace_client_id
        id2 = sm.trace_client_id
        assert id1 == id2

    def test_id_is_valid_uuid(self):
        sm = _make_session_manager(_make_config(enable_request_tracing=True))
        uuid.UUID(sm.trace_client_id)  # raises if invalid

    def test_id_persisted_to_disk(self, tmp_path):
        """A newly generated ID must be written to the trace_client_id file."""
        trace_file = tmp_path / "trace_client_id"
        with patch("d365fo_client.session._TRACE_CLIENT_ID_FILE", trace_file):
            sm = _make_session_manager(_make_config(enable_request_tracing=True))
            assert trace_file.exists()
            assert trace_file.read_text().strip() == sm.trace_client_id

    def test_id_loaded_from_existing_file(self, tmp_path):
        """A pre-existing trace_client_id file must be loaded, not regenerated."""
        existing_id = str(uuid.uuid4())
        trace_file = tmp_path / "trace_client_id"
        trace_file.write_text(existing_id)

        with patch("d365fo_client.session._TRACE_CLIENT_ID_FILE", trace_file):
            sm = _make_session_manager(_make_config(enable_request_tracing=True))

        assert sm.trace_client_id == existing_id


# ---------------------------------------------------------------------------
# 5. ms-dyn-aid from response is surfaced in exceptions
# ---------------------------------------------------------------------------


class TestActivityIdInExceptions:
    def test_fo_client_error_carries_activity_id(self):
        err = FOClientError("test error", activity_id="abc-123", request_id="req-456")
        assert err.activity_id == "abc-123"
        assert err.request_id == "req-456"
        assert str(err) == "test error"

    def test_fo_client_error_to_dict(self):
        err = FOClientError("something failed", activity_id="aid-1", request_id="rid-1")
        d = err.to_dict()
        assert d["error"] == "something failed"
        assert d["ms_dyn_aid"] == "aid-1"
        assert d["x_ms_client_request_id"] == "rid-1"

    def test_entity_error_inherits_tracing_fields(self):
        err = EntityError("entity failed", activity_id="ent-aid")
        assert err.activity_id == "ent-aid"
        assert err.request_id is None

    def test_action_error_inherits_tracing_fields(self):
        err = ActionError("action failed", activity_id="act-aid", request_id="req-1")
        assert err.activity_id == "act-aid"
        assert err.request_id == "req-1"

    def test_to_dict_omits_none_tracing_fields(self):
        """When there is no activity_id the key must not appear in to_dict()."""
        err = FOClientError("bare error")
        d = err.to_dict()
        assert "ms_dyn_aid" not in d
        assert "x_ms_client_request_id" not in d

    @pytest.mark.asyncio
    async def test_crud_error_includes_activity_id(self):
        """EntityError raised by CrudOperations must carry ms-dyn-aid from response."""
        from d365fo_client.crud import CrudOperations

        config = _make_config(enable_request_tracing=True)
        mock_auth = MagicMock()
        mock_auth.get_token = AsyncMock(return_value="tok")
        sm = SessionManager(config, mock_auth)

        # Build a mock aiohttp response that returns 404 + ms-dyn-aid header
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.headers = {"ms-dyn-aid": "server-activity-id-42"}
        mock_response.text = AsyncMock(return_value="Not found")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        with patch.object(sm, "get_session", return_value=mock_session):
            crud = CrudOperations(sm, "https://test.dynamics.com")
            with pytest.raises(EntityError) as exc_info:
                await crud.get_entities("CustomersV3")

        assert exc_info.value.activity_id == "server-activity-id-42"
