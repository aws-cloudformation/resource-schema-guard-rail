"""Module to perform statefull schema diff.
"""
import re
from enum import auto
from functools import partial
from typing import Any, Dict, Iterable

import strenum
from deepdiff import DeepDiff
from src.rpdk.guard_rail.utils.schema_utils import resolve_schema


class METADIFF(strenum.LowercaseStrEnum):
    ITERABLE_ITEM_ADDED = auto()
    ITERABLE_ITEM_REMOVED = auto()
    VALUES_CHANGED = auto()
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
native_constructs = {
    "type",
    "description",
    "enum",
    "maximum",
    "minimum",
    "maxLength",
    "minLength",
    "pattern",
    "maxItems",
    "minItems",
    "contains",
    "items",
    "additionalProperties",
}


def schema_diff(previous_json: Dict[str, Any], current_json: Dict[str, Any]):
    """schema diff function to get formatted schema diff from deep diff"""
    deep_diff = DeepDiff(
        resolve_schema(previous_json),
        resolve_schema(current_json),
        ignore_order=True,
        verbose_level=2,
    )
    return _translate_meta_diff(deep_diff.to_dict())


def is_property(path_list):
    """

    Args:
        path_list:

    Returns:

    """
    return (
        ((path_list[0] == PROPERTIES) and (path_list[-1] not in native_constructs))
        if len(path_list) > 0
        else False
    )


def is_cfn_construct(path_list):
    """

    Args:
        path_list:

    Returns:

    """
    return path_list[0] in cfn_list_constructs if len(path_list) > 0 else False


def is_native_construct(path_list):
    """

    Args:
        path_list:

    Returns:

    """
    return path_list[-1] in native_constructs if len(path_list) > 0 else False


def _get_path(path_list):
    """

    Args:
        path_list:

    Returns:

    """
    return "/".join([""] + path_list)


def _cast_path(value: str):
    """cast the path of the change to process constructs"""
    pattern = r"(?<=\[)'?([\s\S]+?)'?(?=\])"
    value = value.replace("items']['properties", "*")
    value = re.sub(r"[0-9]+]", "", value)
    result = re.findall(pattern, value)
    return result


def _add_item(constructs_diff, result_key, change_key, result_value):
    """_summary_
    Args:
        constructs_diff (_type_): _description_
        result_key (_type_): _description_
        change_key (_type_): _description_
        result_value (_type_): _description_
    """
    if result_key not in constructs_diff:
        constructs_diff[result_key] = {}
    if change_key in constructs_diff[result_key]:
        constructs_diff[result_key][change_key].append(result_value)
    else:
        constructs_diff[result_key][change_key] = [result_value]


def _process_nested_properties(constructs_diff, result_key, prefix, diff_value):
    if "items" in diff_value and PROPERTIES in diff_value["items"]:
        for nested_property in diff_value["items"]["properties"]:
            _add_item(
                constructs_diff,
                PROPERTIES,
                result_key,
                prefix + "/*/" + nested_property,
            )
            _process_nested_properties(
                constructs_diff,
                result_key,
                prefix + "/*/" + nested_property,
                diff_value["items"]["properties"][nested_property],
            )


def _translate_iterable_change(
    changed: DIFFKEYS, constructs_diff: Dict[str, Any], diff_value: Any
):
    """_summary_
    Args:
        constructs_diff (Dict[str, Any]): _description_
        diff_value (Any): _description_
        changed (DIFFKEYS): _description_
    """

    def __translate_iter_added_diff(constructs_diff, diff_value):
        for key, value in diff_value.items():
            path_list = _cast_path(key)
            if is_cfn_construct(path_list):
                _add_item(constructs_diff, path_list[0], DIFFKEYS.ADDED, value)

    def __translate_iter_removed_diff(constructs_diff, diff_value):
        for key, value in diff_value.items():
            path_list = _cast_path(key)
            if is_cfn_construct(path_list):
                _add_item(constructs_diff, path_list[0], DIFFKEYS.REMOVED, value)

    if changed == DIFFKEYS.ADDED:
        __translate_iter_added_diff(constructs_diff, diff_value)
        return
    if changed == DIFFKEYS.REMOVED:
        __translate_iter_removed_diff(constructs_diff, diff_value)
        return

    raise NotImplementedError("Invalid")


