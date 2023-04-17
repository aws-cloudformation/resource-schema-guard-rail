"""
Integ test for statefull schema validation
"""
import os
from pathlib import Path

import pytest

from cli import main


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
                "--statefull",
            ]
        ),
    ],
)
def test_main_cli(
    args,
):
    """Main cli unit test"""
    try:
        main(args_in=args)
    except NotImplementedError as e:
        assert "Statefull evaluation is not supported yet" == str(e)
