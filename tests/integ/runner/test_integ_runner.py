# pylint: disable=C0302
"""
Integ test for runner.py
"""
import os
from pathlib import Path

import pytest

from rpdk.guard_rail.core.data_types import GuardRuleResult, Stateful, Stateless
from rpdk.guard_rail.core.runner import exec_compliance
from rpdk.guard_rail.utils.arg_handler import collect_schemas


@pytest.mark.parametrize(
    "collected_schemas,collected_rules,non_compliant_rules,warning_rules",
    [
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/sample-schema.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_primary_identifier_is_read_or_create_only": {
                    GuardRuleResult(
                        check_id="PID003",
                        message="primaryIdentifier MUST be either readOnly or createOnly",
                        path="/primaryIdentifier/2",
                    )
                },
                "verify_property_notation": {
                    GuardRuleResult(
                        check_id="PR005",
                        message="primaryIdentifier MUST have properties defined in the schema",
                        path="/primaryIdentifier/2",
                    ),
                    GuardRuleResult(
                        check_id="PR006",
                        message="createOnlyProperties MUST have properties defined in the schema",
                        path="/createOnlyProperties/1",
                    ),
                    GuardRuleResult(
                        check_id="PR007",
                        message="readOnlyProperties MUST have properties defined in the schema",
                        path="/readOnlyProperties/2",
                    ),
                    GuardRuleResult(
                        check_id="PR008",
                        message="writeOnlyProperties MUST have properties defined in the schema",
                        path="/writeOnlyProperties/1",
                    ),
                },
                "ensure_tagging_is_specified": {
                    GuardRuleResult(
                        check_id="TAG002",
                        message="`tagging` MUST be specified",
                        path="",
                    )
                },
            },
            {
                "ensure_properties_do_not_support_multitype": {
                    GuardRuleResult(
                        check_id="COM002",
                        message="type MUST NOT have combined definition",
                        path="/properties/KeyPolicy/type",
                    )
                },
                "ensure_arn_properties_contain_pattern": {
                    GuardRuleResult(
                        check_id="ARN002",
                        message="arn related property MUST have pattern specified",
                        path="",
                    )
                },
                "check_if_taggable_is_used": {
                    GuardRuleResult(
                        check_id="TAG001",
                        message="`taggable` is deprecated, please used `tagging` property",
                        path="/taggable",
                    )
                },
            },
        ),
        (
            # this particular test case makes sure that evaluation does not
            # procude duplicate checks, as guard returns dups when working with
            # collections
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-no-update-handler-incorrect-identifier.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_primary_identifier_is_read_or_create_only": {
                    GuardRuleResult(
                        check_id="PID003",
                        message="primaryIdentifier MUST be either readOnly or createOnly",
                        path="/primaryIdentifier/0",
                    )
                },
            },
            {
                "ensure_resource_update_handler_exists_and_have_permissions": {
                    GuardRuleResult(
                        check_id="PER005",
                        message="Resource SHOULD implement update handler",
                        path="",
                    )
                }
            },
        ),
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-update-handler-no-permissions.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_resource_update_handler_exists_and_have_permissions": {
                    GuardRuleResult(
                        check_id="PER006",
                        message="Resource update handler MUST have permissions list specified",
                        path="",
                    )
                },
            },
            {},
        ),
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-update-handler-empty-permissions.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_resource_update_handler_exists_and_have_permissions": {
                    GuardRuleResult(
                        check_id="PER006",
                        message="Resource update handler MUST have non-empty permissions",
                        path="/handlers/update/permissions",
                    )
                },
            },
            {},
        ),
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-malformed-tag-property.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_property_tags_exists_v2": {
                    GuardRuleResult(
                        check_id="TAG013",
                        message="`tagProperty` MUST specify property defined in the schema",
                        path="/tagging/tagProperty",
                    )
                },
            },
            {},
        ),
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-tag-property-writeonly.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_property_tags_exists_v2": {
                    GuardRuleResult(
                        check_id="TAG014",
                        message="`tagProperty` MUST NOT be a part of `writeOnlyProperties`",
                        path="/tagging/tagProperty",
                    )
                },
            },
            {},
        ),
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-primary-id-writeonly.json"
                        )
                    )
                ]
            ),
            [],
            {
                "ensure_primary_identifier_exists_and_not_empty": {
                    GuardRuleResult(
                        check_id="PID004",
                        message="primaryIdentifier MUST NOT be part of writeOnlyProperties",
                        path="/primaryIdentifier/0",
                    )
                },
            },
            {},
        ),
    ],
)
def test_exec_compliance_stateless(
    collected_schemas, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateless"""
    payload: Stateless = Stateless(schemas=collected_schemas, rules=collected_rules)
    compliance_result = exec_compliance(payload)[0]

    # Assert for non-compliant rules
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )
    # Assert for warning rules
    for warning_rule, warning_result in warning_rules.items():
        assert warning_rule in compliance_result.warning
        assert warning_result == compliance_result.warning[warning_rule]


@pytest.mark.parametrize(
    "collected_schemas,collected_rules,non_compliant_rules,warning_rules",
    [
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/aws-verifiedpermissions-policy.json"
                        )
                    )
                ]
            ),
            [],
            {
                "verify_property_notation": {
                    GuardRuleResult(
                        check_id="PR008",
                        message="writeOnlyProperties MUST have properties defined in the schema",
                        path="/writeOnlyProperties/1",
                    )
                },
            },
            {
                "ensure_properties_do_not_support_multitype": {
                    GuardRuleResult(
                        check_id="COM001",
                        message="each property MUST specify type",
                        path="/properties/Definition",
                    )
                },
            },
        ),
    ],
)
def test_exec_compliance_stateless_aws_verifiedpermissions_policy(
    collected_schemas, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateless"""
    payload: Stateless = Stateless(schemas=collected_schemas, rules=collected_rules)
    compliance_result = exec_compliance(payload)[0]

    # Assert for non-compliant rules
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )
    # Assert for warning rules
    for warning_rule, warning_result in warning_rules.items():
        assert warning_rule in compliance_result.warning
        assert warning_result == compliance_result.warning[warning_rule]


