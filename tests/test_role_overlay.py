import base64

import pytest

from src.errors import DuplicateDefinitionPartError
from src.role_overlay import APPEND, REPLACE, overlay_role, overlay_roles


def _part(path, content):
    return {
        "path": path,
        "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "payloadType": "InlineBase64",
    }


def test_existing_role_is_replaced():
    definition = {
        "parts": [
            _part("definition/database.tmdl", "db"),
            _part("definition/roles/abc.tmdl", "OLD CONTENT"),
        ]
    }

    result = overlay_role(definition, "abc.tmdl", "NEW CONTENT")

    assert result.operation == REPLACE
    assert result.target_path == "definition/roles/abc.tmdl"
    assert len(definition["parts"]) == 2
    role_part = next(p for p in definition["parts"] if p["path"] == "definition/roles/abc.tmdl")
    assert base64.b64decode(role_part["payload"]).decode("utf-8") == "NEW CONTENT"
    # unrelated part untouched
    db_part = next(p for p in definition["parts"] if p["path"] == "definition/database.tmdl")
    assert base64.b64decode(db_part["payload"]).decode("utf-8") == "db"


def test_missing_role_is_appended():
    definition = {"parts": [_part("definition/database.tmdl", "db")]}

    result = overlay_role(definition, "NewFinanceRole.tmdl", "role body")

    assert result.operation == APPEND
    assert result.target_path == "definition/roles/NewFinanceRole.tmdl"
    assert len(definition["parts"]) == 2


def test_duplicate_role_path_rejected():
    definition = {
        "parts": [
            _part("definition/roles/abc.tmdl", "one"),
            _part("definition/roles/abc.tmdl", "two"),
        ]
    }

    with pytest.raises(DuplicateDefinitionPartError):
        overlay_role(definition, "abc.tmdl", "new")


def test_custom_role_path_prefix():
    definition = {"parts": []}

    result = overlay_role(
        definition, "abc.tmdl", "content", role_path_prefix="custom/roles/"
    )

    assert result.target_path == "custom/roles/abc.tmdl"


def test_multiple_roles_single_definition_update():
    definition = {
        "parts": [
            _part("definition/database.tmdl", "db"),
            _part("definition/roles/abc.tmdl", "old abc"),
        ]
    }

    results = overlay_roles(
        definition,
        {
            "abc.tmdl": "new abc",
            "finance.tmdl": "new finance",
        },
    )

    operations = {r.target_path: r.operation for r in results}
    assert operations["definition/roles/abc.tmdl"] == REPLACE
    assert operations["definition/roles/finance.tmdl"] == APPEND
    assert len(definition["parts"]) == 3


def test_non_rls_parts_preserved_exactly():
    non_rls_parts = [
        _part("definition/database.tmdl", "db"),
        _part("definition/model.tmdl", "model"),
        _part("definition/tables/Customer.tmdl", "customer"),
    ]
    definition = {"parts": [dict(p) for p in non_rls_parts]}

    overlay_role(definition, "abc.tmdl", "new role")

    for before, after in zip(
        non_rls_parts,
        [p for p in definition["parts"] if p["path"] != "definition/roles/abc.tmdl"],
    ):
        assert before["path"] == after["path"]
        assert before["payload"] == after["payload"]
