"""
Unit test for stateful.py
"""
import pytest

from rpdk.guard_rail.core.stateful import schema_diff


@pytest.mark.parametrize(
    "schema_variant1, schema_variant2, expected_diff, expected_diff_negative",
    [
        # Test Case #1: New Primary Identifier
        (
            {"primaryIdentifier": ["bar"]},
            {"primaryIdentifier": ["bar_changed", "bar_added"]},
            {
                "primaryIdentifier": {
                    "added": ["bar_changed", "bar_added"],
                    "removed": ["bar"],
                }
            },
            {
                "primaryIdentifier": {
                    "added": ["bar"],
                    "removed": ["bar_changed", "bar_added"],
                }
            },
        ),
        # Test Case #2: New Native Constructs and modifications
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
                "type": {"removed": ["/properties/Description"]},
                "minLength": {
                    "changed": [
                        {
                            "property": "/properties/Description",
                            "old_value": 0,
                            "new_value": 10,
                        }
                    ]
                },
                "maxLength": {
                    "changed": [
                        {
                            "property": "/properties/Description",
                            "old_value": 8192,
                            "new_value": 4096,
                        }
                    ]
                },
            },
            {
                "type": {"added": ["/properties/Description"]},
                "minLength": {
                    "changed": [
                        {
                            "property": "/properties/Description",
                            "old_value": 10,
                            "new_value": 0,
                        }
                    ]
                },
                "maxLength": {
                    "changed": [
                        {
                            "property": "/properties/Description",
                            "old_value": 4096,
                            "new_value": 8192,
                        }
                    ]
                },
            },
        ),
        # Test Case #3: New Property
        (
            {"properties": {}},
            {
                "properties": {
                    "NewProperty": {
                        "type": "string",
                        "description": "...",
                        "minLength": 0,
                        "maxLength": 129,
                    }
                }
            },
            {"properties": {"added": ["/properties/NewProperty"]}},
            {"properties": {"removed": ["/properties/NewProperty"]}},
        ),
        # Test Case #4: New Property with nested structure
        (
            {"properties": {}},
            {
                "properties": {
                    "Configurations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Name": {"type": "string"},
                                "Configurations": {  # recursive property
                                    "type": "array",
                                    "items": {},  # ends at this level
                                },
                            },
                        },
                    }
                }
            },
            {
                "properties": {
                    "added": [
                        # we need to add root property
                        # so as it's leafs as separate items
                        "/properties/Configurations",
                        "/properties/Configurations/*/Name",
                        "/properties/Configurations/*/Configurations",
                    ]
                }
            },
            {
                "properties": {
                    "removed": [
                        # we need to add root property
                        # so as it's leafs as separate items
                        "/properties/Configurations",
                        "/properties/Configurations/*/Name",
                        "/properties/Configurations/*/Configurations",
                    ]
                }
            },
        ),
        # Test Case #5: New Nested Property
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"Key": {"type": "string"}},
                        },
                    }
                }
            },
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "string"},
                                "Value": {"type": "string"},
                            },
                        },
                    }
                }
            },
            {
                "properties": {
                    "added": [
                        "/properties/Tags/*/Value",
                    ]
                }
            },
            {
                "properties": {
                    "removed": [
                        "/properties/Tags/*/Value",
                    ]
                }
            },
        ),
        # Test Case #6: Modified Nested Property
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"Key": {"type": "string"}},
                        },
                    }
                }
            },
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "int"},
                            },
                        },
                    }
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "new_value": "int",
                            "old_value": "string",
                            "property": "/properties/Tags/*/Key",
                        }
                    ]
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "new_value": "string",
                            "old_value": "int",
                            "property": "/properties/Tags/*/Key",
                        }
                    ]
                }
            },
        ),
        # Test Case #7: New Two Level Nested Property
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"Key": {"type": "string"}},
                        },
                    }
                }
            },
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "string"},
                                "Value": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "NestedKey": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    }
                }
            },
            {
                "properties": {
                    "added": [
                        "/properties/Tags/*/Value",
                        "/properties/Tags/*/Value/*/NestedKey",
                    ]
                }
            },
            {
                "properties": {
                    "removed": [
                        "/properties/Tags/*/Value",
                        "/properties/Tags/*/Value/*/NestedKey",
                    ]
                }
            },
        ),
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"Key": {"type": "string"}},
                        },
                    }
                }
            },
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "string"},
                                "Value": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "NestedKey": {"type": "string"},
                                            "NestedObject": {
                                                "type": "object",
                                                "properties": {
                                                    "NestedObjectName": {
                                                        "type": "string"
                                                    }
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    }
                }
            },
            {
                "properties": {
                    "added": [
                        "/properties/Tags/*/Value",
                        "/properties/Tags/*/Value/*/NestedKey",
                        "/properties/Tags/*/Value/*/NestedObject",
                        "/properties/Tags/*/Value/*/NestedObject/NestedObjectName",
                    ]
                }
            },
            {
                "properties": {
                    "removed": [
                        "/properties/Tags/*/Value",
                        "/properties/Tags/*/Value/*/NestedKey",
                        "/properties/Tags/*/Value/*/NestedObject",
                        "/properties/Tags/*/Value/*/NestedObject/NestedObjectName",
                    ]
                }
            },
        ),
        # # Test Case #8: New Property with nested combiner (We might shelf this for now)
        # (
        #         {
        #             "properties": {
        #                 "Tags": {
        #                     'type': 'array',
        #                     'items': {
        #                         'anyOf': [
        #                             {
        #                                 'type': 'object',
        #                                 'properties': {
        #                                     'Key': {'type': 'string'},
        #                                     'Value': {'type': 'string'}
        #                                 }
        #                             }
        #                         ]
        #                     }
        #                 }
        #             }
        #         },
        #         {
        #             "properties": {
        #                 "Tags": {
        #                     'type': 'array',
        #                     'items': {
        #                         'anyOf': [
        #                             {
        #                                 'type': 'object',
        #                                 'properties': {
        #                                     'Key1': {'type': 'string'},
        #                                     'Value': {'type': 'string'}
        #                                 }
        #                             },
        #                             {
        #                                 'type': 'object',
        #                                 'properties': {
        #                                     'TagKey': {'type': 'string'},
        #                                     'TagValue': {'type': 'string'}
        #                                 }
        #                             }
        #                         ]
        #                     }
        #                 }
        #             }
        #         },
        #         {
        #             "properties": {
        #                 "added": [
        #                     "/properties/Tags/*/TagKey",
        #                     "/properties/Tags/*/TagValue",
        #                 ]
        #             }
        #         },
        #         {
        #             "properties": {
        #                 "removed": [
        #                     "/properties/Tags/*/TagKey",
        #                     "/properties/Tags/*/TagValue",
        #                 ]
        #             }
        #         },
        # ),
    ],
)
def test_schema_diff_complex_property_mutations(
    schema_variant1, schema_variant2, expected_diff, expected_diff_negative
):
    """

    Args:
        schema_variant1:
        schema_variant2:
        expected_diff:
        expected_diff_negative:
    """
    assert expected_diff == schema_diff(schema_variant1, schema_variant2)
    assert expected_diff_negative == schema_diff(schema_variant2, schema_variant1)


