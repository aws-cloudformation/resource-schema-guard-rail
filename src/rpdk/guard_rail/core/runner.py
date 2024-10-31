"""Module to perform policy execution context.

Main function is __exec_rules__, which is a factory function. It uses closure
to run multiple schemas over multiple sets of rules. There is an abstraction function
on top of lower level (__exec_rules__) - exec_compliance. This function invokes factory function
in stateless and stateful mode

Typical usage example:

    from guard_rail.core.runner import exec_compliance
    payload: Stateless|Stateful = ...
    exec_compliance(payload)
"""
import importlib.resources as pkg_resources
from ast import literal_eval
from functools import singledispatch
from typing import Any, Dict, Mapping

import cfn_guard_rs

from rpdk.guard_rail.core.data_types import (
    GuardRuleResult,
    GuardRuleSetResult,
    Stateful,
    Stateless,
)
from rpdk.guard_rail.core.stateful import schema_diff
from rpdk.guard_rail.rule_library import combiners, core, permissions, stateful, tags
from rpdk.guard_rail.utils.common import is_guard_rule
from rpdk.guard_rail.utils.logger import LOG, logdebug
from rpdk.guard_rail.utils.schema_utils import add_paths_to_schema

NON_COMPLIANT = "NON_COMPLIANT"
WARNING = "WARNING"


@logdebug
def prepare_ruleset(mode: str = "stateless"):
    """Fetches module level schema rules based on mode.

    Iterates over provided modules (core, combiners, permissions, tags) or (stateful)
    and checks if content is a guard rule-set, ten adds it to the list
    `to-run`

    Returns:
        Set[str]: set of rules in a string form
    """
    rule_modules = {
        "stateless": [core, combiners, permissions, tags],
        "stateful": [stateful],
    }
    rule_set = set()
    for module in rule_modules[mode]:
        for content in pkg_resources.contents(module):
            if not is_guard_rule(content):
                continue
            rule_set.add(pkg_resources.read_text(module, content))
    return rule_set


@logdebug
def __exec_rules__(schema: Dict):
    """Closure factory function for schema compliace execution -
    Read rule compliance status and output guard rule set result
    Creates closure, modifies, and retains the previous state between calls (rule set evaluations)
    Args:
        schema ([Dict]): Resource Provider Schema
    Returns:
        [function]: Closure
    """
    exec_result = GuardRuleSetResult()

    @logdebug
    def __exec__(rules: str):
        guard_result = cfn_guard_rs.run_checks(schema, rules)
        tag_path = schema.get("TaggingPath")

        def __render_output(evaluation_result: object):
            def __add_item__(rule_name: str, mapping: Mapping, result: Any):
                if rule_name in mapping:
                    mapping[rule_name].add(result)
                    return
                mapping[rule_name] = {result}

            non_compliant = {}
            warning = {}
            for rule_name, checks in guard_result.not_compliant.items():
                for check in checks:
                    try:
                        if check.message:
                            _message_dict = literal_eval(check.message.strip())
                            _check_id = _message_dict["check_id"]
                            _path = check.path
                            if _check_id == "TAG016" and tag_path:
                                _path = tag_path

                            rule_result = GuardRuleResult(
                                check_id=_check_id,
                                message=_message_dict["message"],
                                path=_path,
                            )

                            if _message_dict.get("result", NON_COMPLIANT) == WARNING:
                                __add_item__(rule_name, warning, rule_result)
                            else:
                                __add_item__(rule_name, non_compliant, rule_result)
                    except SyntaxError as ex:
                        LOG.info("%s %s", str(ex), check.message)
                        __add_item__(rule_name, non_compliant, GuardRuleResult())

            return GuardRuleSetResult(
                compliant=evaluation_result.compliant,
                warning=warning,
                non_compliant=non_compliant,
                skipped=evaluation_result.not_applicable,
            )

        exec_result.merge(__render_output(guard_result))
        return exec_result

    return __exec__


@singledispatch
def exec_compliance(*args, **kwards):
    """Placeholder for exec_compliance
    This function holds no implementation,
    There are two types of compliance checks:
    * Stateless - works with current schema state
    * Stateful - works with current and previous schema states
    Raises:
        NotImplementedError: not supported implementation
    """
    raise NotImplementedError("not supported implementation")


# https://stackoverflow.com/questions/62700774/singledispatchmethod-with-typing-types
# Have to switch to class type instead of typing due to functools known bug
@exec_compliance.register(Stateless)
def _(payload):
    """Implements exec_compliance for stateless compliance assessment
    over specified list of schemas/rules

    Args:
        payload (Stateless): Stateless payload
    Returns:
        [GuardRuleSetResult]: Collection of Rule Results
    """

    compliance_output = []
    ruleset = prepare_ruleset() | set(payload.rules)

    def __execute_rules__(schema_exec, ruleset):
        output = None
        for rules in ruleset:
            output = schema_exec(rules)
        return output

    for schema in payload.schemas:
        schema_with_paths = add_paths_to_schema(schema=schema)
        schema_to_execute = __exec_rules__(schema=schema_with_paths)
        output = __execute_rules__(schema_exec=schema_to_execute, ruleset=ruleset)
        compliance_output.append(output)
    return compliance_output


@exec_compliance.register(Stateful)
def _(payload):
    """Implements exec_compliance for stateful compliance assessment
    over specified list of rules

    Args:
        payload (Stateful): Stateful payload
    Returns:
        GuardRuleSetResult: Rule Result
    """
    compliance_output = []
    ruleset = prepare_ruleset("stateful") | set(payload.rules)

    def __execute__(schema_exec, ruleset):
        output = None
        for rules in ruleset:
            output = schema_exec(rules)
        return output

    schema_difference = schema_diff(
        previous_json=payload.previous_schema, current_json=payload.current_schema
    )

    schema_to_execute = __exec_rules__(schema=schema_difference)
    output = __execute__(schema_exec=schema_to_execute, ruleset=ruleset)
    output.schema_difference = schema_difference
    compliance_output.append(output)

    return compliance_output
