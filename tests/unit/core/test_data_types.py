"""
Unit test for data_types.py
"""
from typing import Dict, List

from rpdk.guard_rail.core.data_types import GuardRuleResult, GuardRuleSetResult


def test_merge():
    """Test GuardRuleSetResult merge"""
    try:
        GuardRuleSetResult().merge("rule_result")
    except TypeError as e:
        assert "cannot merge with non GuardRuleSetResult type" == str(e)


def test_result_str():
    """Test GuardRuleSetResult str"""
    rule_result: GuardRuleResult = GuardRuleResult(
        check_id="id", message="rule message"
    )
    non_compliant: Dict[str, List[GuardRuleResult]] = {
        "non-compliant rule": [rule_result]
    }
    assert str(
        GuardRuleSetResult(non_compliant=non_compliant)
        == "[SKIPPED]:\n\nSKIPPED RULE\n\n\x1b[32m[PASSED]:\x1b[39m\n\nCOMPLIANT "
        "RULE\n\n\x1b[33m[WARNING]:\x1b[39m\n\nWARNING RULE:\n    check-id: id\n    "
        "message: rule message\n\n\n\x1b[31m[FAILED]:\x1b[39m\n\nNON-COMPLIANT RULE:\n   "
        " check-id: id\n    message: rule message"
    )


def test_err_result_str():
    """Test GuardRuleSetResult str fail scenario"""
    assert "Couldn't retrieve the result" == str(GuardRuleSetResult())


def test_success_result_str():
    """Test GuardRuleSetResult str success scenario"""
    assert (
        str(
            GuardRuleSetResult(
                non_compliant={
                    "ensure_old_property_not_turned_immutable": {
                        GuardRuleResult(
                            check_id="MI007",
                            message="cannot remove minimum from properties",
                            path="/minimum/removed",
                        )
                    }
                }
            )
        )
        == "---------\n[SKIPPED]:\n\n\n\x1b[32m[PASSED]:\x1b[39m\n\n\n\x1b[33m[WARNING]:\x1b[39m\n\n\n\x1b[31m[FAILED]:\x1b[39m\n\nENSURE_OLD_PROPERTY_NOT_TURNED_IMMUTABLE:\n    check-id: MI007\n    message: cannot remove minimum from properties\n    path: /minimum/removed\n    \n"  # pylint: disable=C0301
    )
