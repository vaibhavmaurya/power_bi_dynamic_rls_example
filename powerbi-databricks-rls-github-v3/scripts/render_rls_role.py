from __future__ import annotations
import argparse
import shutil
from pathlib import Path

from common import ROOT, load_environment

VALID_MEMBER_TYPES = {"user", "group", "auto", "activeDirectory"}


def q(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def render(environment: str, output_root: str = ".build"):
    cfg = load_environment(environment)
    sm = cfg["semantic_model"]
    rls = sm["rls"]
    role_name = rls["role_name"]

    src_root = ROOT / sm["definition_path"]
    build_root = ROOT / output_root / environment / "semantic-model"

    if build_root.exists():
        shutil.rmtree(build_root)
    shutil.copytree(src_root, build_root)

    template = (ROOT / "templates" / "DynamicUserSecurity.tmdl.tpl").read_text(
        encoding="utf-8"
    )
    template = template.replace(
        "role DynamicUserSecurity", f"role {q(role_name)}"
    )

    members = []
    for member in rls.get("members", []):
        name = member["name"]
        typ = member.get("type", "user")
        if typ not in VALID_MEMBER_TYPES:
            raise RuntimeError(f"Unsupported TMDL role-member type: {typ}")
        if typ == "user":
            members.append(f"\tmember {q(name)}")
        elif typ in ("group", "auto", "activeDirectory"):
            members.append(f"\tmember {q(name)} = {typ}")

    role_text = template.replace(
        "{{MEMBERS}}", "\n".join(members)
    ).rstrip() + "\n"

    role_path = (
        build_root / "definition" / "roles" /
        "DynamicUserSecurity.tmdl"
    )
    role_path.parent.mkdir(parents=True, exist_ok=True)
    role_path.write_text(role_text, encoding="utf-8")

    print(f"Rendered {len(members)} role member(s) into {role_path}")
    return build_root


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True, choices=("dev","test","prod"))
    parser.add_argument("--output-root", default=".build")
    args = parser.parse_args()
    render(args.environment, args.output_root)
