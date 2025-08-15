"""
Unit tests for data_types.py read-only functionality
"""

from rpdk.guard_rail.core.data_types import Stateful, Stateless


def test_stateless_with_read_only_flag():
    """Test Stateless data type with is_read_only flag"""
    payload = Stateless(
        schemas=[{"foo": "bar"}],
        rules=[],
        is_read_only=True
    )
    assert payload.is_read_only is True
    assert payload.schemas == [{"foo": "bar"}]
    assert payload.rules == []


def test_stateless_default_read_only_flag():
    """Test Stateless data type with default is_read_only flag"""
    payload = Stateless(
        schemas=[{"foo": "bar"}],
        rules=[]
    )
    assert payload.is_read_only is False


def test_stateful_with_read_only_flag():
    """Test Stateful data type with is_read_only flag"""
    payload = Stateful(
        current_schema={"foo": "bar"},
        previous_schema={"foo": "baz"},
        rules=[],
        is_read_only=True
    )
    assert payload.is_read_only is True
    assert payload.current_schema == {"foo": "bar"}
    assert payload.previous_schema == {"foo": "baz"}


def test_stateful_default_read_only_flag():
    """Test Stateful data type with default is_read_only flag"""
    payload = Stateful(
        current_schema={"foo": "bar"},
        previous_schema={"foo": "baz"},
        rules=[]
    )
    assert payload.is_read_only is False
