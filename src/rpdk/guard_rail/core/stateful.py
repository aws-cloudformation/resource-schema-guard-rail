"""Module to perform stateful schema diff.

The main idea is to run two json blobs (v1, v2) over deepdiff module;
This module will generate a metadiff, which will have three main categories:
1. iterable
2. values change
3. dictionary change


#1 covers most CFN invented constructs
#2 covers arbitrary changes in values
#3 covers any new item added/removed


Typical usage example:

    schema_v1 = ...
    schema_v2 = ...
    schema_meta_diff = schema_diff(schema_v1, schema_v2)
"""
import re
from copy import copy
from enum import auto
from functools import partial
from typing import Any, Dict, Iterable

from deepdiff import DeepDiff
from rich.console import Console

import strenum
from rpdk.guard_rail.utils.schema_utils import resolve_schema

console = Console()


class METADIFF(strenum.LowercaseStrEnum):
    ITERABLE_ITEM_ADDED = auto()
    ITERABLE_ITEM_REMOVED = auto()
    VALUES_CHANGED = auto()
    TYPE_CHANGES = auto()
    DICTIONARY_ITEM_ADDED = auto()
    DICTIONARY_ITEM_REMOVED = auto()


class DIFFKEYS:
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    OLD_VALUE = "old_value"
    NEW_VALUE = "new_value"
    PROPERTY = "property"


PROPERTIES = "properties"
cfn_list_constructs = {
    "primaryIdentifier",
    "readOnlyProperties",
    "writeOnlyProperties",
    "createOnlyProperties",
    "additionalIdentifiers",
}

combiners = {
    "allOf",
    "anyOf",
    "oneOf",
}

cfn_leaf_level_constructs = {
    "relationshipRef",
    "insertionOrder",
    "arrayType",
}

native_constructs = {
    "type",
    "description",
    "enum",
    "maximum",
    "minimum",
    "maxLength",
    "minLength",
    "required",
    "pattern",
    "maxItems",
    "minItems",
    "contains",
    "items",
    "additionalProperties",
    "uniqueItems",
    "dependencies",
    "default",
}


def schema_diff(previous_json: Dict[str, Any], current_json: Dict[str, Any]):
    """schema diff function to get formatted schema diff from deep diff"""

    previous_schema = resolve_schema(previous_json)
    current_schema = resolve_schema(current_json)

    deep_diff = DeepDiff(
        previous_schema,
        current_schema,
        ignore_order_func=lambda level: "primaryIdentifier" not in level.path(),
        verbose_level=2,
    )

    meta_diff = _translate_meta_diff(deep_diff.to_dict())
    console.rule("[bold red][GENERATED DIFF BETWEEN SCHEMAS]")
    console.print(
        meta_diff,
        style="link https://google.com",
        highlight=True,
        justify="left",
        soft_wrap=True,
    )
    return meta_diff


def _is_combiner_property(path_list):
    """This method accepts an array of steps.
    If set is not empty and it starts with `properties`
    and ends with combiner, then it's considered
    to be a combiner property"""
    return (
        len(path_list) > 0 and path_list[0] == PROPERTIES and path_list[-1] in combiners
    )


def _is_resource_property(path_list):
    """This method accepts an array of steps.
    If set is not empty and it starts with `properties`
    and ends with non-json construct, then it's considered
    to be a property"""
    return (
        len(path_list) > 0
        and path_list[0] == PROPERTIES
        and path_list[-1] not in native_constructs
        and path_list[-1] not in cfn_leaf_level_constructs
    )


def _is_cfn_construct(path_list):
    """This method defines cfn constructs"""
    return len(path_list) == 1 and path_list[0] in cfn_list_constructs


def _is_json_construct(path_list):
    """This method defines json constructs"""
    return len(path_list) > 0 and path_list[-1] in native_constructs


def _is_cfn_leaf_construct(path_list):
    """This method defines json constructs"""
    return len(path_list) > 0 and path_list[-1] in cfn_leaf_level_constructs


def _get_path(path_list):
    """This method converts array into schema path notation"""
    return "/".join([""] + path_list)


def _cast_path(value: str):
    """cast the path of the change to process constructs"""
    pattern = r"(?<=\[)'?([\s\S]+?)'?(?=\])"
    value = value.replace("items']['properties", "*")
    value = value.replace("]['properties'][", "][")
    value = re.sub(r"[0-9]+]", "", value)
    return re.findall(pattern, value)


