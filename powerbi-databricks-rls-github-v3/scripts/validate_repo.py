from __future__ import annotations
import argparse, re
from common import ROOT, load_environment
GUID=re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
def validate(environment):
    cfg=load_environment(environment); errors=[]
    if not GUID.match(cfg.get("workspace_id","")): errors.append("workspace_id must be a GUID")
    sm=cfg["semantic_model"]; root=ROOT/sm["definition_path"]
    for p in [root/"definition.pbism",root/"definition"/"database.tmdl",root/"definition"/"model.tmdl"]:
        if not p.exists(): errors.append(f"Missing required model definition: {p}")
    if (root/"BOOTSTRAP_REQUIRED.txt").exists(): errors.append("Bootstrap the actual semantic model before CI/CD deployment")
    role=root/"definition"/"roles"/"DynamicUserSecurity.tmdl"
    if not role.exists(): errors.append("DynamicUserSecurity.tmdl missing")
    else:
        text=role.read_text(encoding="utf-8")
        for token in ["USERPRINCIPALNAME()","UserAccess[user_upn]","tablePermission UserAccess"]:
            if token not in text: errors.append(f"RLS role missing {token}")
    if errors:
        [print("ERROR:",e) for e in errors]; raise SystemExit(1)
    print(f"Validation successful for {environment}")
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--environment",required=True,choices=("dev","test","prod"))
    validate(p.parse_args().environment)
