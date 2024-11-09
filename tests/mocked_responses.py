import datetime as dt
import random
import string
from typing import List

import pandas as pd

from enerbitdso.enerbit import ScheduleMeasurementRecord, ScheduleUsageRecord

mocked_usages: List[ScheduleUsageRecord] = []
mocked_schedules: List[ScheduleMeasurementRecord] = []


def create_mocked_schedules(
    frt_code: str, since: dt.datetime, until: dt.datetime
) -> None:
    mocked_schedules.clear()
    dt_range: pd.core.indexes.datetimes.DatetimeIndex = (
        pd.core.indexes.datetimes.date_range(
            since,
            until,
            inclusive="both",
            freq="1H",
        )
    )
    intervals = pd.DataFrame({"start": dt_range})
    list_interval = intervals.to_dict(orient="records")
    letters = string.ascii_lowercase
    meter_serial = "".join(random.choice(letters) for i in range(10))
    active_energy_imported = 0
    active_energy_exported = 0
    reactive_energy_imported = 0
    reactive_energy_exported = 0
    for index, item in enumerate(list_interval):
        active_energy_imported += round(random.randint(0, 100))
        active_energy_exported += round(random.randint(0, 100))
        reactive_energy_imported += round(random.randint(0, 100))
        reactive_energy_exported += round(random.randint(0, 100))
        mocked_usages.append(
            ScheduleUsageRecord.model_validate(
                {
                    "frt_code": str(frt_code),
                    "meter_serial": str(meter_serial),
                    "time_local_utc": item["start"],
                    "voltage_multiplier": 1,
                    "current_multiplier": 1,
                    "active_energy_imported": active_energy_imported,
                    "active_energy_exported": active_energy_exported,
                    "reactive_energy_imported": reactive_energy_imported,
                    "reactive_energy_exported": reactive_energy_exported,
                }
            )
        )


def get_mocked_schedules(
    ebclient, frt_code, since, until
) -> list[ScheduleMeasurementRecord]:
    filtered_mocked_usages = [
        schedules
        for schedules in mocked_schedules
        if schedules.time_local_utc >= since
        and schedules.time_local_utc <= until
        and schedules.frt_code == frt_code
    ]
    return filtered_mocked_usages


def create_mocked_usages(frt_code: str, since: dt.datetime, until: dt.datetime) -> None:
    mocked_usages.clear()
    dt_range: pd.core.indexes.datetimes.DatetimeIndex = (
        pd.core.indexes.datetimes.date_range(
            since,
            until - dt.timedelta(hours=1),
            inclusive="both",
            freq="1h",
        )
    )
    intervals = pd.DataFrame({"start": dt_range})
    list_interval = intervals.to_dict(orient="records")
    letters = string.ascii_lowercase
    meter_serial = "".join(random.choice(letters) for i in range(10))
    for index, item in enumerate(list_interval):
        mocked_usages.append(
            ScheduleUsageRecord.model_validate(
                {
                    "frt_code": str(frt_code),
                    "meter_serial": str(meter_serial),
                    "time_start": item["start"],
                    "time_end": item["start"] + dt.timedelta(hours=1),
                    "active_energy_imported": round(random.uniform(0, 3), 2),
                    "active_energy_exported": round(random.uniform(0, 3), 2),
                    "reactive_energy_imported": round(random.uniform(0, 3), 2),
                    "reactive_energy_exported": round(random.uniform(0, 3), 2),
                }
            )
        )


def get_mocked_usages(ebclient, frt_code, since, until) -> list[ScheduleUsageRecord]:
    filtered_mocked_usages = [
        usages
        for usages in mocked_usages
        if usages.time_start >= since
        and usages.time_end <= until
        and usages.frt_code == frt_code
    ]
    return filtered_mocked_usages