def _add_item(
    schema_meta_diff: Dict[str, Any],
    result_key: str,
    change_key: str,
    result_value: Any,
):
    """Appends values to existing/new meta diff values"""
    if result_key not in schema_meta_diff:
        schema_meta_diff[result_key] = {}
    if change_key in schema_meta_diff[result_key]:
        schema_meta_diff[result_key][change_key].append(result_value)
    else:
        schema_meta_diff[result_key][change_key] = [result_value]


def _traverse_nested_properties(
    schema_meta_diff: Dict[str, Any], result_key: str, prefix: str, diff_value: Any
):
    """Traverses a fragment of json schema.
    Checks for type - only array/object can have nested properties

    Args:
        schema_meta_diff (Dict[str, Any]): dictionary of translated schema diff
        result_key (str): Key to append to
        prefix (str): property path
        diff_value (Any): arbitrary value
    """

    # cfn might have more custom leaf level props
    # if not specifically added to cfn_leaf_level_constructs
    # it could be traversed further and interpreted as a property
    # this hedges out from lookup/attribute/unbounded exceptions
    if not diff_value or not isinstance(diff_value, dict):
        return

    # if type is absent, then we are dealing with properties
    if "type" not in diff_value:
        for property_name, property_definition in diff_value.items():
            _add_item(
                schema_meta_diff,
                PROPERTIES,
                result_key,
                prefix + "/" + property_name,
            )

            _traverse_nested_properties(
                schema_meta_diff,
                result_key,
                prefix + "/" + property_name,
                property_definition,
            )
        return

    # otherwise we could be dealing with complex types
    property_type = diff_value["type"]

    properties = {}
    new_prefix = copy(prefix)

    # only array and object might have nested properties
    if property_type == "array":
        new_prefix = prefix + "/*"
        properties = diff_value.get("items", {}).get("properties", {})
    elif property_type == "object":
        properties = diff_value.get("properties", {})

    _traverse_nested_properties(
        schema_meta_diff,
        result_key,
        new_prefix,
        properties,
    )


def _translate_iterable_change(
    changed: DIFFKEYS, schema_meta_diff: Dict[str, Any], diff_value: Any
):
    """Translates iterable diff.
    This will go over iterable changes and translate
    into metadiff structure; Mostly covers cfn and
    json keywords;

    Args:
        changed (DIFFKEYS): keyword to append to
        schema_meta_diff (Dict[str, Any]): dictionary of translated schema diff
        diff_value (Any): arbitrary diff
    """

    def __translate_iter_added_diff(diffkey, schema_meta_diff, diff_value):
        for key, value in diff_value.items():
            path_list = _cast_path(key)
            if _is_combiner_property(path_list):
                raise NotImplementedError(
                    "Schemas with combiners are not yet supported for stateful evaluation"
                )
            if _is_cfn_construct(path_list):
                _add_item(schema_meta_diff, path_list[0], diffkey, value)

            if _is_json_construct(path_list):
                _add_item(
                    schema_meta_diff,
                    path_list[-1],
                    diffkey,
                    value,
                )
            if _is_cfn_leaf_construct(path_list):
                _add_item(
                    schema_meta_diff,
                    path_list[-1],
                    diffkey,
                    value,
                )

    # using partial to avoid code repetition
    append_added = partial(__translate_iter_added_diff, DIFFKEYS.ADDED)
    append_removed = partial(__translate_iter_added_diff, DIFFKEYS.REMOVED)

    if changed == DIFFKEYS.ADDED:
        append_added(schema_meta_diff, diff_value)
        return
    if changed == DIFFKEYS.REMOVED:
        append_removed(schema_meta_diff, diff_value)
        return

    raise NotImplementedError("Invalid")


