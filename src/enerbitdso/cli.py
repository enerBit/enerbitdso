import datetime as dt
import enum
import logging
import operator
import pathlib
import sys
from typing import Annotated, TypedDict

import pydantic
import typer
import zoneinfo
from rich.console import Console

from enerbitdso import enerbit, formats

err_console = Console(stderr=True)
out_console = Console()

logger = logging.getLogger(__name__)

DATE_FORMATS = ["%Y-%m-%d", "%Y%m%d"]


class DateParts(TypedDict, total=False):
    hour: int
    minute: int
    second: int
    microsecond: int


DATE_PARTS_TO_START_DAY: DateParts = {
    "hour": 0,
    "minute": 0,
    "second": 0,
    "microsecond": 0,
}

TZ_INFO = zoneinfo.ZoneInfo("America/Bogota")


cli = typer.Typer(pretty_exceptions_show_locals=False, no_args_is_help=True)
usages = typer.Typer()
cli.add_typer(usages, name="usages", no_args_is_help=True)


class OutputFormat(str, enum.Enum):
    jsonl = "jsonl"
    csv = "csv"


def yesterday():
    return None


def today():
    return None


@usages.command()
def fetch(
    api_base_url: Annotated[str, typer.Option(..., envvar="ENERBIT_API_BASE_URL")],
    api_username: Annotated[str, typer.Option(..., envvar="ENERBIT_API_USERNAME")],
    api_password: Annotated[
        pydantic.SecretStr,
        typer.Option(parser=pydantic.SecretStr, envvar="ENERBIT_API_PASSWORD"),
    ],
    since: dt.datetime = typer.Option(
        yesterday,
        formats=DATE_FORMATS,
        show_default="yesterday",
    ),
    until: dt.datetime = typer.Option(
        today,
        formats=DATE_FORMATS,
        show_default="today",
    ),
    out_format: OutputFormat = typer.Option(
        "jsonl", help="Output file format", case_sensitive=False
    ),
    frt_file: pathlib.Path = typer.Option(
        None, help="Path file with one frt code per line"
    ),
    frts: list[str] = typer.Argument(None, help="List of frt codes separated by ' '"),
):
    try:
        ebconnector = enerbit.DSOClient(
            api_base_url=api_base_url,
            api_username=api_username,
            api_password=api_password.get_secret_value(),
        )
    except Exception:
        err_console.print(
            f"Failed to authenticate to '{api_base_url}' as '{api_username}'"
        )
        raise typer.Exit(code=1)

    today = dt.datetime.now(TZ_INFO).replace(**DATE_PARTS_TO_START_DAY)
    if since is None:
        since = today - dt.timedelta(days=1)
    else:
        since = since.astimezone(TZ_INFO)
    if until is None:
        until = today
    else:
        until = until.astimezone(TZ_INFO)

    if frts is None:
        frts = []

    if not operator.xor(frt_file is not None, len(frts) != 0):
        err_console.print("Can't use '--FRT_FILE' and 'FRTS' on the same call")
        raise typer.Exit(code=1)

    if frt_file is not None:
        with open(frt_file, "r") as frts_src:
            frts = frts_src.read().splitlines()

    err_console.print(
        f"Fetching usages for {len(frts)} frts since={since} until={until}"
    )

    header = True
    for i, f in enumerate(frts):
        try:
            usage_records = ebconnector.fetch_schedule_usage_records_large_interval(
                f, since=since, until=until
            )
        except Exception:
            err_console.print(f"Failed to fetch usage records for frt code '{f}'")
            err_console.print_exception()
            continue

        match out_format:
            case OutputFormat.csv:
                content = formats.as_csv(usage_records, header=header)
                header = False
            case OutputFormat.jsonl:
                content = formats.as_jsonl(usage_records)

        content.seek(0)
        for s in content:
            sys.stdout.write(s)


if __name__ == "__main__":
    cli()
