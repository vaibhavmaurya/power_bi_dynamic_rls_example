from __future__ import annotations

import argparse

from common import fabric_request, find_item, load_environment


def bind_connections(environment: str):
    cfg = load_environment(environment)
    workspace_id = cfg["workspace_id"]
    sm = cfg["semantic_model"]

    bindings = sm.get("connection_bindings", [])
    if not bindings:
        print("No semantic-model connection bindings configured")
        return

    item = find_item(workspace_id, sm["display_name"], "SemanticModel")
    if not item:
        raise RuntimeError("Semantic model must exist before connection binding")

    semantic_model_id = item["id"]

    for binding in bindings:
        required = {"connection_id", "connectivity_type", "connection_details"}
        missing = required.difference(binding)
        if missing:
            raise RuntimeError(
                f"Connection binding missing fields: {sorted(missing)}"
            )

        body = {
            "connectionBinding": {
                "id": binding["connection_id"],
                "connectivityType": binding["connectivity_type"],
                "connectionDetails": binding["connection_details"],
            }
        }

        print(
            "Binding semantic model datasource reference to connection "
            f"{binding['connection_id']}"
        )
        fabric_request(
            "POST",
            f"/workspaces/{workspace_id}/semanticModels/"
            f"{semantic_model_id}/bindConnection",
            json_body=body,
            expected=(200,),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--environment", required=True, choices=("dev", "test", "prod")
    )
    args = parser.parse_args()
    bind_connections(args.environment)
