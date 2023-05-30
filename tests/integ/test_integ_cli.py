"""
Integ test for stateless schema validation
"""
import os
from pathlib import Path

import pytest

from src.cli import main


@pytest.mark.parametrize(
    "args",
    [
        (
            [
                "--schema",
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                        "data/sample-schema.json"
                    )
                ),
                "--format",
            ]
        ),
        (
            [
                "--schema",
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                        "data/sample-schema.json"
                    )
                ),
                "--schema",
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                        "data/sample-schema.json"
                    )
                ),
            ]
        ),
    ],
)
def test_main_cli_stateless(args):
    """Main cli unit test"""
    main(args_in=args)


@pytest.mark.parametrize(
    "args",
    [
        (
            [
                "--schema",
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                        "data/sample-schema.json"
                    )
                ),
                "--schema",
                "file:/"
                + str(
                    Path(os.path.dirname(os.path.realpath(__file__))).joinpath(
                        "data/sample-schema.json"
                    )
                ),
                "--stateful",
            ]
        ),
    ],
)
def test_main_cli_stateful(
    args,
):
    """Main cli unit test"""
    try:
        main(args_in=args)
    except NotImplementedError as e:
        assert "Stateful evaluation is not supported yet" == str(e)
