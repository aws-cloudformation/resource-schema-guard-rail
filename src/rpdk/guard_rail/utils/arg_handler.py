"""Module to setup cli arg-parser.

This sets up arguments that are allowed for the user to provide.
It also implements some checks over the provided arguments (validation).
Collects schemas and rules if associated argemtns are provided.

Typical usage example:

    from .rpdk.guard_rail.utils.arg_handler import argument_validation

    parser = setup_args()
    argument_validation(args)
    collected_schemas = collect_schemas(schemas=args.schemas)
    collected_rules = collect_rules(rules=args.rules)
"""
import argparse
import re
from functools import wraps
from typing import Sequence

from .common import (
    FILE_PATTERN,
    GUARD_FILE_PATTERN,
    GUARD_PATH_EXTRACT_PATTERN,
    JSON_PATH_EXTRACT_PATTERN,
    SCHEMA_FILE_PATTERN,
    read_file,
    read_json,
)
from .logger import LOG, logdebug


def apply_rule(execute_rule, msg, /):
    """Factory function to provide generic validation annotation"""

    def validation_wrapper(func: object):
        @wraps(func)
        def wrapper(args):
            assert execute_rule(args), msg
            return func(args)

        return wrapper

    return validation_wrapper


@apply_rule(
    lambda args: len(args.schemas) == 2 if args.stateful else True,
    "If Stateful mode is executed, then two schemas MUST be provided (current/previous)",
)
def argument_validation(
    args: argparse.Namespace,
):  # pylint: disable=unused-argument,C0116
    pass


@logdebug
def setup_args():  # pylint: disable=C0116
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--version", action="version", version="v0.1alpha")

    parser.add_argument(
        "--schema",
        dest="schemas",
        action="extend",
        nargs="+",
        type=str,
        required=True,
        help="Should specify schema for CFN compliance evaluation (path or plain value)",
    )

    parser.add_argument(
        "--stateful",
        dest="stateful",
        action="store_true",
        default=False,
        help="If specified will execute stateful compliance evaluation",
    )

    parser.add_argument(
        "--format",
        dest="format",
        action="store_true",
        default=False,
        help="Should specify schema for CFN compliance evaluation (path or plain value)",
    )

    parser.add_argument(
        "--rules",
        dest="rules",
        action="extend",
        nargs="+",
        type=str,
        help="Should specify additional rules for compliance evaluation (path of `.guard` file)",
    )

    return parser


@logdebug
@apply_rule(
    lambda input_path: re.search(FILE_PATTERN, input_path),
    "file path must be specified with `file://...`",
)
@apply_rule(
    lambda input_path: re.search(SCHEMA_FILE_PATTERN, input_path),
    "not a valid json file `...(.json)`",
)
def schema_input_path_validation(input_path: str):  # pylint: disable=C0116
    pass


@logdebug
@apply_rule(
    lambda input_path: re.search(FILE_PATTERN, input_path),
    "file path must be specified with `file://...`",
)
def rule_input_path_validation(input_path: str):  # pylint: disable=C0116
    pass


@logdebug
def collect_schemas(schemas: Sequence[str] = None):
    """Collecting schemas.

    Reading schemas from local or serializes into json if provided in escaped form.

    Args:
        schemas (Sequence[str], optional): list of schemas

    Returns:
        List: list of deserialized schemas
    """

    if not schemas:
        return []

    _schemas = []

    for schema_item in schemas:
        LOG.info(schema_item)
        schema_input_path_validation(schema_item)
        path = "/" + re.search(JSON_PATH_EXTRACT_PATTERN, schema_item).group(2)
        _schemas.append(read_json(path))
    return _schemas


@logdebug
def collect_rules(rules: Sequence[str] = None):
    """Collecting rules.

    Args:
        rules (Sequence[str], optional): list of rules

    Returns:
        List: list of deserialized rules
    """
    _rules = []
    if rules:
        for rule in rules:
            rule_input_path_validation(rule)

            if re.search(GUARD_FILE_PATTERN, rule):
                path = "/" + re.search(GUARD_PATH_EXTRACT_PATTERN, rule).group(2)
                file_obj = read_file(path)
                _rules.append(file_obj)

            else:
                raise ValueError("file extenstion is invalid - MUST be `.guard`")
    return _rules
