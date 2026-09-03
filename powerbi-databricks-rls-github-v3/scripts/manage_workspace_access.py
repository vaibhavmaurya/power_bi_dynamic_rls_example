from __future__ import annotations

import argparse

from common import fabric_request, load_environment


def current_assignments(workspace_id: str):
    body = fabric_request(
        "GET",
        f"/workspaces/{workspace_id}/roleAssignments",
        expected=(200,),
    )
    return body.get("value", [])


def ensure_workspace_access(environment: str):
    cfg = load_environment(environment)
    workspace_id = cfg["workspace_id"]
    desired = cfg.get("workspace_access", [])

    existing = current_assignments(workspace_id)
    by_principal = {
        x.get("principal", {}).get("id"): x
        for x in existing
        if x.get("principal", {}).get("id")
    }

    for entry in desired:
        principal_id = entry["principal_id"]
        principal_type = entry["principal_type"]
        desired_role = entry["role"]

        found = by_principal.get(principal_id)
        if not found:
            print(f"Adding {principal_type} {principal_id} as {desired_role}")
            fabric_request(
                "POST",
                f"/workspaces/{workspace_id}/roleAssignments",
                json_body={
                    "principal": {
                        "id": principal_id,
                        "type": principal_type,
                    },
                    "role": desired_role,
                },
                expected=(201,),
            )
            continue

        if found.get("role") != desired_role:
            assignment_id = found["id"]
            print(
                f"Updating {principal_id}: "
                f"{found.get('role')} -> {desired_role}"
            )
            fabric_request(
                "PATCH",
                f"/workspaces/{workspace_id}/roleAssignments/{assignment_id}",
                json_body={"role": desired_role},
                expected=(200,),
            )
        else:
            print(f"No change: {principal_id} already has {desired_role}")

    print(
        "Note: this script is additive/update-only. "
        "It intentionally does not remove principals that are absent from Git."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True, choices=("dev", "test", "prod"))
    args = parser.parse_args()
    ensure_workspace_access(args.environment)
