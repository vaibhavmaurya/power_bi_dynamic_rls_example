"""Deployment orchestrator (spec sections 19, 24-27, 33, 41).

Implements the full flow for a single project + environment deployment:

    Get Semantic Model
      -> Get Definition (D0)
      -> Get Definition again (D1) and diff non-target parts against D0
         (concurrent-change protection, spec section 26)
      -> Overlay all changed roles onto D1 in a single pass
      -> Update Definition once
      -> Get Definition again
      -> Verify deployed RLS content against Git

Multiple role changes are always overlaid together and submitted in one
Update Definition call (spec section 24).
"""

import copy
from dataclasses import dataclass, field

from src.errors import ConcurrentModelChangeDetectedError
from src.fabric_client import FabricClient
from src.role_overlay import DEFAULT_ROLE_PATH_PREFIX, overlay_roles
from src.verify import verify_role_deployments


@dataclass
class DeploymentReport:
    project_key: str
    environment: str
    role_results: list = field(default_factory=list)  # list[OverlayResult]
    verified: bool = False

    @property
    def success(self) -> bool:
        return self.verified


def _non_target_parts(definition: dict, target_paths: set) -> dict:
    return {
        part["path"]: part["payload"]
        for part in definition.get("parts", [])
        if part["path"] not in target_paths
    }


def deploy_roles(
    token_provider,
    workspace_id: str,
    semantic_model_id: str,
    roles: dict,
    project_key: str,
    environment: str,
    role_path_prefix: str = DEFAULT_ROLE_PATH_PREFIX,
    fabric_client: FabricClient = None,
) -> DeploymentReport:
    """Deploy one or more RLS role files to a single Fabric semantic model.

    Args:
        roles: dict mapping role file name (e.g. "abc.tmdl") to its Git
            file content.
        fabric_client: injectable for testing; a default client is created
            from `token_provider` otherwise.
    """
    client = fabric_client or FabricClient(token_provider)

    client.get_semantic_model(workspace_id, semantic_model_id)

    definition_before = client.get_semantic_model_definition(
        workspace_id, semantic_model_id
    )["definition"]

    target_paths = {role_path_prefix + name for name in roles}

    definition_latest = client.get_semantic_model_definition(
        workspace_id, semantic_model_id
    )["definition"]

    if _non_target_parts(definition_before, target_paths) != _non_target_parts(
        definition_latest, target_paths
    ):
        raise ConcurrentModelChangeDetectedError(
            "Semantic model definition changed outside the target RLS "
            "paths between reads; aborting deployment"
        )

    working_definition = copy.deepcopy(definition_latest)
    role_results = overlay_roles(working_definition, roles, role_path_prefix)

    client.update_semantic_model_definition(
        workspace_id, semantic_model_id, working_definition
    )

    definition_after = client.get_semantic_model_definition(
        workspace_id, semantic_model_id
    )["definition"]

    expected_roles = {
        role_path_prefix + name: content for name, content in roles.items()
    }
    verify_role_deployments(definition_after, expected_roles)

    return DeploymentReport(
        project_key=project_key,
        environment=environment,
        role_results=role_results,
        verified=True,
    )
