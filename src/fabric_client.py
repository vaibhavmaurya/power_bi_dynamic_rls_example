"""Thin client over the five approved Fabric REST APIs (spec sections 12-18, 35).

Deliberately does not use XMLA/TOM and does not expose any API beyond the
approved surface: Get Semantic Model, Get Definition, Get Operation State,
Get Operation Result, Update Definition.
"""

import requests

from src.errors import (
    FabricAuthorizationFailedError,
    FabricRateLimitedError,
    GetDefinitionFailedError,
    SemanticModelNotFoundError,
    UpdateDefinitionFailedError,
)
from src.lro import wait_for_operation

DEFAULT_BASE_URL = "https://api.fabric.microsoft.com/v1"


class FabricClient:
    def __init__(
        self,
        token_provider,
        base_url: str = DEFAULT_BASE_URL,
        lro_timeout_seconds: float = 900,
        session: requests.Session = None,
    ):
        self.token_provider = token_provider
        self.base_url = base_url.rstrip("/")
        self.lro_timeout_seconds = lro_timeout_seconds
        self.session = session or requests.Session()

    def _headers(self) -> dict:
        token = self.token_provider.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _raise_for_common_errors(self, response: requests.Response, not_found_error):
        if response.status_code == 401:
            raise FabricAuthorizationFailedError(
                f"Fabric returned 401 Unauthorized: {response.text}"
            )
        if response.status_code == 403:
            raise FabricAuthorizationFailedError(
                f"Fabric returned 403 Forbidden: {response.text}"
            )
        if response.status_code == 404 and not_found_error:
            raise not_found_error(f"Fabric returned 404 Not Found: {response.text}")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise FabricRateLimitedError(
                f"Fabric rate limited the request; Retry-After={retry_after}"
            )

    def get_semantic_model(self, workspace_id: str, semantic_model_id: str) -> dict:
        url = (
            f"{self.base_url}/workspaces/{workspace_id}"
            f"/semanticModels/{semantic_model_id}"
        )
        response = self.session.get(url, headers=self._headers())

        self._raise_for_common_errors(response, SemanticModelNotFoundError)
        if not response.ok:
            raise SemanticModelNotFoundError(
                f"Failed to retrieve semantic model: {response.status_code} "
                f"{response.text}"
            )
        return response.json()

    def get_semantic_model_definition(
        self,
        workspace_id: str,
        semantic_model_id: str,
        definition_format: str = "TMDL",
    ) -> dict:
        url = (
            f"{self.base_url}/workspaces/{workspace_id}"
            f"/semanticModels/{semantic_model_id}/getDefinition"
        )
        response = self.session.post(
            url,
            headers=self._headers(),
            params={"format": definition_format},
        )

        self._raise_for_common_errors(response, None)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 202:
            return self._handle_lro(response, "definition")

        raise GetDefinitionFailedError(
            f"Get Definition failed: {response.status_code} {response.text}"
        )

    def update_semantic_model_definition(
        self,
        workspace_id: str,
        semantic_model_id: str,
        definition: dict,
        allow_purge_data: bool = False,
    ) -> dict:
        url = (
            f"{self.base_url}/workspaces/{workspace_id}"
            f"/semanticModels/{semantic_model_id}/updateDefinition"
        )
        payload = {
            "definition": definition,
            "options": {"allowPurgeData": allow_purge_data},
        }
        response = self.session.post(url, headers=self._headers(), json=payload)

        self._raise_for_common_errors(response, None)

        if response.status_code == 200:
            return response.json() if response.text else {}

        if response.status_code == 202:
            return self._handle_lro(response, "update", result_expected=False)

        raise UpdateDefinitionFailedError(
            f"Update Definition failed: {response.status_code} {response.text}"
        )

    def get_operation_state(self, operation_id: str) -> dict:
        url = f"{self.base_url}/operations/{operation_id}"
        response = self.session.get(url, headers=self._headers())
        self._raise_for_common_errors(response, None)
        response.raise_for_status()
        return response.json()

    def get_operation_result(self, operation_id: str) -> dict:
        url = f"{self.base_url}/operations/{operation_id}/result"
        response = self.session.get(url, headers=self._headers())
        self._raise_for_common_errors(response, None)
        response.raise_for_status()
        return response.json()

    def wait_for_operation(self, operation_id: str, retry_after: float = None) -> dict:
        return wait_for_operation(
            operation_id=operation_id,
            get_operation_state=self.get_operation_state,
            get_operation_result=self.get_operation_result,
            retry_after=retry_after,
            timeout_seconds=self.lro_timeout_seconds,
        )

    def _handle_lro(
        self,
        response: requests.Response,
        context: str,
        result_expected: bool = True,
    ) -> dict:
        operation_id = response.headers.get("x-ms-operation-id")
        retry_after = response.headers.get("Retry-After")
        retry_after_seconds = float(retry_after) if retry_after else None

        return wait_for_operation(
            operation_id=operation_id,
            get_operation_state=self.get_operation_state,
            get_operation_result=self.get_operation_result if result_expected else (lambda _oid: {}),
            retry_after=retry_after_seconds,
            timeout_seconds=self.lro_timeout_seconds,
        )
