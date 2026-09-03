from __future__ import annotations
import argparse
from common import ROOT, fabric_request, find_item, item_definition, load_environment


def deploy(environment: str):
    cfg = load_environment(environment)
    report = cfg["report"]
    if not report.get("enabled", False):
        print("Report deployment disabled")
        return

    ws = cfg["workspace_id"]
    root = ROOT / ".build" / environment / "report"
    payload = item_definition(root, "PBIR")
    existing = find_item(ws, report["display_name"], "Report")

    if existing:
        rid = existing["id"]
        print(f"Updating report {report['display_name']} ({rid})")
        fabric_request(
            "POST",
            f"/workspaces/{ws}/reports/{rid}/updateDefinition?updateMetadata=true",
            json_body=payload,
            expected=(200, 202),
        )
    else:
        print(f"Creating report {report['display_name']}")
        body = {
            "displayName": report["display_name"],
            "description": report.get("description", ""),
            **payload,
        }
        fabric_request(
            "POST", f"/workspaces/{ws}/reports",
            json_body=body, expected=(201, 202)
        )

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    deploy(a.environment)
