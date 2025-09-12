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
    voltage_multiplier = 1
    current_multiplier = 1
    active_energy_imported = 0
    active_energy_exported = 0
    reactive_energy_imported = 0
    reactive_energy_exported = 0
    for index, item in enumerate(list_interval):
        active_energy_imported += round(random.randint(0, 100))
        active_energy_exported += round(random.randint(0, 100))
        reactive_energy_imported += round(random.randint(0, 100))
        reactive_energy_exported += round(random.randint(0, 100))
        mocked_schedules.append(
            ScheduleMeasurementRecord.model_validate(
                {
                    "frt_code": str(frt_code),
                    "meter_serial": str(meter_serial),
                    "time_local_utc": item["start"],
                    "voltage_multiplier": voltage_multiplier,
                    "current_multiplier": current_multiplier,
                    "active_energy_imported": active_energy_imported,
                    "active_energy_exported": active_energy_exported,
                    "reactive_energy_imported": reactive_energy_imported,
                    "reactive_energy_exported": reactive_energy_exported,
                }
            )
        )


def get_mocked_schedules(
    ebclient, frt_code=None, since=None, until=None, meter_serial=None
) -> list[ScheduleMeasurementRecord]:
    """Mock function that handles both frt_code and meter_serial parameters"""
    filtered_mocked_schedules = []
    
    for schedule in mocked_schedules:
        # Filter by time range
        if since and schedule.time_local_utc < since:
            continue
        if until and schedule.time_local_utc > until:
            continue
            
        # Filter by frt_code or meter_serial
        if frt_code and schedule.frt_code != frt_code:
            continue
        if meter_serial and schedule.meter_serial != meter_serial:
            continue
            
        filtered_mocked_schedules.append(schedule)
    
    return filtered_mocked_schedules


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


def get_mocked_usages(
    ebclient, frt_code=None, since=None, until=None, meter_serial=None
) -> list[ScheduleUsageRecord]:
    """Mock function that handles both frt_code and meter_serial parameters"""
    filtered_mocked_usages = []
    
    for usage in mocked_usages:
        # Filter by time range
        if since and usage.time_start < since:
            continue
        if until and usage.time_end > until:
            continue
            
        # Filter by frt_code or meter_serial
        if frt_code and usage.frt_code != frt_code:
            continue
        if meter_serial and usage.meter_serial != meter_serial:
            continue
            
        filtered_mocked_usages.append(usage)
    
    return filtered_mocked_usages
