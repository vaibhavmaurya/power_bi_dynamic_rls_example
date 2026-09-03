from __future__ import annotations
import argparse
import json
import shutil
from common import ROOT, find_item, load_environment


def render(environment: str):
    cfg = load_environment(environment)
    report = cfg["report"]
    if not report.get("enabled", False):
        print("Report deployment disabled")
        return None

    ws = cfg["workspace_id"]
    sm = cfg["semantic_model"]
    sm_item = find_item(ws, sm["display_name"], "SemanticModel")
    if not sm_item:
        raise RuntimeError("Semantic model must exist before rendering report")

    src = ROOT / report["definition_path"]
    dst = ROOT / ".build" / environment / "report"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    pbir = dst / "definition.pbir"
    if not pbir.exists():
        raise RuntimeError(
            "report/definition.pbir missing. Bootstrap the real report first."
        )

    data = json.loads(pbir.read_text(encoding="utf-8"))
    if report.get("rebind_to_deployed_semantic_model", True):
        data["datasetReference"] = {
            "byConnection": {
                "connectionString": f"semanticmodelid={sm_item['id']}"
            }
        }
        pbir.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Rebound report definition to semantic model {sm_item['id']}")

    return dst


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    render(a.environment)
