"""
Unit tests for arg_handler.py read-only functionality
"""

from rpdk.guard_rail.utils.arg_handler import setup_args


def test_setup_args_includes_read_only_flag():
    """Test that setup_args includes the --is-read-only flag"""
    parser = setup_args()
    # Parse with the new flag
    args = parser.parse_args(["--schema", "file://test.json", "--is-read-only"])
    assert args.is_read_only is True
    assert args.schemas == ["file://test.json"]


def test_setup_args_default_read_only_flag():
    """Test that --is-read-only defaults to False"""
    parser = setup_args()
    # Parse without the flag
    args = parser.parse_args(["--schema", "file://test.json"])
    assert args.is_read_only is False
    assert args.schemas == ["file://test.json"]


def test_setup_args_read_only_with_stateful():
    """Test --is-read-only flag works with --stateful"""
    parser = setup_args()
    args = parser.parse_args(
        [
            "--schema",
            "file://test1.json",
            "--schema",
            "file://test2.json",
            "--stateful",
            "--is-read-only",
        ]
    )
    assert args.is_read_only is True
    assert args.stateful is True
    assert len(args.schemas) == 2
