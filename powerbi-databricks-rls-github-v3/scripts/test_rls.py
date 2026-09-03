from __future__ import annotations
import argparse
import io
import json
import sys

import pyarrow as pa

from common import find_item, load_environment, powerbi_binary_request


def parse_arrow_response(content: bytes):
    stream = io.BytesIO(content)
    tables = []
    while stream.tell() < len(content):
        try:
            reader = pa.ipc.open_stream(stream)
        except pa.ArrowInvalid:
            break
        metadata = {
            k.decode(): v.decode()
            for k, v in (reader.schema.metadata or {}).items()
        }
        table = reader.read_all()
        if metadata.get("IsError") == "true":
            raise RuntimeError(
                f"DAX query error [{metadata.get('FaultCode')}]: "
                f"{metadata.get('FaultString')}"
            )
        tables.append(table)
    return tables


def run(environment: str):
    cfg = load_environment(environment)
    tests = cfg.get("security_tests", {})
    if not tests.get("enabled", False):
        print("RLS tests disabled")
        return

    ws = cfg["workspace_id"]
    sm = cfg["semantic_model"]
    item = find_item(ws, sm["display_name"], "SemanticModel")
    if not item:
        raise RuntimeError("Semantic model not found")

    failed = 0
    for case in tests.get("cases", []):
        payload = {
            "query": case["query"],
            "effectiveUsername": case["effective_username"],
            "roles": [tests["role"]],
            "queryTimeout": 300,
            "resultSetRowCountLimit": 10000,
        }
        response = powerbi_binary_request(
            "POST",
            f"/datasets/{item['id']}/executeDaxQueries",
            json_body=payload,
            expected=(200,),
        )
        tables = parse_arrow_response(response.content)
        if not tables:
            actual = []
        else:
            df = tables[0].to_pandas()
            col = case["column"]
            if col not in df.columns:
                # Some Arrow query projections may return a bracketed/qualified name.
                matches = [c for c in df.columns if str(c).strip("[]").endswith(col)]
                if len(matches) != 1:
                    raise RuntimeError(
                        f"Column {col!r} not found in test result columns {list(df.columns)}"
                    )
                col = matches[0]
            actual = sorted(str(v) for v in df[col].dropna().tolist())

        expected = sorted(str(v) for v in case["expected_values"])
        ok = actual == expected
        print(
            f"{'PASS' if ok else 'FAIL'} {case['name']}: "
            f"expected={expected} actual={actual}"
        )
        if not ok:
            failed += 1

    if failed:
        raise SystemExit(f"{failed} RLS security test(s) failed")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", required=True, choices=("dev","test","prod"))
    a = p.parse_args()
    run(a.environment)
