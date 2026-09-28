"""Replace-or-append RLS role overlay (spec sections 20-23).

`overlay_role` never sends a partial definition on its own — callers are
responsible for retrieving the complete definition first and submitting the
complete (overlaid) definition back to Fabric, since Update Definition
overrides whatever it is given.
"""

import base64
from dataclasses import dataclass

from src.errors import DuplicateDefinitionPartError

REPLACE = "REPLACE"
APPEND = "APPEND"

DEFAULT_ROLE_PATH_PREFIX = "definition/roles/"


@dataclass
class OverlayResult:
    target_path: str
    operation: str


def overlay_role(
    definition: dict,
    role_file_name: str,
    role_content: str,
    role_path_prefix: str = DEFAULT_ROLE_PATH_PREFIX,
) -> OverlayResult:
    """Replace or append a single RLS role part in-place on `definition`.

    `definition` is mutated in place (its `parts` list) and also the source
    of truth for the return value's target_path/operation, matching the
    contract in spec section 23.
    """
    target_path = role_path_prefix + role_file_name

    payload = base64.b64encode(role_content.encode("utf-8")).decode("ascii")

    parts = definition["parts"]
    matches = [part for part in parts if part["path"] == target_path]

    new_part = {
        "path": target_path,
        "payload": payload,
        "payloadType": "InlineBase64",
    }

    if len(matches) > 1:
        raise DuplicateDefinitionPartError(target_path)

    if len(matches) == 1:
        index = parts.index(matches[0])
        parts[index] = new_part
        operation = REPLACE
    else:
        parts.append(new_part)
        operation = APPEND

    return OverlayResult(target_path=target_path, operation=operation)


def overlay_roles(
    definition: dict,
    roles: dict,
    role_path_prefix: str = DEFAULT_ROLE_PATH_PREFIX,
) -> list:
    """Overlay multiple roles onto a single definition (spec section 24).

    `roles` maps role_file_name -> role_content. Overlays are applied in a
    single pass so a single Update Definition call can be issued afterward.
    """
    return [
        overlay_role(definition, role_file_name, role_content, role_path_prefix)
        for role_file_name, role_content in roles.items()
    ]
