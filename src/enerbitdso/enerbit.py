import datetime as dt
import logging
import math
import ssl

import httpx
import pydantic
import truststore
import urlpath

logger = logging.getLogger(__name__)

SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

TIMEOUT = httpx.Timeout(5, read=60)

WATT_HOUR_TO_KILOWATT_HOUR = 0.001
MAX_REQUEST_RANGE = dt.timedelta(days=7)


class ScheduleUsageRecord(pydantic.BaseModel):
    frt_code: str
    meter_serial: str
    time_start: dt.datetime
    time_end: dt.datetime
    active_energy_imported: float
    active_energy_exported: float
    reactive_energy_imported: float
    reactive_energy_exported: float


class ScheduleMeasurementRecord(pydantic.BaseModel):
    frt_code: str
    meter_serial: str
    time_local_utc: dt.datetime
    voltage_multiplier: float
    current_multiplier: float
    active_energy_imported: float
    active_energy_exported: float
    reactive_energy_imported: float
    reactive_energy_exported: float


def get_auth_token(base_url, username, password):
    path = "/auth/token/"
    data = {"username": username, "password": password}
    with httpx.Client(base_url=base_url, timeout=TIMEOUT, verify=SSL_CONTEXT) as client:
        response = client.post(path, data=data)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to authenticate: {e}")
            logger.error(f"Response: {response.text}")
            raise
    token = response.json()["access_token"]
    return token


def get_client(base_url, username, password):
    url = str(urlpath.URL(base_url))
    token = get_auth_token(url, username, password)
    auth = {"Authorization": f"Bearer {token}"}
    return httpx.Client(base_url=url, headers=auth, timeout=TIMEOUT, verify=SSL_CONTEXT)


def scale_measurement_records(records: list[ScheduleMeasurementRecord], scale: float):
    for r in records:
        r.active_energy_imported = r.active_energy_imported * scale
        r.active_energy_exported = r.active_energy_exported * scale
        r.reactive_energy_imported = r.reactive_energy_imported * scale
        r.reactive_energy_exported = r.reactive_energy_exported * scale
    return records


def scale_usage_records(records: list[ScheduleUsageRecord], scale: float):
    for r in records:
        r.active_energy_imported = r.active_energy_imported * scale
        r.active_energy_exported = r.active_energy_exported * scale
        r.reactive_energy_imported = r.reactive_energy_imported * scale
        r.reactive_energy_exported = r.reactive_energy_exported * scale
    return records


def get_schedule_usage_records(
    client: httpx.Client, frt_code: str, since: dt.datetime, until: dt.datetime
) -> list[ScheduleUsageRecord]:
    path = "/measurements/schedules/usages"
    params = {
        "since": since,
        "until": until,
        "frt-code": frt_code,
        "period-string": "hour",
        "period-number": 1,
    }
    response = client.get(path, params=params)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch usage records: {e}")
        logger.error(f"Response: {response.text}")
        raise
    response.raise_for_status()
    records = response.json()
    records = sorted(records, key=lambda r: r["time_start"])
    usage_records = [ScheduleUsageRecord.model_validate(r) for r in records]
    usage_records = scale_usage_records(usage_records, scale=WATT_HOUR_TO_KILOWATT_HOUR)
    return usage_records


def get_schedule_measurement_records(
    client: httpx.Client, frt_code: str, since: dt.datetime, until: dt.datetime
) -> list[ScheduleMeasurementRecord]:
    path = "/measurements/schedules/"
    params = {
        "since": since,
        "until": until,
        "frt-code": frt_code,
    }
    response = client.get(path, params=params)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch measurement records: {e}")
        logger.error(f"Response: {response.text}")
        raise
    response.raise_for_status()
    records = response.json()
    records = sorted(records, key=lambda r: r["time_local_utc"])
    measurement_records = [ScheduleMeasurementRecord.model_validate(r) for r in records]
    measurement_records = scale_measurement_records(
        measurement_records, scale=WATT_HOUR_TO_KILOWATT_HOUR
    )
    return measurement_records


class DSOClient:
    def __init__(
        self, api_username: str, api_password: pydantic.SecretStr, api_base_url: str
    ) -> None:
        self.api_base_url = api_base_url
        self.api_username = api_username
        self.api_password = api_password

    def fetch_schedule_usage_records_large_interval(
        self, frt_code: str, since: dt.datetime, until: dt.datetime
    ) -> list[ScheduleUsageRecord]:
        ebclient = get_client(self.api_base_url, self.api_username, self.api_password)
        number_of_requests = math.ceil((until - since) / MAX_REQUEST_RANGE)
        logger.debug(f"Fetching usages in {number_of_requests} requests")
        usage_records = []
        for i in range(0, number_of_requests):
            fi = since + i * MAX_REQUEST_RANGE
            ff = min(fi + MAX_REQUEST_RANGE, until)
            this_usage_records = get_schedule_usage_records(
                ebclient, frt_code, since=fi, until=ff
            )
            usage_records.extend(this_usage_records)
        return usage_records

    def fetch_schedule_measurements_records_large_interval(
        self, frt_code: str, since: dt.datetime, until: dt.datetime
    ) -> list[ScheduleMeasurementRecord]:
        ebclient = get_client(self.api_base_url, self.api_username, self.api_password)
        number_of_requests = math.ceil((until - since) / MAX_REQUEST_RANGE)
        logger.debug(f"Fetching schedules in {number_of_requests} requests")
        schedule_records = []
        for i in range(0, number_of_requests):
            fi = since + i * MAX_REQUEST_RANGE
            ff = min(fi + MAX_REQUEST_RANGE, until)
            this_schedule_records = get_schedule_measurement_records(
                ebclient, frt_code, since=fi, until=ff
            )
            schedule_records.extend(this_schedule_records)
        return schedule_records
