"""
Integ test for stateless schema validation
"""
import os
from pathlib import Path

import pytest

from cli import main


@pytest.mark.parametrize(
    "args,failed_rules",
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
            ],
            [
                "ENSURE_PROPERTIES_DO_NOT_SUPPORT_MULTITYPE:\n"
                "    check-id: COM_2\n"
                "    message: type MUST NOT have combined definition\n",
                "ENSURE_PRIMARY_IDENTIFIER_IS_READ_OR_CREATE_ONLY:\n"
                "    check-id: unidentified\n"
                "    message: unidentified\n"
                "    check-id: unidentified\n"
                "    message: unidentified\n"
                "    check-id: unidentified\n"
                "    message: unidentified\n",
                "ENSURE_ARN_PROPERTIES_CONTAIN_PATTERN:\n"
                "    check-id: ARN_2\n"
                "    message: arn related property MUST have pattern specified\n",
            ],
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
            ],
            [],
        ),
    ],
)
def test_main_cli(capsys, args, failed_rules):
    """Main cli unit test"""
    main(args_in=args)
    captured = capsys.readouterr()
    for rule in failed_rules:
        assert rule in captured.out
