"""Detect changed/added/deleted RLS role files for a project (spec section 34).

ADD and UPDATE (replace) are supported; RENAME and DELETE are rejected so a
role removed from Git can never silently delete the corresponding Fabric
role.
"""

from src.errors import RoleDeleteNotSupportedError


def detect_role_changes(changed_files: list, role_source_path: str) -> list:
    """Return the .tmdl role file names (relative to role_source_path) that
    were added or modified among `changed_files`.

    Args:
        changed_files: list of dicts like {"path": str, "status": "added" |
            "modified" | "removed" | "renamed"}, as reported by a GitHub PR
            diff.
        role_source_path: e.g. "projects/sales/roles/".

    Raises:
        RoleDeleteNotSupportedError: if a role file under role_source_path
            was removed or renamed.
    """
    if not role_source_path.endswith("/"):
        role_source_path += "/"

    role_file_names = []

    for change in changed_files:
        path = change["path"]
        if not path.startswith(role_source_path) or not path.endswith(".tmdl"):
            continue

        status = change.get("status")
        role_file_name = path[len(role_source_path):]

        if status in ("removed", "renamed"):
            raise RoleDeleteNotSupportedError(
                f"Role file '{path}' was {status}; role deletion/rename is "
                "not supported in this POC"
            )

        if status in ("added", "modified"):
            role_file_names.append(role_file_name)

    return role_file_names
