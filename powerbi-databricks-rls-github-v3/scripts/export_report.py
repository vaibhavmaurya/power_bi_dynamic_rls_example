from __future__ import annotations
import argparse
import base64
import shutil
from common import ROOT, fabric_request, find_item, load_environment


def export_report(environment: str, report_id: str | None):
    cfg = load_environment(environment)
    ws = cfg["workspace_id"]
    report_cfg = cfg["report"]

    if not report_id:
        item = find_item(ws, report_cfg["display_name"], "Report")
        if not item:
            raise RuntimeError("Report not found; pass --report-id")
        report_id = item["id"]

    body = fabric_request(
        "POST",
        f"/workspaces/{ws}/reports/{report_id}/getDefinition?format=PBIR",
        expected=(200, 202),
    )
    definition = body.get("definition", body)
    parts = definition.get("parts", [])
    if not parts:
        raise RuntimeError("Fabric returned no report definition parts")

    root = ROOT / report_cfg["definition_path"]
    if root.exists():
        for child in list(root.iterdir()):
            if child.name == "README.md":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        root.mkdir(parents=True)

    for part in parts:
        if part.get("payloadType") != "InlineBase64":
            raise RuntimeError(f"Unsupported payloadType {part.get('payloadType')}")
        out = root / part["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(part["payload"]))

    print(f"Exported {len(parts)} PBIR definition parts to {root}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    p.add_argument("--report-id")
    a = p.parse_args()
    export_report(a.environment, a.report_id)
