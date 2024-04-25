"""
Unit test for cli.py
"""
from typing import Dict, List
from unittest import mock

import pytest

from cli import main
from rpdk.guard_rail.core.data_types import GuardRuleResult, GuardRuleSetResult

RULE_RESULT: GuardRuleResult = GuardRuleResult(check_id="id", message="rule message")
NON_COMPLIANT: Dict[str, List[GuardRuleResult]] = {"non-compliant rule": [RULE_RESULT]}

WARNING: Dict[str, List[GuardRuleResult]] = {"warning rule": [RULE_RESULT]}
COMPLIANCE_RESULT = GuardRuleSetResult(
    compliant=["compliant rule"],
    non_compliant=NON_COMPLIANT,
    warning=WARNING,
    skipped=["skipped rule"],
)


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
                "--stateful",
            ]
        ),
    ],
)
def test_main_cli(
    mock_collect_schemas,
    mock_collect_rules,
    mock_argument_validation,
    mock_exec_compliance,
    args,
):
    """Main cli unit test with downstream mocked"""
    mock_collect_schemas.return_value = [{"foo": "bar"}, {"foo": "bar"}]
    mock_exec_compliance.return_value = [COMPLIANCE_RESULT]
    mock_argument_validation.return_value = True
    mock_collect_rules.return_value = []
    main(args_in=args)
    assert True
