"""Module to perform statefull schema diff.
"""
# import re
# from typing import Any, Collection, Dict, Iterable
#
# from deepdiff import DeepDiff
#
#
# def json_diff(previous_json: Dict[str, Any], current_json: Dict[str, Any]):
#     deep_diff = DeepDiff(previous_json, current_json, ignore_order=True)
#     return _format_json_diff_(deep_diff.to_dict())
#
#
# def _cast_root_to_path_(value: str):
#     pattern = r"(?<=\[)([\s\S]+?)(?=\])"
#     result = re.findall(pattern, value)
#     return "/".join(
#         [""] + [item[1:-1] if item[0] == item[-1] == "'" else item for item in result]
#     )
#
#
# def _format_json_diff_(iterable: Iterable, regex: str = r"root\["):
#     if isinstance(iterable, dict):
#         for key in list(iterable.keys()):
#             new_key = key
#             if re.match(regex, key):
#                 new_key = _cast_root_to_path_(key)
#             iterable[new_key] = _format_json_diff_(iterable.pop(key), regex)
#     elif isinstance(iterable, Collection) and not isinstance(iterable, str):
#         return [
#             _cast_root_to_path_(item) if re.match(regex, item) else item
#             for item in iterable
#         ]
#     else:
#         return iterable
