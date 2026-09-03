from __future__ import annotations
import argparse
import json
import re
from common import ROOT, load_environment

GUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
ROLES = {"Admin","Member","Contributor","Viewer"}
PTYPES = {"User","Group","ServicePrincipal","ServicePrincipalProfile","EntireTenant"}
MEMBER_TYPES = {"user","group","auto","activeDirectory"}

PLACEHOLDER_GUIDS = {
    "00000000-0000-0000-0000-000000000000",
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
    "33333333-3333-3333-3333-333333333333",
}

def validate(environment):
    cfg = load_environment(environment)
    errors, warnings = [], []
    ws = cfg.get("workspace_id","")
    if not GUID.match(ws):
        errors.append("workspace_id must be a GUID")
    if ws in PLACEHOLDER_GUIDS:
        warnings.append("workspace_id is still a placeholder")

    sm = cfg.get("semantic_model", {})
    root = ROOT / sm.get("definition_path","")
    required = [
        root / "definition.pbism",
        root / "definition" / "database.tmdl",
        root / "definition" / "model.tmdl",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Required semantic-model definition part missing: {p}")

    if (root / "BOOTSTRAP_REQUIRED.txt").exists():
        errors.append(
            "Semantic model is still the bootstrap placeholder. "
            "Export the actual semantic model before deployment."
        )

    tables = list((root / "definition" / "tables").glob("*.tmdl")) \
        if (root / "definition" / "tables").exists() else []
    if not tables:
        errors.append("No semantic-model table TMDL files; bootstrap actual model")

    rls = sm.get("rls", {})
    if not rls.get("role_name"):
        errors.append("semantic_model.rls.role_name is required")
    if not rls.get("members"):
        errors.append("At least one RLS role member/group must be configured")
    for m in rls.get("members", []):
        if not m.get("name"):
            errors.append("RLS member.name is required")
        if m.get("type","user") not in MEMBER_TYPES:
            errors.append(f"Unsupported RLS member type: {m.get('type')}")

    conn = sm.get("connection", {})
    if conn.get("mode") == "existing":
        cid = conn.get("connection_id","")
        if not GUID.match(cid):
            errors.append("Existing connection_id must be a GUID")
        if cid in PLACEHOLDER_GUIDS:
            warnings.append("Fabric connection_id is still a placeholder")
    elif conn.get("mode") == "create":
        rf = conn.get("create_request_file")
        if not rf or not (ROOT / rf).exists():
            errors.append("create mode requires an existing create_request_file")
    else:
        errors.append("connection.mode must be existing or create")

    for x in cfg.get("workspace_access", []):
        pid = x.get("principal_id","")
        if not GUID.match(pid):
            errors.append(f"Invalid workspace principal_id: {pid}")
        if pid in PLACEHOLDER_GUIDS:
            warnings.append(f"Workspace principal {pid} is still a placeholder")
        if x.get("role") not in ROLES:
            errors.append(f"Invalid workspace role: {x.get('role')}")
        if x.get("principal_type") not in PTYPES:
            errors.append(f"Invalid principal type: {x.get('principal_type')}")

    report = cfg.get("report", {})
    if report.get("enabled"):
        rr = ROOT / report.get("definition_path","")
        if (rr / "BOOTSTRAP_REQUIRED.txt").exists():
            errors.append(
                "Report is still the bootstrap placeholder. "
                "Export the actual PBIR report before deployment."
            )
        if not (rr / "definition.pbir").exists():
            errors.append("Report enabled but report/definition.pbir is missing")
        if not (rr / "definition").exists():
            errors.append("Report enabled but PBIR definition/ folder is missing")

    for case in cfg.get("security_tests", {}).get("cases", []):
        for field in ("name","effective_username","query","expected_values","column"):
            if field not in case:
                errors.append(f"Security test missing field {field}")

    for w in sorted(set(warnings)):
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        raise SystemExit(1)
    print(f"Validation successful for {environment}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    validate(a.environment)
