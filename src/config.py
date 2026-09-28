"""Loads project and environment configuration (spec sections 5-6, 9).

Deployment config (workspaceId, semanticModelId) and authentication config
(tenantId, clientId, clientSecret) are loaded from separate sources and
never mixed: environment JSON files carry no secrets, and authentication
comes only from environment variables.
"""

import json
import os
from dataclasses import dataclass

from src.role_overlay import DEFAULT_ROLE_PATH_PREFIX


@dataclass
class ProjectConfig:
    project_key: str
    role_source_path: str
    role_definition_path_prefix: str


@dataclass
class EnvironmentConfig:
    environment: str
    workspace_id: str
    semantic_model_id: str


@dataclass
class AuthConfig:
    tenant_id: str
    client_id: str
    client_secret: str


def load_project_config(project_json_path: str) -> ProjectConfig:
    with open(project_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return ProjectConfig(
        project_key=data["projectKey"],
        role_source_path=data["roleSourcePath"],
        role_definition_path_prefix=data.get(
            "roleDefinitionPathPrefix", DEFAULT_ROLE_PATH_PREFIX
        ),
    )


def load_environment_config(environment_json_path: str) -> EnvironmentConfig:
    with open(environment_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return EnvironmentConfig(
        environment=data["environment"],
        workspace_id=data["workspaceId"],
        semantic_model_id=data["semanticModelId"],
    )


def load_auth_config_from_env() -> AuthConfig:
    missing = [
        name
        for name in ("FABRIC_TENANT_ID", "FABRIC_CLIENT_ID", "FABRIC_CLIENT_SECRET")
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(
            "Missing required authentication environment variable(s): "
            + ", ".join(missing)
        )

    return AuthConfig(
        tenant_id=os.environ["FABRIC_TENANT_ID"],
        client_id=os.environ["FABRIC_CLIENT_ID"],
        client_secret=os.environ["FABRIC_CLIENT_SECRET"],
    )
