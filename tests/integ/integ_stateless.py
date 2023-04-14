"""
Integ test for stateless schema validation
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
                "--rule",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-rule.guard",
                "--format",
            ]
        ),
        (
            [
                "--schema",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-schema.json",
                "--schema",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-schema.json",
                "--rule",
                "file://Users/sgathili/workplace/guard_rail/resource-schema-guard-rail/tests/integ/data/sample-rule.guard",
            ]
        ),
    ],
)
def test_main_cli(
    args,
):
    """Main cli unit test"""
    main(args_in=args)
    assert True