def _translate_dict_change(
    changed: DIFFKEYS, schema_meta_diff: Dict[str, Any], diff_value: Any
):
    """Translates dictionary diff.
    This will go over dictionary changes and translate
    into metadiff structure; Mostly covers properties and
    json keywords;

    Args:
        changed (DIFFKEYS): keyword to append to
        schema_meta_diff (Dict[str, Any]): dictionary of translated schema diff
        diff_value (Any): arbitrary diff
    """

    def __translate_dict_diff(diffkey, schema_meta_diff, diff_value):
        for key, value in diff_value.items():
            path_list = _cast_path(key)
            if _is_combiner_property(path_list):
                raise NotImplementedError(
                    "Schemas with combiners are not yet supported for stateful evaluation"
                )
            if _is_resource_property(path_list):
                _add_item(schema_meta_diff, PROPERTIES, diffkey, _get_path(path_list))
                if isinstance(value, dict):
                    _traverse_nested_properties(
                        schema_meta_diff, diffkey, _get_path(path_list), value
                    )
            if _is_json_construct(path_list):
                _add_item(
                    schema_meta_diff,
                    path_list[-1],
                    diffkey,
                    _get_path(path_list[:-1]),
                )
            if _is_cfn_leaf_construct(path_list):
                _add_item(
                    schema_meta_diff,
                    path_list[-1],
                    diffkey,
                    _get_path(path_list[:-1]),
                )

    # using partial to avoid code repetition
    append_added = partial(__translate_dict_diff, DIFFKEYS.ADDED)
    append_removed = partial(__translate_dict_diff, DIFFKEYS.REMOVED)

    if changed == DIFFKEYS.ADDED:
        append_added(schema_meta_diff, diff_value)
        return
    if changed == DIFFKEYS.REMOVED:
        append_removed(schema_meta_diff, diff_value)
        return

    raise NotImplementedError("Not Supported")


def _translate_values_changed_diff_(schema_meta_diff, diff_value):
    """Translates values diff.
    This will go over value changes and translate
    into metadiff structure; Mostly covers cfn and
    json keywords;

    Args:
        schema_meta_diff (Dict[str, Any]): dictionary of translated schema diff
        diff_value (Any): arbitrary diff
    """
    for key, value in diff_value.items():
        path_list = _cast_path(key)
        if _is_cfn_construct(path_list):
            _add_item(
                schema_meta_diff,
                path_list[0],
                DIFFKEYS.REMOVED,
                value[DIFFKEYS.OLD_VALUE],
            )
            _add_item(
                schema_meta_diff,
                path_list[0],
                DIFFKEYS.ADDED,
                value[DIFFKEYS.NEW_VALUE],
            )
        if _is_json_construct(path_list):
            _add_item(
                schema_meta_diff,
                path_list[-1],
                DIFFKEYS.CHANGED,
                {
                    DIFFKEYS.PROPERTY: _get_path(path_list[:-1]),
                    DIFFKEYS.OLD_VALUE: value[DIFFKEYS.OLD_VALUE],
                    DIFFKEYS.NEW_VALUE: value[DIFFKEYS.NEW_VALUE],
                },
            )
        if _is_cfn_leaf_construct(path_list):
            _add_item(
                schema_meta_diff,
                path_list[-1],
                DIFFKEYS.CHANGED,
                {
                    DIFFKEYS.PROPERTY: _get_path(path_list[:-1]),
                    DIFFKEYS.OLD_VALUE: value[DIFFKEYS.OLD_VALUE],
                    DIFFKEYS.NEW_VALUE: value[DIFFKEYS.NEW_VALUE],
                },
            )


def _translate_meta_diff(iterable: Iterable):
    """_summary_
    Args:
        iterable (Iterable): _description_
    Returns:
        _type_: _description_
    """
    diff_switcher = {
        METADIFF.ITERABLE_ITEM_ADDED: partial(
            _translate_iterable_change, DIFFKEYS.ADDED
        ),
        METADIFF.ITERABLE_ITEM_REMOVED: partial(
            _translate_iterable_change, DIFFKEYS.REMOVED
        ),
        METADIFF.VALUES_CHANGED: _translate_values_changed_diff_,
        METADIFF.TYPE_CHANGES: _translate_values_changed_diff_,
        METADIFF.DICTIONARY_ITEM_ADDED: partial(_translate_dict_change, DIFFKEYS.ADDED),
        METADIFF.DICTIONARY_ITEM_REMOVED: partial(
            _translate_dict_change, DIFFKEYS.REMOVED
        ),
    }
    schema_meta_diff = {}
    for diff_key, diff_value in iterable.items():
        diff_switcher.get(diff_key, lambda: "Invalid")(schema_meta_diff, diff_value)
    return schema_meta_diff
