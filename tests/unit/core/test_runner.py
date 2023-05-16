"""
Unit test for runner.py
"""
from unittest import mock

import pytest

from src.rpdk.guard_rail.core.data_types import Statefull, Stateless
from src.rpdk.guard_rail.core.runner import exec_compliance, prepare_ruleset


def test_prepare_ruleset():
    """Test rule set prepare"""
    assert prepare_ruleset()
    assert prepare_ruleset("statefull")


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


@mock.patch("src.rpdk.guard_rail.core.runner.schema_diff")
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
def test_exec_compliance_statefull(
    mock_schema_diff, previous_schema, current_schema, collected_rules, schema_diff
):
    """Test exec_compliance for statefull"""
    mock_schema_diff.return_value = schema_diff
    payload: Statefull = Statefull(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)
    assert "ensure_primary_identifier_not_changed" in compliance_result[0].non_compliant
