from typer.testing import CliRunner

from enerbitdso.cli import cli

runner = CliRunner()

USAGES_ARGLIST = ["usages"]


def _test_usages_with_frt_list():  # TODO: Fix this test
    command = USAGES_ARGLIST + ["fetch", "frt00000", "frt00001", "frt00002"]
    result = runner.invoke(cli, command)
    assert result.exit_code == 0
