"""Module to perform statefull schema diff.
"""
import re
from typing import Any, Dict, Iterable

from deepdiff import DeepDiff

ITERABLE_ITEM_ADDED = "iterable_item_added"
ITERABLE_ITEM_REMOVED = "iterable_item_removed"
VALUES_CHANGED = "values_changed"
DICT_ITEM_ADDED = "dictionary_item_added"
DICT_ITEM_REMOVED = "dictionary_item_removed"
ADDED = "added"
REMOVED = "removed"
CHANGED = "changed"
OLD_VALUE = "old_value"
NEW_VALUE = "new_value"
ADDITIONAL_IDS = "additionalIdentifiers"
PROPERTIES = "properties"
cfn_list_constructs = {
    "primaryIdentifier",
    "readOnlyProperties",
    "writeOnlyProperties",
    "createOnlyProperties",
}
native_constructs = {
    "type",
    "enum",
    "maximum",
    "minimum",
    "maxLength",
    "minLength",
    "pattern",
    "maxItems",
    "minItems",
    "contains",
}


def schema_diff(previous_json: Dict[str, Any], current_json: Dict[str, Any]):
    """schema diff function to get formatted schema diff from deep diff"""
    deep_diff = DeepDiff(previous_json, current_json, ignore_order=True)
    return _format_schema_diff_(deep_diff.to_dict())


def _cast_path_(value: str):
    """cast the path of the change to process constructs"""
    pattern = r"(?<=\[)'?([\s\S]+?)'?(?=\])"
    result = re.findall(pattern, value)
    is_additional_property = result[0] == ADDITIONAL_IDS
    is_property = result[0] == PROPERTIES
    is_cfn_construct = result[0] in cfn_list_constructs
    is_native_construct = result[-1] in native_constructs
    is_array = re.match(r"[0-9]+", result[-1])
    return (
        result,
        is_cfn_construct,
        is_native_construct,
        is_array,
        is_property,
        is_additional_property,
    )


def _get_path_(path_list):
    return "/".join(path_list)


def _process_iter_added_diff_(constructs_diff, diff_value):
    for key, value in diff_value.items():
        (
            result,
            is_cfn_construct,
            is_native_construct,
            is_array,
            is_property,
            is_additional_property,
        ) = _cast_path_(key)
        if is_cfn_construct:
            _add_item_(constructs_diff, result[0], ADDED, value)


def _process_iter_removed_diff_(constructs_diff, diff_value):
    for key, value in diff_value.items():
        (
            result,
            is_cfn_construct,
            is_native_construct,
            is_array,
            is_property,
            is_additional_property,
        ) = _cast_path_(key)
        if is_cfn_construct:
            _add_item_(constructs_diff, result[0], REMOVED, value)


def _process_values_changed_diff_(constructs_diff, diff_value):
    for key, value in diff_value.items():
        (
            result,
            is_cfn_construct,
            is_native_construct,
            is_array,
            is_property,
            is_additional_property,
        ) = _cast_path_(key)
        if is_cfn_construct:
            _add_item_(constructs_diff, result[0], REMOVED, value[OLD_VALUE])
            _add_item_(constructs_diff, result[0], ADDED, value[NEW_VALUE])
        if is_native_construct:
            _add_item_(
                constructs_diff,
                result[-1],
                CHANGED,
                {
                    "property": _get_path_(result[:-1]),
                    OLD_VALUE: value[OLD_VALUE],
                    NEW_VALUE: value[NEW_VALUE],
                },
            )


def _process_dict_added_diff_(constructs_diff, diff_value):
    for key in diff_value:
        (
            result,
            is_cfn_construct,
            is_native_construct,
            is_array,
            is_property,
            is_additional_property,
        ) = _cast_path_(key)
        if is_property:
            _add_item_(constructs_diff, PROPERTIES, ADDED, _get_path_(result))
        if is_native_construct:
            _add_item_(constructs_diff, result[-1], ADDED, _get_path_(result[:-1]))


def _process_dict_removed_diff_(constructs_diff, diff_value):
    for key in diff_value:
        (
            result,
            is_cfn_construct,
            is_native_construct,
            is_array,
            is_property,
            is_additional_property,
        ) = _cast_path_(key)
        if is_property:
            _add_item_(constructs_diff, PROPERTIES, REMOVED, _get_path_(result))
        if is_native_construct:
            _add_item_(constructs_diff, result[-1], REMOVED, _get_path_(result[:-1]))


def _add_item_(constructs_diff, result_key, change_key, result_value):
    if result_key not in constructs_diff:
        constructs_diff[result_key] = {}
    if change_key in constructs_diff[result_key]:
        constructs_diff[result_key][change_key].append(result_value)
    else:
        constructs_diff[result_key][change_key] = [result_value]


def _format_schema_diff_(iterable: Iterable):
    """schema diff function to get formatted schema diff"""
    print(iterable)
    diff_switcher = {
        ITERABLE_ITEM_ADDED: _process_iter_added_diff_,
        ITERABLE_ITEM_REMOVED: _process_iter_removed_diff_,
        VALUES_CHANGED: _process_values_changed_diff_,
        DICT_ITEM_ADDED: _process_dict_added_diff_,
        DICT_ITEM_REMOVED: _process_dict_removed_diff_,
    }
    constructs_diff = {}
    for diff_key, diff_value in iterable.items():
        diff_switcher.get(diff_key, lambda: "Invalid")(constructs_diff, diff_value)
    print(constructs_diff)
    return constructs_diff
