"""Post-deployment RLS verification (spec sections 33, 38).

After Update Definition succeeds, re-read the definition and confirm the
deployed payload for each target role path matches the Git TMDL content
exactly (modulo line-ending normalization).
"""

import base64

from src.errors import PostDeploymentValidationFailedError


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def verify_role_deployment(definition: dict, target_path: str, expected_content: str) -> bool:
    """Verify a single deployed role path's payload matches expected Git content.

    Raises PostDeploymentValidationFailedError if the path is missing or the
    decoded payload does not match; returns True on success.
    """
    parts = definition.get("parts", [])
    matches = [part for part in parts if part["path"] == target_path]

    if not matches:
        raise PostDeploymentValidationFailedError(
            f"Expected RLS path '{target_path}' was not found after deployment"
        )

    decoded = base64.b64decode(matches[0]["payload"]).decode("utf-8")

    if _normalize(decoded) != _normalize(expected_content):
        raise PostDeploymentValidationFailedError(
            f"Deployed content for '{target_path}' does not match Git content"
        )

    return True


def verify_role_deployments(definition: dict, expected_roles: dict) -> list:
    """Verify multiple target_path -> expected_content pairs.

    Returns the list of verified target paths; raises on the first mismatch.
    """
    verified = []
    for target_path, expected_content in expected_roles.items():
        verify_role_deployment(definition, target_path, expected_content)
        verified.append(target_path)
    return verified
