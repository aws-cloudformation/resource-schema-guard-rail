import pytest

from src.rpdk.guard_rail.core.stateful import schema_diff


@pytest.mark.parametrize(
    "previous_schema, current_schema, expected_diff",
    [
        (
            {"primaryIdentifier": ["bar"]},
            {"primaryIdentifier": ["bar_changed", "bar_added"]},
            {
                "primaryIdentifier": {
                    "added": ["bar_changed", "bar_added"],
                    "removed": ["bar"],
                }
            },
        ),
        (
            {
                "properties": {
                    "Description": {
                        "description": "A description of the AWS KMS key.",
                        "type": "string",
                        "minLength": 0,
                        "maxLength": 8192,
                    }
                },
            },
            {
                "properties": {
                    "Description": {
                        "description": "A description of the AWS KMS key.",
                        "minLength": 10,
                        "maxLength": 4096,
                    }
                },
            },
            {
                "properties": {"removed": ["properties/Description/type"]},
                "type": {"removed": ["properties/Description"]},
                "minLength": {
                    "changed": [
                        {
                            "property": "properties/Description",
                            "old_value": 0,
                            "new_value": 10,
                        }
                    ]
                },
                "maxLength": {
                    "changed": [
                        {
                            "property": "properties/Description",
                            "old_value": 8192,
                            "new_value": 4096,
                        }
                    ]
                },
            },
        ),
    ],
)
def test_schema_diff(previous_schema, current_schema, expected_diff):
    assert expected_diff == schema_diff(previous_schema, current_schema)
