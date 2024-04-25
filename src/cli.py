"""CLI entry to the package.

Execution of the rules can come via cli command. This module allows
one to execute resource json schema compliance assessment via cli
command with a prespecified set of arguments.

Typical usage example:

    $ guard-rail --schema file://path1 --schema file://path2 --rule file://path1 --rule file://path2

Arguments:
    guard-rail - is the name of the package
    schema - is the argument to provide resource schema
    rule - is the argument to provide custom set of rules
"""

from functools import singledispatch
from typing import List

from rpdk.guard_rail.core.data_types import GuardRuleSetResult, Stateful, Stateless
from rpdk.guard_rail.core.runner import exec_compliance
from rpdk.guard_rail.utils.arg_handler import (
    argument_validation,
    collect_rules,
    collect_schemas,
    setup_args,
)


def main(args_in=None):
    """Main cli entry point.

    Retrieves provided argument set. Based on provided arguments
    runs different executions of the compliance tests.

    Args:
        args_in: set of arguments supported by the cli module

    Returns:
        None

    Raises:
        NotImplementedError: An error occurred accessing invoke method
        that has not been implemented yet
    """
    parser = setup_args()
    args = parser.parse_args(args=args_in)

    argument_validation(args)
    collected_schemas = collect_schemas(schemas=args.schemas)
    collected_rules = collect_rules(rules=args.rules)

    compliance_result = None

    if not args.stateful:
        payload: Stateless = Stateless(schemas=collected_schemas, rules=collected_rules)
        compliance_result = invoke(payload)
    else:
        # should be index safe as argument validation should fail prematurely
        payload: Stateful = Stateful(
            previous_schema=collected_schemas[0],
            current_schema=collected_schemas[1],
            rules=collected_rules,
        )
        compliance_result = invoke(payload)

    if args.format:
        display(compliance_result)
    else:
        print(compliance_result)


def display(compliance_result: List[GuardRuleSetResult]):  # pylint: disable=C0116
    for item in compliance_result:
        print()
        item.display()
    print()


@singledispatch
def invoke(*args, **kwargs):  # pylint: disable=C0116
    raise NotImplementedError("not supported implementation")


@invoke.register(Stateless)
def _(payload):
    return exec_compliance(payload)


@invoke.register(Stateful)
def _(payload):
    return exec_compliance(payload)
