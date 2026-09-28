"""Authentication abstraction over MSAL (spec sections 7-11).

Fabric API code must depend only on the TokenProvider interface, never on a
specific MSAL application type, so the authentication mechanism can be
swapped (service principal, interactive user, device code, certificate,
workload identity federation) without touching deployment logic.
"""

from abc import ABC, abstractmethod

import msal

from src.errors import AuthenticationFailedError

FABRIC_DEFAULT_SCOPE = ["https://api.fabric.microsoft.com/.default"]
FABRIC_DELEGATED_SCOPE = [
    "https://api.fabric.microsoft.com/SemanticModel.ReadWrite.All"
]


class TokenProvider(ABC):
    """Abstraction so FabricClient never depends on a specific MSAL flow."""

    @abstractmethod
    def get_access_token(self) -> str:
        raise NotImplementedError


class ServicePrincipalTokenProvider(TokenProvider):
    """Primary CI/CD authentication: OAuth 2.0 client credentials via MSAL.

    Uses msal.ConfidentialClientApplication.acquire_token_for_client(), the
    documented method for obtaining a token as the application itself.
    """

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = list(FABRIC_DEFAULT_SCOPE)
        self.app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=self.authority,
            client_credential=client_secret,
        )

    def get_access_token(self) -> str:
        result = self.app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" not in result:
            raise AuthenticationFailedError(
                "Authentication failed: "
                + result.get(
                    "error_description",
                    result.get("error", "Unknown error"),
                )
            )

        return result["access_token"]


class InteractiveUserTokenProvider(TokenProvider):
    """Optional delegated user authentication for local dev/troubleshooting.

    Must not be used as the default GitHub CI/CD authentication method.
    """

    def __init__(self, tenant_id: str, client_id: str):
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = msal.PublicClientApplication(
            client_id=client_id,
            authority=authority,
        )
        self.scopes = list(FABRIC_DELEGATED_SCOPE)

    def get_access_token(self) -> str:
        accounts = self.app.get_accounts()

        result = None
        if accounts:
            result = self.app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0],
            )

        if not result:
            result = self.app.acquire_token_interactive(scopes=self.scopes)

        if not result or "access_token" not in result:
            raise AuthenticationFailedError(
                (result or {}).get(
                    "error_description", "Authentication failed"
                )
            )

        return result["access_token"]
