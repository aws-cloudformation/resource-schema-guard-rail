"""Module to handle schema manipulations."""
from typing import Any, Dict, Set

from jsonschema import RefResolver

_PROPERTIES = "properties"
_REF = "$ref"
_ITEMS = "items"
_PATTERN_PROPERTIES = "patternProperties"
_ANY_OF = "anyOf"
_ONE_OF = "oneOf"
_ALL_OF = "allOf"


def resolve_schema(schema: Dict):
    """Resolving schema into a nested object.
    Json schema allows recursive and chained
    $refs, which is hard to analyze and get diff
    between two schemas. This method resolves refs;
    Args:
        schema (Dict): _description_
    Returns:
        _type_: _description_
    """
    resolver = RefResolver.from_schema(schema)

    def _internal_resolver(schema: Dict, resolver: Any, resolved_refs: Set):
        if _PROPERTIES in schema:
            for key, val in schema[_PROPERTIES].items():
                schema[_PROPERTIES][key] = _internal_resolver(
                    val, resolver, resolved_refs
                )
        if _REF in schema:
            reference_path = schema.pop(_REF, None)
            if reference_path in resolved_refs:
                return schema
            resolved = resolver.resolve(reference_path)[1]
            schema.update(resolved)
            return _internal_resolver(
                schema, resolver, resolved_refs | {reference_path}
            )
        if _PATTERN_PROPERTIES in schema:
            for key, val in schema[_PATTERN_PROPERTIES].items():
                schema[_PATTERN_PROPERTIES][key] = _internal_resolver(
                    val, resolver, resolved_refs
                )
        if _ITEMS in schema:
            schema[_ITEMS] = _internal_resolver(schema[_ITEMS], resolver, resolved_refs)
        if _ALL_OF in schema:
            for index, element in enumerate(schema[_ALL_OF]):
                schema[_ALL_OF][index] = _internal_resolver(
                    element, resolver, resolved_refs
                )
        if _ANY_OF in schema:
            for index, element in enumerate(schema[_ANY_OF]):
                schema[_ANY_OF][index] = _internal_resolver(
                    element, resolver, resolved_refs
                )
        if _ONE_OF in schema:
            for index, element in enumerate(schema[_ONE_OF]):
                schema[_ONE_OF][index] = _internal_resolver(
                    element, resolver, resolved_refs
                )
        return schema

    resolved_schema = _internal_resolver(schema, resolver, set())
    resolved_schema.pop("definitions", None)
    return resolved_schema
