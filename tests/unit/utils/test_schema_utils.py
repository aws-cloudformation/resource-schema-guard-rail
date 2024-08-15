"""unittest module to test schema utils"""
import os
from pathlib import Path

import pytest

from rpdk.guard_rail.utils.arg_handler import collect_schemas
from rpdk.guard_rail.utils.schema_utils import add_paths_to_schema, resolve_schema


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


@pytest.mark.parametrize(
    "schema,result",
    [
        (
            "data/schemas-for-testing/schema-with-chained-refs.json",
            {
                "/properties/NewProperty",
                "/properties/NewProperty/Name",
                "/properties/Configurations",
                "/properties/Configurations/*/Configurations",
                "/properties/Configurations/*/Name",
                "/properties/Tags2",
                "/properties/Tags2/*/Key",
                "/properties/Tags2/*/Value2",
                "/properties/Tags2/*/Value",
                "/properties/Tags3",
                "/properties/Tags3/*/Key",
                "/properties/Tags3/*/Value2",
                "/properties/Tags3/*/Value",
                "/properties/Tags4",
                "/properties/Tags4/*/Key",
                "/properties/Tags4/*/Value",
                "/properties/Tags4/*/Value2",
                "/properties/Tags5",
                "/properties/Tags5/*/Key",
                "/properties/Tags5/*/Value2",
                "/properties/Tags5/*/Value",
                "/properties/Description",
                "/properties/PendingWindowInDays",
                "/properties/KeyUsage",
                "/properties/KeySpec",
                "/properties/EnableKeyRotation",
                "/properties/MultiRegion",
                "/properties/Enabled",
                "/properties/KeyPolicy",
                "/properties/Arn",
                "/properties/KeyId",
            },
        ),
        (
            "data/schemas-for-testing/schema-with-nested-combiners.json",
            {
                "/properties/Name",
                "/properties/Id",
                "/properties/Tuples",
                "/properties/Tuples/*/TextTransformation",
                "/properties/Tuples/*/Field",
                "/properties/Tuples/*/Field/Data",
                "/properties/Tuples/*/Field/Type",
                "/properties/Tuples/*/Field/*/Type",
                "/properties/Tuples/*/Field/*/NewType",
            },
        ),
        (
            "data/schemas-for-testing/schema-launch-template.json",
            {
                "/properties/LaunchTemplate",
                "/properties/LaunchTemplate/LaunchTemplateName",
                "/properties/LaunchTemplate/LaunchTemplateId",
                "/properties/LaunchTemplate/Version",
                "/properties/Description",
                "/properties/Description/Tags",
                "/properties/Description/Tags/*/Key",
                "/properties/Description/Tags/*/Value",
            },
        ),
    ],
)
def test_add_paths_to_schema(schema, result):
    """Unit test to verify that all properties are traversed"""
    collected_schemas_to_resolve = collect_schemas(
        schemas=[
            "file:/"
            + str(Path(os.path.dirname(os.path.realpath(__file__))).joinpath(schema))
        ]
    )
    schema_with_paths = add_paths_to_schema(collected_schemas_to_resolve[0])
    assert set(schema_with_paths["paths"]) == result


@pytest.mark.parametrize(
    "schema,result",
    [
        (
            "data/schemas-for-testing/schema-launch-template.json",
            {
                "/properties/LaunchTemplate",
                "/properties/LaunchTemplate/LaunchTemplateName",
                "/properties/LaunchTemplate/LaunchTemplateId",
                "/properties/LaunchTemplate/Version",
                "/properties/Description",
                "/properties/Description/Tags",
                "/properties/Description/Tags/*/Key",
                "/properties/Description/Tags/*/Value",
            },
        )
    ],
)
def test_add_tag_path(schema, result):
    """Unit test to verify that schema has tag property identified"""
    collected_schemas_to_resolve = collect_schemas(
        schemas=[
            "file:/"
            + str(Path(os.path.dirname(os.path.realpath(__file__))).joinpath(schema))
        ]
    )
    schema_with_paths = add_paths_to_schema(collected_schemas_to_resolve[0])
    assert "TaggingPath" in schema_with_paths
    assert schema_with_paths["TaggingPath"] == "/properties/Description/Tags"
