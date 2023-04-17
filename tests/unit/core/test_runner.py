"""
Unit test for data_types.py
"""
import pytest

from src.rpdk.guard_rail.core.data_types import Statefull, Stateless
from src.rpdk.guard_rail.core.runner import exec_compliance, prepare_ruleset


def test_prepare_ruleset():
    """Test rule set prepare"""
    assert prepare_ruleset()


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
    print(compliance_result)
    assert "check_if_taggable_is_used" in compliance_result[0].compliant


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules",
    [
        ({"foo": "bar"}, {"foo": "changed_bar"}, []),
    ],
)
def test_exec_compliance_statefull(previous_schema, current_schema, collected_rules):
    """Test exec_compliance for statefull"""
    try:
        payload: Statefull = Statefull(
            previous_schema=previous_schema,
            current_schema=current_schema,
            rules=collected_rules,
        )
        exec_compliance(payload)
    except NotImplementedError as e:
        assert "Statefull evaluation is not supported yet" == str(e)
