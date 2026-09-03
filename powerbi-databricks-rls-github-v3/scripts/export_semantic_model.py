from __future__ import annotations

import argparse
import base64
import shutil
from pathlib import Path

from common import ROOT, fabric_request, find_item, load_environment


def export_model(environment: str, semantic_model_id: str | None):
    cfg = load_environment(environment)
    workspace_id = cfg["workspace_id"]
    sm_cfg = cfg["semantic_model"]
    model_root = ROOT / sm_cfg["definition_path"]

    if not semantic_model_id:
        item = find_item(
            workspace_id, sm_cfg["display_name"], "SemanticModel"
        )
        if not item:
            raise RuntimeError(
                "Semantic model not found by configured display name; "
                "pass --semantic-model-id."
            )
        semantic_model_id = item["id"]

    body = fabric_request(
        "POST",
        f"/workspaces/{workspace_id}/semanticModels/"
        f"{semantic_model_id}/getDefinition?format=TMDL",
        expected=(200, 202),
    )

    definition = body.get("definition", body)
    parts = definition.get("parts", [])
    if not parts:
        raise RuntimeError("Fabric returned no semantic model definition parts")

    # Replace only definition content; keep repository docs outside this folder.
    for child in list(model_root.iterdir()):
        if child.name in {"README.md"}:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for part in parts:
        if part.get("payloadType") != "InlineBase64":
            raise RuntimeError(
                f"Unsupported payload type: {part.get('payloadType')}"
            )
        out = model_root / part["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(part["payload"]))

    print(
        f"Exported {len(parts)} definition parts for semantic model "
        f"{semantic_model_id} into {model_root}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--environment", required=True, choices=("dev", "test", "prod")
    )
    parser.add_argument("--semantic-model-id")
    args = parser.parse_args()
    export_model(args.environment, args.semantic_model_id)
