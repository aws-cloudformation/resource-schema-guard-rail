"""unittest module to test arg handler"""
import argparse
import os
from pathlib import Path

import pytest

from rpdk.guard_rail.utils.arg_handler import (
    argument_validation,
    collect_rules,
    collect_schemas,
    rule_input_path_validation,
    schema_input_path_validation,
    setup_args,
)


def test_arg_parse_setup():
    """test arg setup"""
    assert setup_args()


@pytest.mark.parametrize(
    "schemas,stateful,expect_to_pass",
    [
        (["schema1", "schema2"], True, True),
        (["schema1"], True, False),
        (["schema1"], False, True),
    ],
)
def test_argument_validation(schemas, stateful, expect_to_pass):
    """test argument validation"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schema",
        dest="schemas",
        default=schemas,
    )
    parser.add_argument(
        "--stateful",
        dest="stateful",
        default=stateful,
    )

    if expect_to_pass:
        argument_validation(parser.parse_args([]))
        assert True
    else:
        try:
            argument_validation(parser.parse_args([]))
        except AssertionError as e:
            assert (
                "If Stateful mode is executed, then two schemas MUST be provided (current/previous)"
                == str(e)
            )


@pytest.mark.parametrize(
    "input_path,expect_to_pass",
    [
        ("file://directory1/file.json", True),
        ("/directory1", False),
        ("file://directory1/file.jpeg", False),
    ],
)
def test_input_validation(input_path, expect_to_pass):
    """test input validation"""
    if expect_to_pass:
        schema_input_path_validation(input_path)
        rule_input_path_validation(input_path)
        assert True
    else:
        try:
            schema_input_path_validation(input_path)
        except AssertionError as e:
            print(e)
            assert "file path must be specified with `file://...`" == str(
                e
            ) or "not a valid json file `...(.json)`" == str(e)


@pytest.mark.parametrize(
    "schemas,expected_schemas",
    [
        (['{"foo": "bar"}'], [{"foo": "bar"}]),
        ([], []),
        (None, []),
        (['{"foo": "bar"}', '{"foo": "bar"}'], [{"foo": "bar"}, {"foo": "bar"}]),
    ],
)
def test_collect_schemas_body(schemas, expected_schemas):
    """test collect schemas body"""
    result = collect_schemas(schemas=schemas)
    assert result == expected_schemas


@pytest.mark.parametrize(
    "schemas,expected_schemas",
    [(["data/sample.json"], [{"foo": "bar"}])],
)
def test_collect_schemas_file(schemas, expected_schemas):
    """test collect schemas files"""
    result = collect_schemas(
        schemas=[
            "file:/"
            + str(Path(os.path.dirname(os.path.realpath(__file__))).joinpath(schema))
            for schema in schemas
        ]
    )
    assert result == expected_schemas


@pytest.mark.parametrize(
    "schemas,msg",
    [
        (["data/sample.jsn"], "not a valid json file `...(.json)`"),
        (["data/samplea.json"], "No such file or directory:"),
    ],
)
def test_collect_schemas_file_fail(schemas, msg):
    """test fail scenario of collect schemas body"""
    try:
        collect_schemas(
            schemas=[
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(schema)
                )
                for schema in schemas
            ]
        )
    except Exception as e:
        assert msg == str(e) or msg in str(e)


@pytest.mark.parametrize(
    "rules,expected_rules",
    [
        ([], []),
        (None, []),
        (["data/sample.guard"], [""]),
    ],
)
def test_collect_rules(rules, expected_rules):
    """test collect rules"""
    rules_to_check = (
        [
            "file:/"
            + str(Path(os.path.dirname(os.path.realpath(__file__))).joinpath(rule))
            for rule in rules
        ]
        if rules is not None
        else rules
    )

    assert collect_rules(rules_to_check) == expected_rules


def test_collect_rules_invalid():
    """test collect rules fails scenario"""
    try:
        collect_rules(
            [
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                        "data/sample.guardian"
                    )
                )
            ]
        )
    except ValueError as e:
        assert "file extenstion is invalid - MUST be `.guard`" == str(e)
