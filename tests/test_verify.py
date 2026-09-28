import base64

import pytest

from src.errors import PostDeploymentValidationFailedError
from src.verify import verify_role_deployment, verify_role_deployments


def _definition_with(path, content):
    return {
        "parts": [
            {
                "path": path,
                "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "payloadType": "InlineBase64",
            }
        ]
    }


def test_matching_payload_passes():
    definition = _definition_with("definition/roles/abc.tmdl", "role body")

    assert verify_role_deployment(definition, "definition/roles/abc.tmdl", "role body")


def test_line_ending_normalization():
    definition = _definition_with("definition/roles/abc.tmdl", "line1\r\nline2\r\n")

    assert verify_role_deployment(
        definition, "definition/roles/abc.tmdl", "line1\nline2\n"
    )


def test_missing_path_fails():
    definition = _definition_with("definition/roles/other.tmdl", "content")

    with pytest.raises(PostDeploymentValidationFailedError):
        verify_role_deployment(definition, "definition/roles/abc.tmdl", "content")


def test_mismatched_payload_fails():
    definition = _definition_with("definition/roles/abc.tmdl", "deployed content")

    with pytest.raises(PostDeploymentValidationFailedError):
        verify_role_deployment(definition, "definition/roles/abc.tmdl", "git content")


def test_multiple_roles_all_verified():
    definition = {
        "parts": [
            {
                "path": "definition/roles/abc.tmdl",
                "payload": base64.b64encode(b"abc body").decode("ascii"),
                "payloadType": "InlineBase64",
            },
            {
                "path": "definition/roles/finance.tmdl",
                "payload": base64.b64encode(b"finance body").decode("ascii"),
                "payloadType": "InlineBase64",
            },
        ]
    }

    verified = verify_role_deployments(
        definition,
        {
            "definition/roles/abc.tmdl": "abc body",
            "definition/roles/finance.tmdl": "finance body",
        },
    )

    assert set(verified) == {
        "definition/roles/abc.tmdl",
        "definition/roles/finance.tmdl",
    }
