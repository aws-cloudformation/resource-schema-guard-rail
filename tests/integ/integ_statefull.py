"""
Integ test for statefull schema validation
"""
import pytest

from cli import main


@pytest.mark.parametrize(
    "args",
    [
        (
            [
                "--schema",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-schema.json",
                "--schema",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-schema.json",
                "--rule",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-rule.guard",
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
