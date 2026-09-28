import pytest

from src.change_detection import detect_role_changes
from src.errors import RoleDeleteNotSupportedError


def test_added_and_modified_roles_detected():
    changed_files = [
        {"path": "projects/sales/roles/abc.tmdl", "status": "modified"},
        {"path": "projects/sales/roles/NewFinanceRole.tmdl", "status": "added"},
        {"path": "projects/sales/project.json", "status": "modified"},
        {"path": "projects/other/roles/x.tmdl", "status": "modified"},
    ]

    roles = detect_role_changes(changed_files, "projects/sales/roles/")

    assert set(roles) == {"abc.tmdl", "NewFinanceRole.tmdl"}


def test_removed_role_rejected():
    changed_files = [{"path": "projects/sales/roles/abc.tmdl", "status": "removed"}]

    with pytest.raises(RoleDeleteNotSupportedError):
        detect_role_changes(changed_files, "projects/sales/roles/")


def test_renamed_role_rejected():
    changed_files = [{"path": "projects/sales/roles/abc.tmdl", "status": "renamed"}]

    with pytest.raises(RoleDeleteNotSupportedError):
        detect_role_changes(changed_files, "projects/sales/roles/")


def test_no_role_changes_returns_empty():
    changed_files = [{"path": "projects/sales/project.json", "status": "modified"}]

    assert detect_role_changes(changed_files, "projects/sales/roles/") == []
