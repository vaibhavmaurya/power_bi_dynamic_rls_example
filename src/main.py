"""CLI entry point invoked by GitHub Actions (spec sections 27-28, 41).

Usage:
    python -m src.main --project projects/sales/project.json \\
        --environment projects/sales/environments/dev.json \\
        --base-ref origin/main

Detects changed .tmdl role files against --base-ref, deploys them, prints a
GitHub-style deployment report, and exits non-zero on any failure so the
`RLS / DEV Deployment` (or equivalent) check fails the PR.
"""

import argparse
import os
import subprocess
import sys

from src.authentication import ServicePrincipalTokenProvider
from src.change_detection import detect_role_changes
from src.config import load_auth_config_from_env, load_environment_config, load_project_config
from src.deploy import deploy_roles
from src.errors import RlsGovernanceError


def _git_changed_files(base_ref: str) -> list:
    output = subprocess.check_output(
        ["git", "diff", "--name-status", f"{base_ref}...HEAD"],
        text=True,
    )

    status_map = {
        "A": "added",
        "M": "modified",
        "D": "removed",
        "R": "renamed",
    }

    changed = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        code = parts[0][0]
        path = parts[-1]
        changed.append({"path": path, "status": status_map.get(code, "modified")})
    return changed


def _read_role_files(role_source_path: str, role_file_names: list) -> dict:
    roles = {}
    for name in role_file_names:
        full_path = os.path.join(role_source_path, name)
        with open(full_path, "r", encoding="utf-8") as f:
            roles[name] = f.read()
    return roles


def _print_report(report, check_name: str) -> None:
    lines = [check_name, "", f"Project: {report.project_key}", f"Environment: {report.environment}", ""]
    lines.append("Roles:")
    for result in report.role_results:
        status = "REPLACED" if result.operation == "REPLACE" else "APPENDED"
        lines.append(f"  {result.target_path}: {status} ✓")
    lines.append("")
    lines.append(f"Verification: {'PASSED' if report.verified else 'FAILED'}")
    lines.append("")
    lines.append(f"RESULT: {'SUCCESS' if report.success else 'FAILURE'}")

    text = "\n".join(lines)
    print(text)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Deploy RLS role changes to a Fabric semantic model")
    parser.add_argument("--project", required=True, help="Path to project.json")
    parser.add_argument("--environment", required=True, help="Path to environment JSON")
    parser.add_argument("--base-ref", default="origin/main", help="Git ref to diff against")
    parser.add_argument(
        "--check-name",
        default="RLS / DEV Deployment",
        help="Label used in the printed report",
    )
    args = parser.parse_args(argv)

    try:
        project_config = load_project_config(args.project)
        environment_config = load_environment_config(args.environment)
        auth_config = load_auth_config_from_env()

        changed_files = _git_changed_files(args.base_ref)
        role_file_names = detect_role_changes(changed_files, project_config.role_source_path)

        if not role_file_names:
            print("No RLS role changes detected; nothing to deploy.")
            return 0

        roles = _read_role_files(project_config.role_source_path, role_file_names)

        token_provider = ServicePrincipalTokenProvider(
            auth_config.tenant_id, auth_config.client_id, auth_config.client_secret
        )

        report = deploy_roles(
            token_provider=token_provider,
            workspace_id=environment_config.workspace_id,
            semantic_model_id=environment_config.semantic_model_id,
            roles=roles,
            project_key=project_config.project_key,
            environment=environment_config.environment,
            role_path_prefix=project_config.role_definition_path_prefix,
        )

        _print_report(report, args.check_name)
        return 0 if report.success else 1

    except RlsGovernanceError as exc:
        print(f"RLS deployment failed [{exc.code}]: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
