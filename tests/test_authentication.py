import pytest

from src.authentication import ServicePrincipalTokenProvider
from src.errors import AuthenticationFailedError


class FakeConfidentialClientApplication:
    def __init__(self, result, **kwargs):
        self._result = result
        self.calls = []

    def acquire_token_for_client(self, scopes):
        self.calls.append(scopes)
        return self._result


def test_service_principal_auth_success(monkeypatch):
    fake_app = FakeConfidentialClientApplication({"access_token": "fake-token"})
    monkeypatch.setattr(
        "src.authentication.msal.ConfidentialClientApplication",
        lambda **kwargs: fake_app,
    )

    provider = ServicePrincipalTokenProvider("tenant", "client", "secret")
    token = provider.get_access_token()

    assert token == "fake-token"
    assert fake_app.calls == [["https://api.fabric.microsoft.com/.default"]]


def test_service_principal_auth_failure(monkeypatch):
    fake_app = FakeConfidentialClientApplication(
        {"error": "invalid_client", "error_description": "bad secret"}
    )
    monkeypatch.setattr(
        "src.authentication.msal.ConfidentialClientApplication",
        lambda **kwargs: fake_app,
    )

    provider = ServicePrincipalTokenProvider("tenant", "client", "wrong-secret")

    with pytest.raises(AuthenticationFailedError, match="bad secret"):
        provider.get_access_token()
