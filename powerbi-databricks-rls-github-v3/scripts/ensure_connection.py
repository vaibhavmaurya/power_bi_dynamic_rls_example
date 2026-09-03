from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from common import ROOT, fabric_request, load_environment


def substitute_secrets(obj):
    if isinstance(obj, dict):
        return {k: substitute_secrets(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute_secrets(v) for v in obj]
    if isinstance(obj, str) and obj.startswith("${ENV:") and obj.endswith("}"):
        env_name = obj[6:-1]
        value = os.getenv(env_name)
        if value is None:
            raise RuntimeError(f"Missing required secret environment variable: {env_name}")
        return value
    return obj


def ensure(environment: str):
    cfg = load_environment(environment)
    conn = cfg["semantic_model"].get("connection", {})
    mode = conn.get("mode", "existing")

    if mode == "existing":
        connection_id = conn.get("connection_id")
        if not connection_id:
            raise RuntimeError("connection.mode=existing requires connection_id")
        print(f"Using existing Fabric connection: {connection_id}")
        return connection_id

    if mode != "create":
        raise RuntimeError("connection.mode must be existing or create")

    request_file = conn.get("create_request_file")
    if not request_file:
        raise RuntimeError("connection.mode=create requires create_request_file")

    payload = json.loads((ROOT / request_file).read_text(encoding="utf-8"))
    payload = substitute_secrets(payload)

    result = fabric_request(
        "POST", "/connections", json_body=payload, expected=(201, 202)
    )
    connection_id = (result or {}).get("id")
    if not connection_id:
        raise RuntimeError(
            "Connection was created but response did not contain id. "
            "Use List Connections/API to resolve it and set connection_id."
        )
    print(f"Created Fabric connection: {connection_id}")
    return connection_id


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    ensure(a.environment)
