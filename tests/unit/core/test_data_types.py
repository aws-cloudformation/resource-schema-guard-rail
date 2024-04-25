"""
Unit test for data_types.py
"""

from rpdk.guard_rail.core.data_types import GuardRuleResult, GuardRuleSetResult


def test_merge():
    """Test GuardRuleSetResult merge"""
    try:
        GuardRuleSetResult().merge("rule_result")
    except TypeError as e:
        assert "cannot merge with non GuardRuleSetResult type" == str(e)


def test_err_result_str():
    """Test GuardRuleSetResult str fail scenario"""
    try:
        GuardRuleSetResult().display()
    except ValueError as e:
        assert "No Rules have been executed" == str(e)


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
        == "GuardRuleSetResult(compliant=[], non_compliant={'ensure_old_property_not_turned_immutable': {GuardRuleResult(check_id='MI007', message='cannot remove minimum from properties', path='/minimum/removed')}}, warning={}, skipped=[])"  # pylint: disable=C0301
    )
