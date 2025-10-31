import pytest
from batchtools.batchtools import BatchTools


def test_no_command():
    app = BatchTools()

    with pytest.raises(SystemExit) as err:
        app.run([])

    assert err.value.code == 2


def test_invalid_command():
    app = BatchTools()

    with pytest.raises(SystemExit) as err:
        app.run(["badcommand"])

    assert err.value.code == 2


def test_invalid_option():
    app = BatchTools()

    with pytest.raises(SystemExit) as err:
        app.run(["--bad-option"])

    assert err.value.code == 2


def test_global_help():
    app = BatchTools()

    with pytest.raises(SystemExit) as err:
        app.run(["--help"])

    assert err.value.code == 0


def test_command_invalid_option():
    app = BatchTools()

    for name in app.commands:
        with pytest.raises(SystemExit) as err:
            app.run([name, "--bad-option"])
        assert err.value.code == 2


def test_command_help():
    app = BatchTools()

    for name in app.commands:
        with pytest.raises(SystemExit) as err:
            app.run([name, "--help"])
        assert err.value.code == 0
