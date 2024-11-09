import csv
import io
import typing

import orjson
import pydantic


def as_json(records: list[pydantic.BaseModel]) -> io.StringIO:
    content = orjson.dumps([r.model_dump() for r in records])
    res = io.BytesIO(content)

    return io.StringIO(res.getvalue().decode("utf-8"))


def as_csv(records: typing.Sequence[pydantic.BaseModel], header: bool) -> io.StringIO:
    res = io.StringIO(newline="")
    fields = records[0].model_fields.keys()
    writer = csv.DictWriter(res, fields, lineterminator="\n")
    if header:
        writer.writeheader()
    for i in records:
        writer.writerow(i.model_dump())
    return res


def as_jsonl(records: typing.Sequence[pydantic.BaseModel]) -> io.StringIO:
    res = io.StringIO()
    for i in records:
        res.write(i.model_dump_json())
        res.write("\n")
    return res
