"""Module with common variable and methods."""
import json
import re

from .logger import LOG, logdebug

FILE_PATTERN = re.compile(r"^(file:\/\/)")


GUARD_EXTENSION = re.compile(r"[\s\S]+(.guard)")
SCHEMA_FILE_PATTERN = re.compile(r"^(.+)\/([^\/]+)(\.json)$")
GUARD_FILE_PATTERN = re.compile(r"^(.+)\/([^\/]+)(\.guard)$")


JSON_PATH_EXTRACT_PATTERN = r"(^file:/)((.+)(\.json))$"
GUARD_PATH_EXTRACT_PATTERN = r"(^file:/)((.+)(\.guard))$"


@logdebug
def is_guard_rule(file_input: str) -> bool:  # pylint: disable=C0116
    return bool(re.search(GUARD_EXTENSION, file_input))


@logdebug
def read_file(file_path: str):  # pylint: disable=C0116
    try:
        with open(file_path, "r", encoding="utf8") as file:
            return file.read()
    except IOError as ex:
        LOG.info("File not found. Please check the path.")
        raise ex


@logdebug
def read_json(file_path: str):  # pylint: disable=C0116
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except IOError as ex:
        LOG.info("File not found. Please check the path.")
        raise ex
