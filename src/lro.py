"""Shared long-running-operation (LRO) handler (spec section 19).

Fabric APIs may return 202 Accepted with Location / x-ms-operation-id /
Retry-After headers. This module implements the single common poller used
by every caller that might hit an async Fabric response, so polling and
Retry-After handling is not reimplemented per API.
"""

import time

from src.errors import LroFailedError, LroTimeoutError

DEFAULT_LRO_TIMEOUT_SECONDS = 900
DEFAULT_POLL_INTERVAL_SECONDS = 5

TERMINAL_SUCCESS = "Succeeded"
TERMINAL_FAILED = "Failed"
NON_TERMINAL_STATES = ("NotStarted", "Running")


def wait_for_operation(
    operation_id: str,
    get_operation_state,
    get_operation_result,
    retry_after: float = None,
    timeout_seconds: float = DEFAULT_LRO_TIMEOUT_SECONDS,
    sleep=time.sleep,
    clock=time.monotonic,
):
    """Poll a Fabric long-running operation until it reaches a terminal state.

    Args:
        operation_id: The Fabric operation id to poll.
        get_operation_state: callable(operation_id) -> dict with a "status" key
            (one of NotStarted/Running/Succeeded/Failed).
        get_operation_result: callable(operation_id) -> dict, invoked only
            once the operation succeeds and a result is applicable.
        retry_after: seconds to wait before the first poll, per Fabric's
            Retry-After header.
        timeout_seconds: overall timeout (FABRIC_LRO_TIMEOUT_SECONDS).
        sleep / clock: injectable for testing.

    Returns:
        The operation result dict (or the terminal state dict if there is no
        separate result payload for this operation).
    """
    deadline = clock() + timeout_seconds

    wait_seconds = retry_after if retry_after is not None else DEFAULT_POLL_INTERVAL_SECONDS
    sleep(max(wait_seconds, 0))

    while True:
        state = get_operation_state(operation_id)
        status = state.get("status")

        if status == TERMINAL_SUCCESS:
            if get_operation_result is not None:
                return get_operation_result(operation_id)
            return state

        if status == TERMINAL_FAILED:
            error = state.get("error", {})
            raise LroFailedError(
                f"Fabric operation {operation_id} failed: "
                f"{error.get('message', error) or 'Unknown error'}"
            )

        if status not in NON_TERMINAL_STATES:
            raise LroFailedError(
                f"Fabric operation {operation_id} returned unexpected "
                f"status: {status}"
            )

        if clock() >= deadline:
            raise LroTimeoutError(
                f"Fabric operation {operation_id} did not complete within "
                f"{timeout_seconds} seconds"
            )

        sleep(DEFAULT_POLL_INTERVAL_SECONDS)
