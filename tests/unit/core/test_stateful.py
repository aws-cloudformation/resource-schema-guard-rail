# pylint: disable=C0301
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
                                    "insertionOrder": True,
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
                        "insertionOrder": True,
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
                },
                "insertionOrder": {"added": ["/properties/Tags"]},
            },
            {
                "properties": {
                    "removed": [
                        "/properties/Tags/*/Value",
                    ]
                },
                "insertionOrder": {"removed": ["/properties/Tags"]},
            },
        ),
        # Test Case #6: Modified Nested Property
        (
            {
                "properties": {
                    "Configuration": {
                        "type": "object",
                        "properties": {
                            "ExecuteCommandConfiguration": {
                                "type": "object",
                                "properties": {
                                    "KmsKeyId": {
                                        "type": "string",
                                        "relationshipRef": {
                                            "typeName": "AWS::KMS::Key",
                                            "propertyPath": "/properties/Arn",
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"Key": {"type": "string"}},
                        },
                    },
                }
            },
            {
                "properties": {
                    "Configuration": {
                        "type": "object",
                        "properties": {
                            "ExecuteCommandConfiguration": {
                                "type": "object",
                                "properties": {
                                    "KmsKeyId": {
                                        "type": "string",
                                    }
                                },
                            }
                        },
                    },
                    "Tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Key": {"type": "int"},
                            },
                        },
                    },
                }
            },
            {
                "relationshipRef": {
                    "removed": [
                        "/properties/Configuration/ExecuteCommandConfiguration/KmsKeyId"
                    ]
                },
                "type": {
                    "changed": [
                        {
                            "new_value": "int",
                            "old_value": "string",
                            "property": "/properties/Tags/*/Key",
                        }
                    ]
                },
            },
            {
                "relationshipRef": {
                    "added": [
                        "/properties/Configuration/ExecuteCommandConfiguration/KmsKeyId"
                    ]
                },
                "type": {
                    "changed": [
                        {
                            "new_value": "string",
                            "old_value": "int",
                            "property": "/properties/Tags/*/Key",
                        }
                    ]
                },
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
        # Test Case #8: ECS Schema Snippet with cfn leaf constructs
        # almost integ tests but not because we are not verifying checks
        (
            {
                "definitions": {
                    "CapacityProviderStrategyItem": {
                        "description": "A capacity provider strategy consists of one or more capacity providers along with the `base` and `weight` to assign to them. A capacity provider must be associated with the cluster to be used in a capacity provider strategy. The PutClusterCapacityProviders API is used to associate a capacity provider with a cluster. Only capacity providers with an `ACTIVE` or `UPDATING` status can be used.",
                        "additionalProperties": False,
                        "type": "object",
                        "properties": {
                            "CapacityProvider": {"type": "string"},
                            "Weight": {"type": "integer"},
                            "Base": {"type": "integer"},
                        },
                    },
                    "Configuration": {
                        "type": "object",
                        "properties": {
                            "ExecuteCommandConfiguration": {
                                "$ref": "#/definitions/ExecuteCommandConfiguration"
                            }
                        },
                        "additionalProperties": False,
                    },
                    "ExecuteCommandConfiguration": {
                        "type": "object",
                        "properties": {"KmsKeyId": {"type": "string"}},
                        "additionalProperties": False,
                    },
                    "ClusterSettings": {
                        "description": "The settings to use when creating a cluster. This parameter is used to turn on CloudWatch Container Insights for a cluster.",
                        "type": "object",
                        "properties": {
                            "Name": {
                                "type": "string",
                                "description": "The name of the cluster setting. The value is ``containerInsights`` .",
                            },
                            "Value": {
                                "type": "string",
                                "description": "The value to set for the cluster setting. The supported values are ``enabled`` and ``disabled``. \n If you set ``name`` to ``containerInsights`` and ``value`` to ``enabled``, CloudWatch Container Insights will be on for the cluster, otherwise it will be off unless the ``containerInsights`` account setting is turned on. If a cluster value is specified, it will override the ``containerInsights`` value set with [PutAccountSetting](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_PutAccountSetting.html) or [PutAccountSettingDefault](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_PutAccountSettingDefault.html).",
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "properties": {
                    "ClusterSettings": {
                        "type": "array",
                        "insertionOrder": True,
                        "items": {"$ref": "#/definitions/ClusterSettings"},
                        "description": "The settings to use when creating a cluster. This parameter is used to turn on CloudWatch Container Insights for a cluster.",
                    },
                    "DefaultCapacityProviderStrategy": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/CapacityProviderStrategyItem"},
                        "description": "The default capacity provider strategy for the cluster. When services or tasks are run in the cluster with no launch type or capacity provider strategy specified, the default capacity provider strategy is used.",
                    },
                    "Configuration": {"$ref": "#/definitions/Configuration"},
                    "Arn": {"type": "string"},
                },
            },
            {
                "definitions": {
                    "CapacityProviderStrategyItem": {
                        "description": "A capacity provider strategy consists of one or more capacity providers along with the `base` and `weight` to assign to them. A capacity provider must be associated with the cluster to be used in a capacity provider strategy. The PutClusterCapacityProviders API is used to associate a capacity provider with a cluster. Only capacity providers with an `ACTIVE` or `UPDATING` status can be used.",
                        "additionalProperties": False,
                        "type": "object",
                        "properties": {
                            "CapacityProvider": {
                                "type": "string",
                                "relationshipRef": {
                                    "typeName": "AWS::ECS::CapacityProvider",
                                    "propertyPath": "/properties/Name",
                                },
                            },
                            "Weight": {"type": "integer"},
                            "Base": {"type": "integer"},
                        },
                    },
                    "Configuration": {
                        "type": "object",
                        "properties": {
                            "ExecuteCommandConfiguration": {
                                "$ref": "#/definitions/ExecuteCommandConfiguration"
                            }
                        },
                        "additionalProperties": False,
                    },
                    "ExecuteCommandConfiguration": {
                        "type": "object",
                        "properties": {
                            "KmsKeyId": {
                                "type": "string",
                                "relationshipRef": {
                                    "typeName": "AWS::KMS::Key",
                                    "propertyPath": "/properties/Arn",
                                },
                            },
                            "Logging": {
                                "type": "string",
                                "description": "The log setting to use for redirecting logs for your execute command results. The following log settings are available.\n  +   ``NONE``: The execute command session is not logged.\n  +   ``DEFAULT``: The ``awslogs`` configuration in the task definition is used. If no logging parameter is specified, it defaults to this value. If no ``awslogs`` log driver is configured in the task definition, the output won't be logged.\n  +   ``OVERRIDE``: Specify the logging details as a part of ``logConfiguration``. If the ``OVERRIDE`` logging option is specified, the ``logConfiguration`` is required.",
                            },
                        },
                        "additionalProperties": False,
                    },
                    "ClusterSettings": {
                        "description": "The settings to use when creating a cluster. This parameter is used to turn on CloudWatch Container Insights for a cluster.",
                        "type": "object",
                        "properties": {
                            "Name": {
                                "type": "string",
                                "description": "The name of the cluster setting. The value is ``containerInsights`` .",
                            },
                            "Value": {
                                "type": "string",
                                "description": "The value to set for the cluster setting. The supported values are ``enabled`` and ``disabled``. \n If you set ``name`` to ``containerInsights`` and ``value`` to ``enabled``, CloudWatch Container Insights will be on for the cluster, otherwise it will be off unless the ``containerInsights`` account setting is turned on. If a cluster value is specified, it will override the ``containerInsights`` value set with [PutAccountSetting](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_PutAccountSetting.html) or [PutAccountSettingDefault](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_PutAccountSettingDefault.html).",
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "properties": {
                    "ClusterSettings": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/ClusterSettings"},
                        "description": "The settings to use when creating a cluster. This parameter is used to turn on CloudWatch Container Insights for a cluster.",
                    },
                    "DefaultCapacityProviderStrategy": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/CapacityProviderStrategyItem"},
                        "description": "The default capacity provider strategy for the cluster. When services or tasks are run in the cluster with no launch type or capacity provider strategy specified, the default capacity provider strategy is used.",
                    },
                    "ECSEndpoint": {"type": "string"},
                    "Configuration": {"$ref": "#/definitions/Configuration"},
                    "Arn": {"type": "string"},
                },
            },
            {
                "properties": {
                    "added": [
                        "/properties/ECSEndpoint",
                        "/properties/Configuration/ExecuteCommandConfiguration/Logging",
                    ]
                },
                "relationshipRef": {
                    "added": [
                        "/properties/DefaultCapacityProviderStrategy/*/CapacityProvider",
                        "/properties/Configuration/ExecuteCommandConfiguration/KmsKeyId",
                    ]
                },
                "insertionOrder": {"removed": ["/properties/ClusterSettings"]},
            },
            {
                "properties": {
                    "removed": [
                        "/properties/ECSEndpoint",
                        "/properties/Configuration/ExecuteCommandConfiguration/Logging",
                    ]
                },
                "relationshipRef": {
                    "removed": [
                        "/properties/DefaultCapacityProviderStrategy/*/CapacityProvider",
                        "/properties/Configuration/ExecuteCommandConfiguration/KmsKeyId",
                    ]
                },
                "insertionOrder": {"added": ["/properties/ClusterSettings"]},
            },
        ),
        # # Test Case #9: New Property with nested combiner (We might shelf this for now)
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


@pytest.mark.parametrize(
    "schema_variant1, schema_variant2, expected_diff, expected_diff_negative",
    [
        (
            {
                "primaryIdentifier": [
                    "/properties/A",
                    "/properties/B",
                ]
            },
            {
                "primaryIdentifier": [
                    "/properties/B",
                    "/properties/A",
                ]
            },
            {
                "primaryIdentifier": {
                    "added": ["/properties/B", "/properties/A"],
                    "removed": ["/properties/A", "/properties/B"],
                }
            },
            {
                "primaryIdentifier": {
                    "added": ["/properties/A", "/properties/B"],
                    "removed": ["/properties/B", "/properties/A"],
                }
            },
        )
    ],
)
def test_schema_diff_primary_identifier_order_change(
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
        # Test Case #2: type changed from list using anyof
        (
            {
                "properties": {
                    "Tags": {"anyOf": [{"type": "array"}, {"type": "string"}]}
                }
            },
            {
                "properties": {
                    "Tags": {
                        "anyOf": [
                            {"type": "array"},
                            {"type": "string"},
                            {"type": "integer"},
                        ]
                    }
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
    try:
        assert expected_diff == schema_diff(schema_variant1, schema_variant2)
        assert expected_diff_negative == schema_diff(schema_variant2, schema_variant1)
    except NotImplementedError as e:
        assert (
            "Schemas with combiners are not yet supported for stateful evaluation"
            == str(e)
        )
