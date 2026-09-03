from __future__ import annotations
import argparse

from common import fabric_request, find_item, load_environment
from ensure_connection import ensure


def bind(environment: str):
    cfg = load_environment(environment)
    ws = cfg["workspace_id"]
    sm = cfg["semantic_model"]
    conn = sm.get("connection", {})

    # Resolves an existing connection ID or creates the connection from the
    # approved request template, depending on connection.mode.
    connection_id = ensure(environment)

    item = find_item(ws, sm["display_name"], "SemanticModel")
    if not item:
        raise RuntimeError("Semantic model not found before connection binding")

    details = conn.get("connection_details")
    connectivity = conn.get("connectivity_type")
    if not details or not connectivity:
        raise RuntimeError(
            "connection_details and connectivity_type are required for binding"
        )

    fabric_request(
        "POST",
        f"/workspaces/{ws}/semanticModels/{item['id']}/bindConnection",
        json_body={
            "connectionBinding": {
                "id": connection_id,
                "connectivityType": connectivity,
                "connectionDetails": details,
            }
        },
        expected=(200,),
    )
    print(f"Bound semantic model to Fabric connection {connection_id}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    bind(a.environment)