@pytest.mark.parametrize(
    "collected_schemas,collected_rules,non_compliant_rules,warning_rules",
    [
        (
            collect_schemas(
                schemas=[
                    "file:/"
                    + str(
                        Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                            "../data/schema-no-tagging-permission.json"
                        )
                    )
                ]
            ),
            [],
            {},
            {
                "ensure_property_tags_exists_v2": {
                    GuardRuleResult(
                        check_id="TAG011",
                        message="Resource MUST implement Tags property if `tagging.taggable` is true",
                        path="",
                    ),
                    GuardRuleResult(
                        check_id="TAG012",
                        message="Resource MUST provide `permissions` if `tagging.taggable` is true",
                        path="",
                    ),
                },
            },
        ),
    ],
)
def test_exec_compliance_stateless_tagging_permission_specified(
    collected_schemas, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateless"""
    payload: Stateless = Stateless(schemas=collected_schemas, rules=collected_rules)
    compliance_result = exec_compliance(payload)[0]

    # Assert for non-compliant rules
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )
    # Assert for warning rules
    for warning_rule, warning_result in warning_rules.items():
        assert warning_rule in compliance_result.warning
        assert warning_result == compliance_result.warning[warning_rule]


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            {"primaryIdentifier": ["bar"]},
            {"primaryIdentifier": ["bar_changed", "bar_added"]},
            [],
            {
                "ensure_primary_identifier_not_changed": {
                    GuardRuleResult(
                        check_id="PID001",
                        message="primaryIdentifier cannot add more members",
                        path="/primaryIdentifier/added",
                    ),
                    GuardRuleResult(
                        check_id="PID002",
                        message="primaryIdentifier cannot remove members",
                        path="/primaryIdentifier/removed",
                    ),
                }
            },
            [],
        ),
        (
            {
                "typeName": "AWS::ARCZonalShift::ZonalAutoshiftConfiguration",
                "description": "Definition of AWS::ARCZonalShift::ZonalAutoshiftConfiguration Resource Type",
                "definitions": {
                    "ZonalAutoshiftStatus": {"type": "string", "enum": ["ENABLED"]},
                },
                "properties": {
                    "ZonalAutoshiftStatus": {
                        "$ref": "#/definitions/ZonalAutoshiftStatus"
                    },
                },
            },
            {
                "typeName": "AWS::ARCZonalShift::ZonalAutoshiftConfiguration",
                "description": "Definition of AWS::ARCZonalShift::ZonalAutoshiftConfiguration Resource Type",
                "definitions": {
                    "ZonalAutoshiftStatus": {"type": "string", "enum": ["ENABLED"]},
                },
                "properties": {
                    "ZonalAutoshiftStatus": {
                        "$ref": "#/definitions/ZonalAutoshiftStatus",
                        "dependencies": {
                            "ZonalAutoshiftStatus": ["PracticeRunConfiguration"]
                        },
                    },
                },
            },
            [],
            {},
            [],
        ),
    ],
)
def test_exec_compliance_stateful(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateful"""
    try:
        payload: Stateful = Stateful(
            previous_schema=previous_schema,
            current_schema=current_schema,
            rules=collected_rules,
        )
        compliance_result = exec_compliance(payload)[0]

        if not non_compliant_rules:
            assert not compliance_result.non_compliant

        for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
            assert non_compliant_rule in compliance_result.non_compliant
            assert (
                non_compliant_result
                == compliance_result.non_compliant[non_compliant_rule]
            )
    except NotImplementedError as e:
        assert "Stateful evaluation is not supported yet" == str(e)


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            {
                "properties": {
                    "DeprecatedProperty": {},
                    "WriteOnlyProp": {},
                    "Name": {},
                    "Enum": {},
                    "LastName": {},
                },
                "createOnlyProperties": ["/properties/Name"],
                "writeOnlyProperties": [],
                "readOnlyProperties": [
                    "/properties/LastName",
                ],
                "primaryIdentifier": ["/properties/Name"],
            },
            {
                "properties": {
                    "WriteOnlyProp": {},
                    "Name": {},
                    "Enum": {},
                    "LastName": {},
                    "Prop": {},
                },
                "createOnlyProperties": [
                    "/properties/Name",
                    "/properties/LastName",
                ],
                "writeOnlyProperties": [
                    "/properties/WriteOnlyProp",
                ],
                "readOnlyProperties": [
                    "/properties/Name",
                ],
                "primaryIdentifier": ["/properties/LastName"],
            },
            [],
            {
                "ensure_old_property_not_removed": {
                    GuardRuleResult(
                        check_id="PR001",
                        message="Resource properties MUST NOT be removed",
                        path="/properties/removed",
                    )
                },
                "ensure_old_property_not_turned_immutable": {
                    GuardRuleResult(
                        check_id="PR002",
                        message="Only NEWLY ADDED properties can be marked as createOnlyProperties",
                        path="/createOnlyProperties/added/0",
                    )
                },
                "ensure_old_property_not_turned_writeonly": {
                    GuardRuleResult(
                        check_id="PR003",
                        message="Only NEWLY ADDED properties can be marked as writeOnlyProperties",
                        path="/writeOnlyProperties/added/0",
                    )
                },
                "ensure_old_property_not_removed_from_readonly": {
                    GuardRuleResult(
                        check_id="PR004",
                        message="Only NEWLY ADDED properties can be marked as readOnlyProperties",
                        path="/readOnlyProperties/added/0",
                    ),
                    GuardRuleResult(
                        check_id="PR005",
                        message="Resource properties MUST NOT be removed from readOnlyProperties",
                        path="/readOnlyProperties/removed",
                    ),
                },
                "ensure_primary_identifier_not_changed": {
                    GuardRuleResult(
                        check_id="PID001",
                        message="primaryIdentifier cannot add more members",
                        path="/primaryIdentifier/added",
                    ),
                    GuardRuleResult(
                        check_id="PID002",
                        message="primaryIdentifier cannot remove members",
                        path="/primaryIdentifier/removed",
                    ),
                },
            },
            [],
        ),
    ],
)
def test_exec_compliance_stateful_properties_breaking_changes(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateful"""
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)[0]
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            {
                "properties": {
                    "DeprecatedProperty": {},
                    "WriteOnlyProp": {"type": "string"},
                    "Name": {},
                    "Enum": {"type": "string", "enum": ["VALUE1"]},
                    "LastName": {"type": "string"},
                },
                "required": ["Name"],
            },
            {
                "properties": {
                    "WriteOnlyProp": {"type": "boolean"},
                    "Name": {"type": "string"},
                    "Enum": {"type": "string"},
                    "LastName": {},
                    "Prop": {},
                },
                "required": ["Name", "LastName"],
            },
            [],
            {
                "ensure_old_property_not_removed": {
                    GuardRuleResult(
                        check_id="PR001",
                        message="Resource properties MUST NOT be removed",
                        path="/properties/removed",
                    )
                },
                "ensure_no_more_required_properties": {
                    GuardRuleResult(
                        check_id="RQ001",
                        message="cannot add more REQUIRED properties",
                        path="/required/added",
                    )
                },
                "ensure_property_type_not_changed": {
                    GuardRuleResult(
                        check_id="TP001",
                        message="Only NEWLY ADDED properties can have new type added",
                        path="/type/added/0",
                    ),
                    GuardRuleResult(
                        check_id="TP002",
                        message="cannot remove TYPE from a property",
                        path="/type/removed",
                    ),
                    GuardRuleResult(
                        check_id="TP003",
                        message="cannot change TYPE of a property",
                        path="/type/changed",
                    ),
                },
                "ensure_enum_not_changed": {
                    GuardRuleResult(
                        check_id="ENM001",
                        message="CANNOT remove values from enum",
                        path="/enum/removed",
                    )
                },
            },
            [],
        ),
    ],
)
def test_exec_compliance_stateful_json_breaking_changes(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateful"""
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)[0]

    assert len(non_compliant_rules.keys()) == len(
        compliance_result.non_compliant.keys()
    )

    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            {
                "properties": {
                    "MiddleName": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 20,
                        "pattern": "value1",
                    },
                    "LastName": {
                        "type": "string",
                    },
                    "Name": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 20,
                        "pattern": "value1",
                    },
                    "Friends": {"type": "array", "minItems": 2, "maxItems": 3},
                    "Pets": {
                        "type": "array",
                    },
                    "Relatives": {"type": "array", "minItems": 2, "maxItems": 3},
                    "YearsOfEx": {"type": "array", "minimum": 1, "maximum": 100},
                    "Degrees": {
                        "type": "number",
                    },
                    "Age": {"type": "number", "minimum": 1, "maximum": 100},
                },
            },
            {
                "properties": {
                    "MiddleName": {
                        "type": "string",
                    },
                    "LastName": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 20,
                        "pattern": "value1",
                    },
                    "Name": {
                        "type": "string",
                        "minLength": 11,
                        "maxLength": 19,
                        "pattern": "value2",
                    },
                    "Friends": {
                        "type": "array",
                    },
                    "Pets": {"type": "array", "minItems": 2, "maxItems": 3},
                    "Relatives": {"type": "array", "minItems": 3, "maxItems": 2},
                    "YearsOfEx": {"type": "array"},
                    "Degrees": {"type": "number", "minimum": 1, "maximum": 100},
                    "Age": {"type": "number", "minimum": 100, "maximum": 1},
                    "Prop": {},
                },
            },
            [],
            {
                "ensure_minlength_not_contracted": {
                    GuardRuleResult(
                        check_id="ML001",
                        message="cannot remove minLength from properties",
                        path="/minLength/removed",
                    ),
                    GuardRuleResult(
                        check_id="ML002",
                        message="only NEWLY ADDED properties can have additional minLength constraint",
                        path="/minLength/added/0",
                    ),
                    GuardRuleResult(
                        check_id="ML003",
                        message="new minLength value cannot exceed old value",
                        path="/minLength/changed/0/old_value",
                    ),
                },
                "ensure_maxlength_not_contracted": {
                    GuardRuleResult(
                        check_id="ML004",
                        message="cannot remove maxLength from properties",
                        path="/maxLength/removed",
                    ),
                    GuardRuleResult(
                        check_id="ML005",
                        message="only NEWLY ADDED properties can have additional maxLength constraint",
                        path="/maxLength/added/0",
                    ),
                    GuardRuleResult(
                        check_id="ML006",
                        message="new maxLength value cannot be less than the old value",
                        path="/maxLength/changed/0/old_value",
                    ),
                },
                "ensure_minitems_not_contracted": {
                    GuardRuleResult(
                        check_id="MI001",
                        message="cannot remove minItems from properties",
                        path="/minItems/removed",
                    ),
                    GuardRuleResult(
                        check_id="MI002",
                        message="only NEWLY ADDED properties can have additional minItems constraint",
                        path="/minItems/added/0",
                    ),
                    GuardRuleResult(
                        check_id="MI003",
                        message="new minItems value cannot exceed old value",
                        path="/minItems/changed/0/old_value",
                    ),
                },
                "ensure_maxitems_not_contracted": {
                    GuardRuleResult(
                        check_id="MI004",
                        message="cannot remove maxItems from properties",
                        path="/maxItems/removed",
                    ),
                    GuardRuleResult(
                        check_id="MI005",
                        message="only NEWLY ADDED properties can have additional maxItems constraint",
                        path="/maxItems/added/0",
                    ),
                    GuardRuleResult(
                        check_id="MI006",
                        message="new maxItems value cannot be less than the old value",
                        path="/maxItems/changed/0/old_value",
                    ),
                },
                "ensure_minimum_not_contracted": {
                    GuardRuleResult(
                        check_id="MI007",
                        message="cannot remove minimum from properties",
                        path="/minimum/removed",
                    ),
                    GuardRuleResult(
                        check_id="MI008",
                        message="only NEWLY ADDED properties can have additional minimum constraint",
                        path="/minimum/added/0",
                    ),
                    GuardRuleResult(
                        check_id="MI009",
                        message="new minimum value cannot exceed old value",
                        path="/minimum/changed/0/old_value",
                    ),
                },
                "ensure_maximum_not_contracted": {
                    GuardRuleResult(
                        check_id="MI010",
                        message="cannot remove maximum from properties",
                        path="/maximum/removed",
                    ),
                    GuardRuleResult(
                        check_id="MI011",
                        message="only NEWLY ADDED properties can have additional maximum constraint",
                        path="/maximum/added/0",
                    ),
                    GuardRuleResult(
                        check_id="MI012",
                        message="new maximum value cannot be less than the old value",
                        path="/maximum/changed/0/old_value",
                    ),
                },
            },
            {
                "ensure_property_string_pattern_not_changed": {
                    GuardRuleResult(
                        check_id="PAT001",
                        message="Only NEWLY ADDED properties can have new pattern added",
                        path="/pattern/added/0",
                    ),
                    GuardRuleResult(
                        check_id="PAT002",
                        message="cannot remove PATTERN from a property",
                        path="/pattern/removed",
                    ),
                    GuardRuleResult(
                        check_id="PAT003",
                        message="cannot change PATTERN of a property",
                        path="/pattern/changed",
                    ),
                },
            },
        ),
    ],
)
def test_exec_compliance_stateful_json_validation_breaking_changes(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateful"""
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)[0]
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )
    for warning_rule, warning_result in warning_rules.items():
        assert warning_rule in compliance_result.warning
        assert warning_result == compliance_result.warning[warning_rule]


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            {
                "properties": {
                    "LastName": {
                        "type": "string",
                    },
                    "Name": {
                        "type": "string",
                    },
                },
                "createOnlyProperties": [
                    "/properties/Name",
                ],
            },
            {
                "properties": {
                    "LastName": {
                        "type": "string",
                    },
                    "Name": {
                        "type": "string",
                    },
                },
                "createOnlyProperties": [
                    "/properties/Name",
                    "/properties/LastName",
                ],
            },
            [],
            {
                "ensure_old_property_not_turned_immutable": {
                    GuardRuleResult(
                        check_id="PR002",
                        message="Only NEWLY ADDED properties can be marked as createOnlyProperties",
                        path="/createOnlyProperties/added",
                    )
                },
            },
            [],
        ),
    ],
)
def test_exec_compliance_stateful_create_only_breaking_change_with_no_properties_change(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateful"""
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)[0]
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )


