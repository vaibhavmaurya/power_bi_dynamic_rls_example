import base64
import copy

import pytest

from src.deploy import deploy_roles
from src.errors import ConcurrentModelChangeDetectedError
from src.role_overlay import APPEND, REPLACE


def _part(path, content):
    return {
        "path": path,
        "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "payloadType": "InlineBase64",
    }


class FakeFabricClient:
    """Simulates Fabric with a single in-memory definition and no LROs."""

    def __init__(self, initial_definition, mutate_between_reads=False):
        self._definition = initial_definition
        self._reads = 0
        self._mutate_between_reads = mutate_between_reads

    def get_semantic_model(self, workspace_id, semantic_model_id):
        return {"id": semantic_model_id}

    def get_semantic_model_definition(self, workspace_id, semantic_model_id):
        # Mirrors the real Fabric API response shape: the parts list is
        # nested under a "definition" key, not returned at the top level.
        self._reads += 1
        if self._mutate_between_reads and self._reads == 2:
            self._definition["parts"].append(_part("definition/model.tmdl", "changed elsewhere"))
        return {"definition": copy.deepcopy(self._definition)}

    def update_semantic_model_definition(self, workspace_id, semantic_model_id, definition):
        self._definition = copy.deepcopy(definition)
        return {}


def test_deploy_existing_role_replace_and_verify():
    initial_definition = {
        "parts": [
            _part("definition/database.tmdl", "db"),
            _part("definition/roles/abc.tmdl", "old abc"),
        ]
    }
    fabric_client = FakeFabricClient(initial_definition)

    report = deploy_roles(
        token_provider=None,
        workspace_id="ws-1",
        semantic_model_id="model-1",
        roles={"abc.tmdl": "new abc"},
        project_key="sales",
        environment="DEV",
        fabric_client=fabric_client,
    )

    assert report.success
    assert len(report.role_results) == 1
    assert report.role_results[0].operation == REPLACE
    assert report.role_results[0].target_path == "definition/roles/abc.tmdl"


def test_deploy_new_role_append_and_verify():
    initial_definition = {"parts": [_part("definition/database.tmdl", "db")]}
    fabric_client = FakeFabricClient(initial_definition)

    report = deploy_roles(
        token_provider=None,
        workspace_id="ws-1",
        semantic_model_id="model-1",
        roles={"NewFinanceRole.tmdl": "finance role body"},
        project_key="sales",
        environment="DEV",
        fabric_client=fabric_client,
    )

    assert report.success
    assert report.role_results[0].operation == APPEND


def test_deploy_multiple_roles_single_update_call():
    initial_definition = {
        "parts": [
            _part("definition/database.tmdl", "db"),
            _part("definition/roles/abc.tmdl", "old abc"),
        ]
    }
    fabric_client = FakeFabricClient(initial_definition)
    update_calls = []
    original_update = fabric_client.update_semantic_model_definition

    def counting_update(*args, **kwargs):
        update_calls.append(1)
        return original_update(*args, **kwargs)

    fabric_client.update_semantic_model_definition = counting_update

    report = deploy_roles(
        token_provider=None,
        workspace_id="ws-1",
        semantic_model_id="model-1",
        roles={"abc.tmdl": "new abc", "finance.tmdl": "new finance"},
        project_key="sales",
        environment="DEV",
        fabric_client=fabric_client,
    )

    assert len(update_calls) == 1
    assert report.success


def test_non_rls_parts_preserved_after_deploy():
    initial_definition = {
        "parts": [
            _part("definition/database.tmdl", "db"),
            _part("definition/model.tmdl", "model"),
            _part("definition/roles/abc.tmdl", "old abc"),
        ]
    }
    fabric_client = FakeFabricClient(initial_definition)

    deploy_roles(
        token_provider=None,
        workspace_id="ws-1",
        semantic_model_id="model-1",
        roles={"abc.tmdl": "new abc"},
        project_key="sales",
        environment="DEV",
        fabric_client=fabric_client,
    )

    final_parts = {p["path"]: p["payload"] for p in fabric_client._definition["parts"]}
    assert final_parts["definition/database.tmdl"] == _part("definition/database.tmdl", "db")["payload"]
    assert final_parts["definition/model.tmdl"] == _part("definition/model.tmdl", "model")["payload"]


def test_concurrent_non_rls_change_detected():
    initial_definition = {
        "parts": [
            _part("definition/database.tmdl", "db"),
            _part("definition/roles/abc.tmdl", "old abc"),
        ]
    }
    fabric_client = FakeFabricClient(initial_definition, mutate_between_reads=True)

    with pytest.raises(ConcurrentModelChangeDetectedError):
        deploy_roles(
            token_provider=None,
            workspace_id="ws-1",
            semantic_model_id="model-1",
            roles={"abc.tmdl": "new abc"},
            project_key="sales",
            environment="DEV",
            fabric_client=fabric_client,
        )
