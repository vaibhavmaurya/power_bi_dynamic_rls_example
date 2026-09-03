from __future__ import annotations

import argparse
import time

from common import load_environment, powerbi_request


def find_powerbi_dataset_id(workspace_id: str, display_name: str):
    body = powerbi_request(
        "GET",
        f"/groups/{workspace_id}/datasets",
        expected=(200,),
    )
    matches = [d for d in body.get("value", []) if d.get("name") == display_name]
    if len(matches) > 1:
        raise RuntimeError(f"Multiple datasets named {display_name!r}")
    return matches[0]["id"] if matches else None


def refresh(environment: str):
    cfg = load_environment(environment)
    sm = cfg["semantic_model"]

    if not sm.get("refresh_after_deploy", False):
        print("Refresh disabled by environment configuration")
        return

    workspace_id = cfg["workspace_id"]
    display_name = sm["display_name"]
    dataset_id = find_powerbi_dataset_id(workspace_id, display_name)

    if not dataset_id:
        raise RuntimeError(
            f"Power BI dataset for semantic model {display_name!r} was not found"
        )

    print(f"Starting refresh: {display_name} ({dataset_id})")

    # For service-principal calls, notifyOption is not applicable.
    # Sending no JSON body triggers a standard refresh request.
    powerbi_request(
        "POST",
        f"/groups/{workspace_id}/datasets/{dataset_id}/refreshes",
        json_body=None,
        expected=(202,),
    )

    deadline = time.time() + 1800
    while time.time() < deadline:
        history = powerbi_request(
            "GET",
            f"/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1",
            expected=(200,),
        )
        rows = history.get("value", [])
        if not rows:
            time.sleep(10)
            continue

        status = rows[0].get("status")
        print(f"Refresh status: {status}")

        if status == "Completed":
            return
        if status in ("Failed", "Cancelled", "Disabled"):
            raise RuntimeError(
                f"Semantic model refresh ended with status: {status}"
            )
        time.sleep(15)

    raise TimeoutError("Semantic model refresh did not complete in 30 minutes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--environment", required=True, choices=("dev", "test", "prod")
    )
    args = parser.parse_args()
    refresh(args.environment)
