"""
Unit test for cli.py
"""
from typing import Dict, List
from unittest import mock

import pytest

from cli import main
from rpdk.guard_rail.core.data_types import GuardRuleResult, GuardRuleSetResult


@pytest.fixture(scope="module")
def compliance_result():
    """Fixture function to create GuardRuleSetResult"""
    rule_result: GuardRuleResult = GuardRuleResult(
        check_id="id", message="rule message"
    )
    non_compliant: Dict[str, List[GuardRuleResult]] = {
        "non-compliant rule": [rule_result]
    }
    warning: Dict[str, List[GuardRuleResult]] = {"warning rule": [rule_result]}
    result = GuardRuleSetResult(
        compliant=["compliant rule"],
        non_compliant=non_compliant,
        warning=warning,
        skipped=["skipped rule"],
    )
    yield result


@mock.patch("cli.exec_compliance")
@mock.patch("cli.argument_validation")
@mock.patch("cli.collect_rules")
@mock.patch("cli.collect_schemas")
@pytest.mark.parametrize(
    "args",
    [
        (
            [
                "--schema",
                "file://path1",
                "--schema",
                "file://path2",
                "--rule",
                "file://path1",
                "--rule",
                "file://path2",
                "--format",
            ]
        ),
        (
            [
                "--schema",
                "file://path1",
                "--schema",
                "file://path2",
                "--rule",
                "file://path1",
                "--rule",
                "file://path2",
            ]
        ),
        (
            [
                "--schema",
                "file://path1",
                "--schema",
                "file://path2",
                "--rule",
                "file://path1",
                "--rule",
                "file://path2",
                "--statefull",
            ]
        ),
    ],
)
def test_main_cli(
    mock_exec_compliance,
    mock_argument_validation,
    mock_collect_rules,
    mock_collect_schemas,
    args,
):
    """Main cli unit test with downstream mocked"""
    mock_collect_schemas.return_value = [{"foo": "bar"}, {"foo": "bar"}]
    mock_exec_compliance.return_value = compliance_result
    mock_argument_validation.return_value = True
    mock_collect_rules.return_value = []
    main(args_in=args)
    assert True
