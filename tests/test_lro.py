import pytest

from src.errors import LroFailedError, LroTimeoutError
from src.lro import wait_for_operation


def _clock_sequence(values):
    it = iter(values)

    def clock():
        return next(it)

    return clock


def test_running_then_succeeded_returns_result():
    states = iter(
        [
            {"status": "Running"},
            {"status": "Running"},
            {"status": "Succeeded"},
        ]
    )
    sleeps = []

    result = wait_for_operation(
        operation_id="op-1",
        get_operation_state=lambda _id: next(states),
        get_operation_result=lambda _id: {"definition": "final"},
        retry_after=1,
        sleep=sleeps.append,
        clock=_clock_sequence([0, 0, 0, 0]),
    )

    assert result == {"definition": "final"}
    assert sleeps[0] == 1  # respected Retry-After for the first wait


def test_failed_operation_raises():
    with pytest.raises(LroFailedError):
        wait_for_operation(
            operation_id="op-2",
            get_operation_state=lambda _id: {
                "status": "Failed",
                "error": {"message": "boom"},
            },
            get_operation_result=lambda _id: {},
            retry_after=0,
            sleep=lambda _s: None,
            clock=_clock_sequence([0, 0]),
        )


def test_timeout_raises():
    clock_values = iter([0, 100, 200, 1000])

    with pytest.raises(LroTimeoutError):
        wait_for_operation(
            operation_id="op-3",
            get_operation_state=lambda _id: {"status": "Running"},
            get_operation_result=lambda _id: {},
            retry_after=0,
            timeout_seconds=50,
            sleep=lambda _s: None,
            clock=lambda: next(clock_values),
        )


def test_unexpected_status_raises():
    with pytest.raises(LroFailedError):
        wait_for_operation(
            operation_id="op-4",
            get_operation_state=lambda _id: {"status": "Cancelled"},
            get_operation_result=lambda _id: {},
            retry_after=0,
            sleep=lambda _s: None,
            clock=_clock_sequence([0, 0]),
        )
