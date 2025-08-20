"""
Unit tests for data_types.py readonly functionality
"""

from rpdk.guard_rail.core.data_types import Stateless


def test_stateless_with_read_only_flag():
    """Test Stateless data type with is_read_only flag"""
    payload = Stateless(schemas=[{"foo": "bar"}], rules=[], is_read_only=True)
    assert payload.is_read_only is True
    assert payload.schemas == [{"foo": "bar"}]
    assert payload.rules == []


def test_stateless_default_read_only_flag():
    """Test Stateless data type with default is_read_only flag"""
    payload = Stateless(schemas=[{"foo": "bar"}], rules=[])
    assert payload.is_read_only is False
