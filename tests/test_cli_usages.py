from typer.testing import CliRunner

from enerbitdso.cli import cli

runner = CliRunner()

USAGES_ARGLIST = ["usages"]


def test_usages_with_frt_list():
    result = runner.invoke(cli, ["usages", "fetch", "frt00000", "frt00001", "frt00002"])
    assert result.exit_code == 0
