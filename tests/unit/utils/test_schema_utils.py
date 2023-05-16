"""unittest module to test schema utils"""
import os
from pathlib import Path

import pytest

from rpdk.guard_rail.utils.arg_handler import collect_schemas
from rpdk.guard_rail.utils.schema_utils import resolve_schema


@pytest.mark.parametrize(
    "schema,result",
    [
        (
            "data/schemas-for-testing/schema-with-chained-refs.json",
            "data/schemas-for-verifying/schema-with-chained-refs.json",
        )
    ],
)
def test_resolve_schema(schema, result):
    """Unit test to verify resolve_schema method"""
    try:
        collected_schemas_to_resolve = collect_schemas(
            schemas=[
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(schema)
                )
            ]
        )
        collected_schemas_to_verify = collect_schemas(
            schemas=[
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(result)
                )
            ]
        )
        assert (
            resolve_schema(collected_schemas_to_resolve[0])
            == collected_schemas_to_verify[0]
        )
    except IOError as e:
        assert "No such file or directory: " in str(e)
