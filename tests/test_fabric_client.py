import pytest

from src.errors import (
    FabricAuthorizationFailedError,
    FabricRateLimitedError,
    GetDefinitionFailedError,
    SemanticModelNotFoundError,
    UpdateDefinitionFailedError,
)
from src.fabric_client import FabricClient


class FakeTokenProvider:
    def get_access_token(self):
        return "fake-token"


class FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}
        self.text = text or str(json_data or "")

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        # responses: list of FakeResponse returned in order per call
        self._get_responses = list(responses.get("get", []))
        self._post_responses = list(responses.get("post", []))
        self.get_calls = []
        self.post_calls = []

    def get(self, url, headers=None, **kwargs):
        self.get_calls.append(url)
        return self._get_responses.pop(0)

    def post(self, url, headers=None, **kwargs):
        self.post_calls.append((url, kwargs))
        return self._post_responses.pop(0)


def make_client(session):
    return FabricClient(FakeTokenProvider(), session=session, lro_timeout_seconds=10)


def test_get_semantic_model_success():
    session = FakeSession({"get": [FakeResponse(200, {"id": "model-1"})]})
    client = make_client(session)

    result = client.get_semantic_model("ws-1", "model-1")

    assert result == {"id": "model-1"}


def test_get_semantic_model_not_found():
    session = FakeSession({"get": [FakeResponse(404, text="not found")]})
    client = make_client(session)

    with pytest.raises(SemanticModelNotFoundError):
        client.get_semantic_model("ws-1", "missing")


def test_get_semantic_model_unauthorized():
    session = FakeSession({"get": [FakeResponse(401, text="unauthorized")]})
    client = make_client(session)

    with pytest.raises(FabricAuthorizationFailedError):
        client.get_semantic_model("ws-1", "model-1")


def test_get_definition_200_path():
    definition_response = {"definition": {"parts": [{"path": "definition/database.tmdl"}]}}
    session = FakeSession({"post": [FakeResponse(200, definition_response)]})
    client = make_client(session)

    result = client.get_semantic_model_definition("ws-1", "model-1")

    assert result == definition_response


def test_get_definition_202_lro_path():
    accepted = FakeResponse(
        202,
        headers={"x-ms-operation-id": "op-1", "Retry-After": "0"},
    )
    session = FakeSession({"post": [accepted]})
    client = make_client(session)

    final_result = {"definition": {"parts": []}}
    client.get_operation_state = lambda op_id: {"status": "Succeeded"}
    client.get_operation_result = lambda op_id: final_result

    result = client.get_semantic_model_definition("ws-1", "model-1")

    assert result == final_result


def test_get_definition_failure_raises():
    session = FakeSession({"post": [FakeResponse(500, text="boom")]})
    client = make_client(session)

    with pytest.raises(GetDefinitionFailedError):
        client.get_semantic_model_definition("ws-1", "model-1")


def test_update_definition_200_path():
    session = FakeSession({"post": [FakeResponse(200, {}, text="")]})
    client = make_client(session)

    result = client.update_semantic_model_definition(
        "ws-1", "model-1", {"parts": []}
    )

    assert result == {}
    # confirm allowPurgeData defaults to False in the payload sent
    _, kwargs = session.post_calls[0]
    assert kwargs["json"]["options"]["allowPurgeData"] is False


def test_update_definition_202_lro_path():
    accepted = FakeResponse(
        202, headers={"x-ms-operation-id": "op-2", "Retry-After": "0"}
    )
    session = FakeSession({"post": [accepted]})
    client = make_client(session)

    client.get_operation_state = lambda op_id: {"status": "Succeeded"}
    client.get_operation_result = lambda op_id: {}

    result = client.update_semantic_model_definition(
        "ws-1", "model-1", {"parts": []}
    )

    assert result == {}


def test_update_definition_failure_raises():
    session = FakeSession({"post": [FakeResponse(500, text="boom")]})
    client = make_client(session)

    with pytest.raises(UpdateDefinitionFailedError):
        client.update_semantic_model_definition("ws-1", "model-1", {"parts": []})


def test_rate_limited_raises():
    session = FakeSession(
        {"get": [FakeResponse(429, headers={"Retry-After": "5"}, text="throttled")]}
    )
    client = make_client(session)

    with pytest.raises(FabricRateLimitedError):
        client.get_semantic_model("ws-1", "model-1")
