"""
Unit test for runner.py
"""
from unittest import mock

import pytest

from rpdk.guard_rail.core.data_types import Stateful, Stateless
from rpdk.guard_rail.core.runner import (
    exec_compliance,
    filter_rules_for_read_only,
    prepare_ruleset,
)


def test_prepare_ruleset():
    """Test rule set prepare"""
    assert prepare_ruleset()
    assert prepare_ruleset("stateful")


def test_prepare_ruleset_read_only():
    """Test rule set prepare with read-only flag"""
    normal_rules = prepare_ruleset()
    read_only_rules = prepare_ruleset(is_read_only=True)

    # Read-only should have fewer rules
    assert len(read_only_rules) <= len(normal_rules)


def test_filter_rules_for_read_only():
    """Test filtering rules for read-only checks"""
    test_rules = """
rule ensure_primary_identifier_exists_and_not_empty
{
    primaryIdentifier exists
    <<
    {
        "result": "NON_COMPLIANT",
        "check_id": "PID001",
        "message": "primaryIdentifier MUST exist"
    }
    >>
}

rule some_other_rule
{
    someProperty exists
    <<
    {
        "result": "NON_COMPLIANT",
        "check_id": "OTHER001",
        "message": "Some other check"
    }
    >>
}
"""

    filtered = filter_rules_for_read_only(test_rules)

    # Should include read-only rule
    assert "ensure_primary_identifier_exists_and_not_empty" in filtered
    assert "PID001" in filtered

    # Should exclude non-read-only rule
    assert "some_other_rule" not in filtered
    assert "OTHER001" not in filtered


@pytest.mark.parametrize(
    "collected_schemas,collected_rules",
    [
        ([{"foo": "bar"}], []),
    ],
)
def test_exec_compliance_stateless(collected_schemas, collected_rules):
    """Test exec_compliance for stateless"""
    payload: Stateless = Stateless(schemas=collected_schemas, rules=collected_rules)
    compliance_result = exec_compliance(payload)
    assert "check_if_taggable_is_used" in compliance_result[0].compliant


@pytest.mark.parametrize(
    "collected_schemas,collected_rules,is_read_only",
    [
        ([{"foo": "bar"}], [], True),
    ],
)
def test_exec_compliance_stateless_read_only(
    collected_schemas, collected_rules, is_read_only
):
    """Test exec_compliance for stateless with read-only flag"""
    payload: Stateless = Stateless(
        schemas=collected_schemas, rules=collected_rules, is_read_only=is_read_only
    )
    compliance_result = exec_compliance(payload)
    # Should still return results but with filtered rules
    assert compliance_result[0] is not None


@mock.patch("rpdk.guard_rail.core.runner.schema_diff")
@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules, schema_diff",
    [
        (
            {},
            {},
            [],
            {
                "primaryIdentifier": {
                    "added": ["bar_changed", "bar_added"],
                    "removed": ["bar"],
                }
            },
        ),
    ],
)
def test_exec_compliance_stateful(
    mock_schema_diff, previous_schema, current_schema, collected_rules, schema_diff
):
    """Test exec_compliance for stateful"""
    mock_schema_diff.return_value = schema_diff
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)
    assert "ensure_primary_identifier_not_changed" in compliance_result[0].non_compliant


@mock.patch("rpdk.guard_rail.core.runner.schema_diff")
@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules, schema_diff, is_read_only",
    [
        (
            {},
            {},
            [],
            {
                "primaryIdentifier": {
                    "added": ["bar_changed", "bar_added"],
                    "removed": ["bar"],
                }
            },
            True,
        ),
    ],
)
def test_exec_compliance_stateful_read_only(
    mock_schema_diff,
    previous_schema,
    current_schema,
    collected_rules,
    schema_diff,
    is_read_only,
):
    """Test exec_compliance for stateful with read-only flag"""
    mock_schema_diff.return_value = schema_diff
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
        is_read_only=is_read_only,
    )
    compliance_result = exec_compliance(payload)
    # Should still detect primary identifier changes in read-only mode
    assert "ensure_primary_identifier_not_changed" in compliance_result[0].non_compliant