@pytest.mark.parametrize(
    "previous_schema, current_schema, collected_rules,non_compliant_rules,warning_rules",
    [
        (
            {
                "properties": {
                    "LastName": {
                        "type": "string",
                        "default": "Snow",
                    },
                    "Name": {
                        "type": "string",
                        "default": "Jon",
                    },
                },
            },
            {
                "properties": {
                    "LastName": {
                        "type": "string",
                        "default": "Targaryen",
                    },
                    "Name": {
                        "type": "string",
                        "default": "Jon",
                    },
                },
            },
            [],
            {
                "ensure_default_values_have_not_changed": {
                    GuardRuleResult(
                        check_id="TFDF002",
                        message="cannot change default values",
                        path="/default/changed",
                    )
                },
            },
            [],
        ),
        (
            {
                "properties": {
                    "LastName": {
                        "type": "string",
                        "default": "Snow",
                    },
                    "Name": {
                        "type": "string",
                        "default": "Jon",
                    },
                },
            },
            {
                "properties": {
                    "LastName": {
                        "type": "string",
                    },
                    "Name": {
                        "type": "string",
                        "default": "Jon",
                    },
                },
            },
            [],
            {
                "ensure_default_values_have_not_changed": {
                    GuardRuleResult(
                        check_id="TFDF001",
                        message="cannot remove default values from properties",
                        path="/default/removed",
                    )
                },
            },
            [],
        ),
    ],
)
def test_exec_compliance_stateful_default_value_breaking_change(
    previous_schema, current_schema, collected_rules, non_compliant_rules, warning_rules
):
    """Test exec_compliance for stateful"""
    payload: Stateful = Stateful(
        previous_schema=previous_schema,
        current_schema=current_schema,
        rules=collected_rules,
    )
    compliance_result = exec_compliance(payload)[0]
    for non_compliant_rule, non_compliant_result in non_compliant_rules.items():
        assert non_compliant_rule in compliance_result.non_compliant
        assert (
            non_compliant_result == compliance_result.non_compliant[non_compliant_rule]
        )
