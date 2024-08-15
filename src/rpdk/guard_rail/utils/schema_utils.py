"""Module to handle schema manipulations."""
from copy import deepcopy
from typing import Any, Dict, List, Sequence, Set, Tuple

from jsonschema import RefResolver

_PROPERTIES = "properties"
_DEFINITIONS = "definitions"
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
    resolved_schema.pop(_DEFINITIONS, None)
    return resolved_schema


def _fetch_all_paths(schema: Dict):
    """Traversing resolved schema and fetching
    all properties paths.

    Example:
    {"properties": {"foo": {"properties": {"bar": {...}}}}}
    translated into -> ["/properties/foo", "/properties/foo/bar"]
    Args:
        schema (Dict): raw/resolved schema
    Returns:
        Sequence: list of traversed paths
    """

    def __traverse(
        prop_name: str, prop_definition: Dict, cur_path: Tuple[str], all_paths: Sequence
    ):
        # need to add parents/leafs
        all_paths.add(cur_path if cur_path[-1] != "*" else cur_path[:-1])
        definition_replica = deepcopy(prop_definition)

        if _ITEMS in definition_replica:
            __traverse(
                prop_name, definition_replica[_ITEMS], cur_path + ("*",), all_paths
            )
        else:
            # if combiners are specified then we need to squash variants
            # and iterate over each sub schema

            if _PROPERTIES in definition_replica:
                nested_properties = definition_replica[_PROPERTIES]
                while nested_properties:
                    _prop_name, _prop_definition = nested_properties.popitem()
                    __traverse(
                        _prop_name,
                        _prop_definition,
                        cur_path + (_prop_name,),
                        all_paths,
                    )

            if _ALL_OF in definition_replica:
                for sub_schema in definition_replica[_ALL_OF]:
                    __traverse(prop_name, sub_schema, cur_path, all_paths)
            elif _ANY_OF in definition_replica:
                for sub_schema in definition_replica[_ANY_OF]:
                    __traverse(prop_name, sub_schema, cur_path, all_paths)
            elif _ONE_OF in definition_replica:
                for sub_schema in definition_replica[_ONE_OF]:
                    __traverse(prop_name, sub_schema, cur_path, all_paths)
            else:
                pass

    resolved_schema = resolve_schema(schema)
    properties_replica = deepcopy(resolved_schema.get(_PROPERTIES, {}))
    traversed_paths = set()
    path = tuple()

    while properties_replica:
        property_name, property_definition = properties_replica.popitem()
        __traverse(
            property_name, property_definition, path + (property_name,), traversed_paths
        )
    return ["/properties/" + "/".join(i) for i in traversed_paths]


def add_paths_to_schema(schema: Dict):
    """Method to add all defined properties as paths

    Args:
        schema (Dict): resource schema

    Returns:
        Dict: schema with added paths
    """
    paths = _fetch_all_paths(schema)
    schema["paths"] = paths
    _add_tag_property(paths, schema)
    return schema


def _add_tag_property(paths: List[str], schema: Dict):
    for path in paths:
        property_name = path.split("/")[-1]
        if "Tag" in property_name:
            schema["TaggingPath"] = path
            return
