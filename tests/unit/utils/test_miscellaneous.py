"""
Unit test for cli.py
"""
from importlib.util import find_spec
from pathlib import Path
from unittest import mock

from jinja2 import FileSystemLoader, PackageLoader

from rpdk.guard_rail.utils.miscellaneous import jinja_loader


@mock.patch("rpdk.guard_rail.utils.miscellaneous.find_spec")
def test_jinja_loader_none_spec(mock_find_spec):
    """Test jinja loader"""
    mock_find_spec.return_value = None
    env = jinja_loader("src.rpdk.guard_rail.core")
    assert (
        env.loader.loaders[0].package_path
        == PackageLoader("src.rpdk.guard_rail.core").package_path
    )


@mock.patch("rpdk.guard_rail.utils.miscellaneous.FileSystemLoader")
def test_jinja_loader(mock_file_systeam_loader):
    """Test jinja loader"""
    spec_path = Path(find_spec(__name__).origin).resolve(strict=True)
    mock_file_systeam_loader.return_value = FileSystemLoader(
        str(spec_path.parent / "templates")
    )
    env = jinja_loader("src.rpdk.guard_rail.core")
    assert (
        env.loader.loaders[0].searchpath
        == FileSystemLoader(str(spec_path.parent / "templates")).searchpath
    )
