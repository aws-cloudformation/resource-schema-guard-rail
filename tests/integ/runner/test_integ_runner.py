"""
Integ test for runner.py
"""
import os
from pathlib import Path

import pytest

from src.rpdk.guard_rail.core.data_types import GuardRuleResult, Statefull, Stateless
from src.rpdk.guard_rail.core.runner import exec_compliance
from src.rpdk.guard_rail.utils.arg_handler import collect_schemas


@pytest.mark.parametrize(
    "collected_schemas,collected_rules,non_compliant_rules,warning_rules",
    [
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/sample-schema.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_properties_do_not_support_multitype": [
                    GuardRuleResult(
                        check_id="COM_2",
                        message="type MUST NOT have combined definition",
                    )
                ],
                "ensure_primary_identifier_is_read_or_create_only": [
                    GuardRuleResult(
                        check_id="P_ID_2",
                        message="primaryIdentifier MUST be either readOnly or createOnly",
                    )
                ],
                "ensure_arn_properties_contain_pattern": [
                    GuardRuleResult(
                        check_id="ARN_2",
                        message="arn related property MUST have pattern specified",
                    )
                ],
            },
            {
                "check_if_taggable_is_used": [
                    GuardRuleResult(
                        check_id="TAG_1",
                        message="`taggable` is deprecated, please used `tagging` property",
                    )
                ],
                "ensure_tagging_is_specified": [
                    GuardRuleResult(
                        check_id="TAG_2", message="`tagging` MUST be specified"
                    )
                ],
            },
        ),
    ],
)
def test_exec_compliance_stateless(
    collected_schemas, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateless"""
    payload: Stateless = Stateless(schemas=collected_schemas, rules=collected_rules)
    compliance_result = exec_compliance(payload)[0]

    # Assert for non-compliant rules
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )
    # Assert for warning rules
    for warning_rule, warning_result in warning_rules.items():
        assert warning_rule in compliance_result.warning
        assert warning_result == compliance_result.warning[warning_rule]


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/sample-schema.json"
                        )
                    )
                ]
            ),
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/sample-schema.json"
                        )
                    )
                ]
            ),
            [],
            [],
            [],
        ),
    ],
)
def test_exec_compliance_statefull(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
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
