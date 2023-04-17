"""
Unit test for cli.py
"""
import os
from pathlib import Path

import pytest

from src.rpdk.guard_rail.utils.common import is_guard_rule, read_file


@pytest.mark.parametrize(
    "rule,result",
    [("file:/data/sample.guard", True), ("file:/data/sample.json", False)],
)
def test_is_guard_rule(rule, result):
    """Unit test to verify guard rule extension check"""
    assert result == is_guard_rule(rule)


@pytest.mark.parametrize(
    "file",
    [("data/sample.guard"), ("data/sample_not_found.guard")],
)
def test_read_file(file):
    """Unit test to read files"""
    try:
        file_obj = read_file(
            str(Path(os.path.dirname(os.path.realpath(__file__))).joinpath(file))
        )
        assert file_obj is not None
    except IOError as e:
        assert "No such file or directory: " in str(e)
