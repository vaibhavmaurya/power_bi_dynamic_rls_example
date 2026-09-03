from __future__ import annotations
import argparse
from common import ROOT, fabric_request, find_item, item_definition, load_environment


def deploy(environment: str):
    cfg = load_environment(environment)
    ws = cfg["workspace_id"]
    sm = cfg["semantic_model"]
    model_root = ROOT / ".build" / environment / "semantic-model"
    payload = item_definition(model_root, "TMDL")
    existing = find_item(ws, sm["display_name"], "SemanticModel")

    if existing:
        model_id = existing["id"]
        print(f"Updating semantic model {sm['display_name']} ({model_id})")
        fabric_request(
            "POST",
            f"/workspaces/{ws}/semanticModels/{model_id}/updateDefinition?updateMetadata=true",
            json_body=payload,
            expected=(200, 202),
        )
    else:
        print(f"Creating semantic model {sm['display_name']}")
        body = {
            "displayName": sm["display_name"],
            "description": sm.get("description", ""),
            **payload,
        }
        fabric_request(
            "POST", f"/workspaces/{ws}/semanticModels",
            json_body=body, expected=(201, 202)
        )
        existing = find_item(ws, sm["display_name"], "SemanticModel")
        if not existing:
            raise RuntimeError("Semantic model creation completed but item not found")
        model_id = existing["id"]

    print(f"SEMANTIC_MODEL_ID={model_id}")
    return model_id


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    deploy(a.environment)
