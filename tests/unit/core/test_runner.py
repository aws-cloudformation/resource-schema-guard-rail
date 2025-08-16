"""
Unit test for runner.py
"""
from unittest import mock

import pytest

from rpdk.guard_rail.core.data_types import Stateful, Stateless
from rpdk.guard_rail.core.runner import (
    exec_compliance,
    filter_results_for_read_only,
    prepare_ruleset,
)


def test_prepare_ruleset():
    """Test rule set prepare"""
    assert prepare_ruleset()
    assert prepare_ruleset("stateful")


def test_filter_results_for_read_only():
    """Test filtering results for read-only checks"""
    from rpdk.guard_rail.core.data_types import GuardRuleResult, GuardRuleSetResult

    # Create test result with mixed check IDs
    test_result = GuardRuleSetResult(
        compliant=["some_rule"],
        non_compliant={
            "rule1": [GuardRuleResult(check_id="PID001", message="test", path="test")],
            "rule2": [
                GuardRuleResult(check_id="OTHER001", message="test", path="test")
            ],
        },
        warning={
            "rule3": [GuardRuleResult(check_id="PR005", message="test", path="test")]
        },
        skipped=["skipped_rule"],
    )

    filtered = filter_results_for_read_only(test_result)

    # Should include read-only check IDs
    assert "rule1" in filtered.non_compliant  # PID001
    assert "rule3" in filtered.warning  # PR005

    # Should exclude non-read-only check IDs
    assert "rule2" not in filtered.non_compliant  # OTHER001

    # Should keep compliant and skipped as-is
    assert filtered.compliant == ["some_rule"]
    assert filtered.skipped == ["skipped_rule"]


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