@pytest.mark.parametrize(
    "schema_variant1, schema_variant2, expected_diff, expected_diff_negative",
    [
        # Test Case #1: Type changed inside nested variable
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "string"},
                                "Value": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "NestedKey": {"type": "string"},
                                            "NestedKey2": {},
                                        },
                                    },
                                },
                            },
                        },
                    }
                }
            },
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "string"},
                                "Value": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "NestedKey": {"type": "integer"},
                                            "NestedKey2": {"type": "list"},
                                        },
                                    },
                                },
                            },
                        },
                    }
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "new_value": "integer",
                            "old_value": "string",
                            "property": "/properties/Tags/*/Value/*/NestedKey",
                        }
                    ],
                    "added": ["/properties/Tags/*/Value/*/NestedKey2"],
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "new_value": "string",
                            "old_value": "integer",
                            "property": "/properties/Tags/*/Value/*/NestedKey",
                        }
                    ],
                    "removed": ["/properties/Tags/*/Value/*/NestedKey2"],
                }
            },
        ),
        # Test Case #2: Enum change
        (
            {
                "properties": {
                    "MarvelComics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "SpiderMan": {
                                    "type": "string",
                                    "enum": [
                                        "AMAZING_SPIDERMAN",
                                        "AMAZING_SPIDERMAN2",
                                    ],
                                },
                            },
                        },
                    }
                }
            },
            {
                "properties": {
                    "MarvelComics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "SpiderMan": {
                                    "type": "string",
                                    "enum": [
                                        "AMAZING_SPIDERMAN",
                                        "AMAZING_SPIDERMAN2",
                                        "AMAZING_SPIDERMAN3",
                                    ],
                                },
                            },
                        },
                    }
                }
            },
            {"enum": {"added": ["AMAZING_SPIDERMAN3"]}},
            {"enum": {"removed": ["AMAZING_SPIDERMAN3"]}},
        ),
    ],
)
def test_schema_diff_complex_json_semantics_mutations(
    schema_variant1, schema_variant2, expected_diff, expected_diff_negative
):
    """

    Args:
        schema_variant1:
        schema_variant2:
        expected_diff:
        expected_diff_negative:
    """
    assert expected_diff == schema_diff(schema_variant1, schema_variant2)
    assert expected_diff_negative == schema_diff(schema_variant2, schema_variant1)


@pytest.mark.skip(reason="TODO: implement cobiners")
@pytest.mark.parametrize(
    "schema_variant1, schema_variant2, expected_diff, expected_diff_negative",
    [
        # Test Case #1: type changed from scalar to list
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                    }
                }
            },
            {"properties": {"Tags": {"type": ["array", "string"]}}},
            {
                "type": {
                    "changed": [
                        {
                            "new_value": ["array", "string"],
                            "old_value": "array",
                            "property": "/properties/Tags",
                        }
                    ]
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "old_value": ["array", "string"],
                            "new_value": "array",
                            "property": "/properties/Tags",
                        }
                    ]
                }
            },
        ),
        # Test Case #2: type changed from scalar to list using anyof
        (
            {
                "properties": {
                    "Tags": {
                        "type": "array",
                    }
                }
            },
            {
                "properties": {
                    "Tags": {"anyOf": [{"type": "array"}, {"type": "string"}]}
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "new_value": ["array", "string"],
                            "old_value": "array",
                            "property": "/properties/Tags",
                        }
                    ]
                }
            },
            {
                "type": {
                    "changed": [
                        {
                            "old_value": ["array", "string"],
                            "new_value": "array",
                            "property": "/properties/Tags",
                        }
                    ]
                }
            },
        ),
    ],
)
def test_schema_diff_complex_json_semantics_with_combiners_mutations(
    schema_variant1, schema_variant2, expected_diff, expected_diff_negative
):
    """

    Args:
        schema_variant1:
        schema_variant2:
        expected_diff:
        expected_diff_negative:
    """
    assert expected_diff == schema_diff(schema_variant1, schema_variant2)
    assert expected_diff_negative == schema_diff(schema_variant2, schema_variant1)