def _translate_dict_change(
    changed: DIFFKEYS, constructs_diff: Dict[str, Any], diff_value: Any
):
    """_summary_
    Args:
        constructs_diff (Dict[str, Any]): _description_
        diff_value (Any): _description_
        changed (DIFFKEYS): _description_
    """

    def __translate_dict_added_diff(constructs_diff, diff_value):
        for key, value in diff_value.items():
            path_list = _cast_path(key)
            if is_property(path_list):
                _add_item(
                    constructs_diff, PROPERTIES, DIFFKEYS.ADDED, _get_path(path_list)
                )
                if isinstance(value, dict):
                    _process_nested_properties(
                        constructs_diff, DIFFKEYS.ADDED, _get_path(path_list), value
                    )
            if is_native_construct(path_list):
                _add_item(
                    constructs_diff,
                    path_list[-1],
                    DIFFKEYS.ADDED,
                    _get_path(path_list[:-1]),
                )

    def __translate_dict_removed_diff(constructs_diff, diff_value):
        for key, value in diff_value.items():
            path_list = _cast_path(key)
            if is_property(path_list):
                _add_item(
                    constructs_diff, PROPERTIES, DIFFKEYS.REMOVED, _get_path(path_list)
                )
                if isinstance(value, dict):
                    _process_nested_properties(
                        constructs_diff, DIFFKEYS.REMOVED, _get_path(path_list), value
                    )
            if is_native_construct(path_list):
                _add_item(
                    constructs_diff,
                    path_list[-1],
                    DIFFKEYS.REMOVED,
                    _get_path(path_list[:-1]),
                )

    if changed == DIFFKEYS.ADDED:
        __translate_dict_added_diff(constructs_diff, diff_value)
        return
    if changed == DIFFKEYS.REMOVED:
        __translate_dict_removed_diff(constructs_diff, diff_value)
        return

    raise NotImplementedError("Invalid")


def _translate_values_changed_diff_(constructs_diff, diff_value):
    """_summary_
    Args:
        constructs_diff (_type_): _description_
        diff_value (_type_): _description_
    """
    for key, value in diff_value.items():
        path_list = _cast_path(key)
        if is_cfn_construct(path_list):
            _add_item(
                constructs_diff,
                path_list[0],
                DIFFKEYS.REMOVED,
                value[DIFFKEYS.OLD_VALUE],
            )
            _add_item(
                constructs_diff, path_list[0], DIFFKEYS.ADDED, value[DIFFKEYS.NEW_VALUE]
            )
        if is_native_construct(path_list):
            _add_item(
                constructs_diff,
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
    print(iterable)
    diff_switcher = {
        METADIFF.ITERABLE_ITEM_ADDED: partial(
            _translate_iterable_change, DIFFKEYS.ADDED
        ),
        METADIFF.ITERABLE_ITEM_REMOVED: partial(
            _translate_iterable_change, DIFFKEYS.REMOVED
        ),
        METADIFF.VALUES_CHANGED: _translate_values_changed_diff_,
        METADIFF.DICTIONARY_ITEM_ADDED: partial(_translate_dict_change, DIFFKEYS.ADDED),
        METADIFF.DICTIONARY_ITEM_REMOVED: partial(
            _translate_dict_change, DIFFKEYS.REMOVED
        ),
    }
    constructs_diff = {}
    for diff_key, diff_value in iterable.items():
        diff_switcher.get(diff_key, lambda: "Invalid")(constructs_diff, diff_value)
    return constructs_diff
