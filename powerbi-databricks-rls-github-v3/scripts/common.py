from __future__ import annotations

import base64
import io
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
FABRIC_BASE = "https://api.fabric.microsoft.com/v1"
PBI_BASE = "https://api.powerbi.com/v1.0/myorg"
RETRIABLE = {429, 500, 502, 503, 504}


class ApiError(RuntimeError):
    pass


def load_environment(name: str) -> dict[str, Any]:
    path = ROOT / "config" / "environments" / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Environment config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def bearer_headers(token: str, content_type: str = "application/json") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": content_type}


def _absolute_fabric_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    return FABRIC_BASE + (path_or_url if path_or_url.startswith("/") else "/" + path_or_url)


def _request_with_retry(method, url, headers, *, json_body=None, data=None,
                        timeout=120, max_attempts=6):
    for attempt in range(1, max_attempts + 1):
        response = requests.request(
            method, url, headers=headers, json=json_body, data=data, timeout=timeout
        )
        if response.status_code not in RETRIABLE or attempt == max_attempts:
            return response
        time.sleep(int(response.headers.get("Retry-After", min(2 ** attempt, 30))))
    raise AssertionError("unreachable")


def fabric_request(method: str, path_or_url: str, *, json_body=None,
                   expected=(200, 201, 202)):
    url = _absolute_fabric_url(path_or_url)
    r = _request_with_retry(
        method, url, bearer_headers(required_env("FABRIC_TOKEN")), json_body=json_body
    )
    if r.status_code not in expected:
        raise ApiError(f"{method} {url} -> {r.status_code}: {r.text}")
    if r.status_code == 202:
        location = r.headers.get("Location")
        if not location:
            raise ApiError(f"202 without Location header: {url}")
        return wait_for_lro(location)
    return r.json() if r.content else None


def powerbi_request(method: str, path: str, *, json_body=None,
                    expected=(200, 201, 202)):
    url = f"{PBI_BASE}{path}"
    r = _request_with_retry(
        method, url, bearer_headers(required_env("POWERBI_TOKEN")), json_body=json_body
    )
    if r.status_code not in expected:
        raise ApiError(f"{method} {url} -> {r.status_code}: {r.text}")
    return r.json() if r.content else None


def powerbi_binary_request(method: str, path: str, *, json_body=None,
                           expected=(200,)):
    url = f"{PBI_BASE}{path}"
    r = _request_with_retry(
        method, url, bearer_headers(required_env("POWERBI_TOKEN")), json_body=json_body
    )
    if r.status_code not in expected:
        raise ApiError(f"{method} {url} -> {r.status_code}: {r.text}")
    return r


def wait_for_lro(location: str, timeout_seconds=1200):
    location = _absolute_fabric_url(location)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        r = _request_with_retry(
            "GET", location, bearer_headers(required_env("FABRIC_TOKEN"))
        )
        if r.status_code == 202:
            time.sleep(int(r.headers.get("Retry-After", "5")))
            continue
        if r.status_code != 200:
            raise ApiError(f"LRO GET {location} -> {r.status_code}: {r.text}")
        body = r.json() if r.content else {}
        status = str(body.get("status", "")).lower()
        if status in ("failed", "cancelled"):
            raise ApiError(f"Fabric operation failed: {body}")
        if status in ("succeeded", "completed"):
            result_url = body.get("resultUrl")
            if result_url:
                rr = _request_with_retry(
                    "GET", _absolute_fabric_url(result_url),
                    bearer_headers(required_env("FABRIC_TOKEN"))
                )
                if rr.status_code >= 300:
                    raise ApiError(f"LRO result -> {rr.status_code}: {rr.text}")
                return rr.json() if rr.content else body
            return body
        if "status" not in body:
            return body
        time.sleep(int(r.headers.get("Retry-After", "5")))
    raise TimeoutError(f"Fabric operation timed out: {location}")


def list_workspace_items(workspace_id: str, item_type: str | None = None):
    path = f"/workspaces/{workspace_id}/items"
    if item_type:
        path += f"?type={quote(item_type)}"
    items = []
    while path:
        body = fabric_request("GET", path, expected=(200,))
        items.extend(body.get("value", []))
        path = body.get("continuationUri")
    return items


def find_item(workspace_id: str, display_name: str, item_type: str):
    matches = [
        x for x in list_workspace_items(workspace_id, item_type)
        if x.get("displayName") == display_name
    ]
    if len(matches) > 1:
        raise RuntimeError(f"Multiple {item_type} items named {display_name!r}")
    return matches[0] if matches else None


def definition_parts(directory: Path, ignored=None):
    ignored = set(ignored or ()) | {
        "README.md", ".DS_Store", "BOOTSTRAP_REQUIRED.txt"
    }
    parts = []
    for p in sorted(directory.rglob("*")):
        if not p.is_file() or p.name in ignored:
            continue
        if "__pycache__" in p.parts or p.suffix == ".pyc":
            continue
        parts.append({
            "path": p.relative_to(directory).as_posix(),
            "payload": base64.b64encode(p.read_bytes()).decode("ascii"),
            "payloadType": "InlineBase64",
        })
    return parts


def item_definition(directory: Path, format_name: str | None = None):
    parts = definition_parts(directory)
    if not parts:
        raise RuntimeError(f"No definition files under {directory}")
    definition = {"parts": parts}
    if format_name:
        definition["format"] = format_name
    return {"definition": definition}
