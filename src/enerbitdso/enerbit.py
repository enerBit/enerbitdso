import datetime as dt
import logging
import math
import ssl
import urllib
import urllib.parse
import base64
import json
from typing import Optional

import httpx
import pydantic
import truststore

logger = logging.getLogger(__name__)

SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

TIMEOUT = httpx.Timeout(5, read=60)

WATT_HOUR_TO_KILOWATT_HOUR = 0.001
MAX_REQUEST_RANGE = dt.timedelta(days=7)


class InvalidParameterError(ValueError):
    """Error cuando los parámetros de consulta son inválidos"""
    pass


def _validate_query_parameters(frt_code: Optional[str], meter_serial: Optional[str]) -> None:
    """Valida que exactamente uno de frt_code o meter_serial esté presente.
    
    Args:
        frt_code: Código de frontera (opcional)
        meter_serial: Número de serie del medidor (opcional)
        
    Raises:
        InvalidParameterError: Si ambos parámetros están presentes o si ambos están ausentes
    """
    has_frt = frt_code is not None and frt_code.strip() != ""
    has_meter = meter_serial is not None and meter_serial.strip() != ""
    
    if has_frt and has_meter:
        raise InvalidParameterError(
            "No se pueden especificar tanto 'frt_code' como 'meter_serial' al mismo tiempo. "
            "Debe proporcionar exactamente uno de los dos parámetros."
        )
    
    if not has_frt and not has_meter:
        raise InvalidParameterError(
            "Debe especificar al menos uno de 'frt_code' o 'meter_serial'. "
            "No se pueden omitir ambos parámetros."
        )


def _decode_jwt_payload(token: str) -> dict:
    """Decodifica el payload de un JWT sin verificar la firma"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        return {}


def _get_token_expiration(token: str) -> Optional[dt.datetime]:
    """Extrae la fecha de expiración de un JWT"""
    payload = _decode_jwt_payload(token)
    if 'exp' in payload:
        return dt.datetime.fromtimestamp(payload['exp'])
    return None


class ScheduleUsageRecord(pydantic.BaseModel):
    frt_code: str
    meter_serial: str
    time_start: dt.datetime
    time_end: dt.datetime
    active_energy_imported: Optional[float] = None
    active_energy_exported: Optional[float] = None
    reactive_energy_imported: Optional[float] = None
    reactive_energy_exported: Optional[float] = None


class ScheduleMeasurementRecord(pydantic.BaseModel):
    frt_code: str
    meter_serial: str
    time_local_utc: dt.datetime
    voltage_multiplier: Optional[float] = None
    current_multiplier: Optional[float] = None
    active_energy_imported: Optional[float] = None
    active_energy_exported: Optional[float] = None
    reactive_energy_imported: Optional[float] = None
    reactive_energy_exported: Optional[float] = None


def get_auth_token(base_url: str, username: str, password: pydantic.SecretStr) -> dict:
    """Obtiene tokens de autenticación (access y refresh)"""
    path = "/auth/token/"
    data = {"username": username, "password": password.get_secret_value()}
    with httpx.Client(base_url=base_url, timeout=TIMEOUT, verify=SSL_CONTEXT) as client:
        response = client.post(path, data=data)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to authenticate: {e}")
            logger.error(f"Response: {response.text}")
            raise
    
    token_data = response.json()
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type", "bearer")
    }


def get_client(
    base_url: str, username: str, password: pydantic.SecretStr
) -> httpx.Client:
    url_parse: urllib.parse.ParseResult = urllib.parse.urlparse(base_url)
    url = url_parse.geturl()
    token_data = get_auth_token(url, username, password)
    auth = {"Authorization": f"Bearer {token_data['access_token']}"}
    return httpx.Client(base_url=url, headers=auth, timeout=TIMEOUT, verify=SSL_CONTEXT)


def scale_measurement_records(records: list[ScheduleMeasurementRecord], scale: float):
    for r in records:
        r.active_energy_imported = (
            r.active_energy_imported * scale
            if r.active_energy_imported is not None
            else None
        )
        r.active_energy_exported = (
            r.active_energy_exported * scale
            if r.active_energy_exported is not None
            else None
        )
        r.reactive_energy_imported = (
            r.reactive_energy_imported * scale
            if r.reactive_energy_imported is not None
            else None
        )
        r.reactive_energy_exported = (
            r.reactive_energy_exported * scale
            if r.reactive_energy_exported is not None
            else None
        )
    return records


def scale_usage_records(records: list[ScheduleUsageRecord], scale: float):
    for r in records:
        r.active_energy_imported = (
            r.active_energy_imported * scale
            if r.active_energy_imported is not None
            else None
        )
        r.active_energy_exported = (
            r.active_energy_exported * scale
            if r.active_energy_exported is not None
            else None
        )
        r.reactive_energy_imported = (
            r.reactive_energy_imported * scale
            if r.reactive_energy_imported is not None
            else None
        )
        r.reactive_energy_exported = (
            r.reactive_energy_exported * scale
            if r.reactive_energy_exported is not None
            else None
        )
    return records


def get_schedule_usage_records(
    client: httpx.Client, since: dt.datetime, until: dt.datetime, meter_serial: Optional[str] = None, frt_code: Optional[str] = None
) -> list[ScheduleUsageRecord]:
    _validate_query_parameters(frt_code, meter_serial)
    
    path = "/measurements/schedules/usages"
    params = {
        "since": since.isoformat(),
        "until": until.isoformat(),
        "period-string": "hour",
        "period-number": "1",
    }
    
    if frt_code and frt_code.strip():
        params["frt-code"] = frt_code
    if meter_serial and meter_serial.strip():
        params["meter-serial"] = meter_serial
    
    response = client.get(
        path,
        params=params,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch usage records: {e}")
        logger.error(f"Response: {response.text}")
        raise
    records = response.json()
    records = sorted(records, key=lambda r: r["time_start"])
    usage_records = [ScheduleUsageRecord.model_validate(r) for r in records]
    usage_records = scale_usage_records(usage_records, scale=WATT_HOUR_TO_KILOWATT_HOUR)
    return usage_records


def get_schedule_measurement_records(
    client: httpx.Client, since: dt.datetime, until: dt.datetime, meter_serial: Optional[str] = None, frt_code: Optional[str] = None
) -> list[ScheduleMeasurementRecord]:
    _validate_query_parameters(frt_code, meter_serial)
    
    path = "/measurements/schedules/"
    params = {
        "since": since.isoformat(),
        "until": until.isoformat(),
    }
    
    if frt_code and frt_code.strip():
        params["frt-code"] = frt_code
    if meter_serial and meter_serial.strip():
        params["meter-serial"] = meter_serial
    
    response = client.get(path, params=params)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch measurement records: {e}")
        logger.error(f"Response: {response.text}")
        raise
    records = response.json()
    records = sorted(records, key=lambda r: r["time_local_utc"])
    measurement_records = [ScheduleMeasurementRecord.model_validate(r) for r in records]
    measurement_records = scale_measurement_records(
        measurement_records, scale=WATT_HOUR_TO_KILOWATT_HOUR
    )
    return measurement_records


class DSOClient:
    def __init__(self, api_username: str, api_password: str, api_base_url: str) -> None:
        self.api_base_url = api_base_url
        self.api_username = api_username
        self.api_password = pydantic.SecretStr(api_password)
        self._client: Optional[httpx.Client] = None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[dt.datetime] = None

    def _is_token_valid(self) -> bool:
        """Verifica si el token actual es válido y no ha expirado"""
        if self._access_token is None:
            return False
        if self._token_expires_at is None:
            return True
        buffer = dt.timedelta(seconds=30)
        return dt.datetime.now() < (self._token_expires_at - buffer)

    def _refresh_access_token(self) -> bool:
        """Intenta refrescar el access token usando el refresh token"""
        if not self._refresh_token:
            return False
            
        path = "/auth/refresh/"
        data = {"refresh_token": self._refresh_token}
        
        try:
            with httpx.Client(base_url=self.api_base_url, timeout=TIMEOUT, verify=SSL_CONTEXT) as client:
                response = client.post(path, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                self._access_token = token_data["access_token"]
                
                if "refresh_token" in token_data:
                    self._refresh_token = token_data["refresh_token"]
                
                if not self._access_token:
                    return False
                
                self._token_expires_at = _get_token_expiration(self._access_token)
                
                logger.debug("Access token refreshed successfully")
                return True
                
        except Exception as e:
            logger.warning(f"Failed to refresh token: {e}")
            return False

    def _authenticate(self) -> None:
        """Obtiene un nuevo token de autenticación"""
        logger.debug("Authenticating with API")
        try:
            token_data = get_auth_token(self.api_base_url, self.api_username, self.api_password)
            
            if not self._access_token:
                raise
            self._access_token = token_data["access_token"]
            self._refresh_token = token_data.get("refresh_token")
            
            self._token_expires_at = _get_token_expiration(self._access_token)
            
            if self._token_expires_at:
                time_to_expire = self._token_expires_at - dt.datetime.now()
                logger.debug(f"Token expires at {self._token_expires_at} (in {time_to_expire})")
            else:
                logger.debug("Token expiration not found in JWT, using 1 hour default")
                self._token_expires_at = dt.datetime.now() + dt.timedelta(hours=1)
                
            logger.debug("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
            raise

    def _get_client(self) -> httpx.Client:
        """Obtiene un cliente HTTP autenticado, reutilizando la conexión si es posible"""
        if not self._is_token_valid():
            if self._refresh_token and not self._refresh_access_token():
                self._authenticate()
            elif not self._refresh_token:
                self._authenticate()
            
            if self._client:
                self._client.close()
                self._client = None

        if self._client is None:
            url_parse = urllib.parse.urlparse(self.api_base_url)
            url = url_parse.geturl()
            auth = {"Authorization": f"Bearer {self._access_token}"}
            self._client = httpx.Client(
                base_url=url, 
                headers=auth, 
                timeout=TIMEOUT, 
                verify=SSL_CONTEXT
            )
            logger.debug("Created new HTTP client")
        
        return self._client

    def _handle_auth_error(self, error: httpx.HTTPStatusError) -> None:
        """Maneja errores de autenticación forzando una nueva autenticación"""
        if error.response.status_code == 401:
            logger.warning("Received 401, forcing re-authentication")
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
            if self._client:
                self._client.close()
                self._client = None

    def fetch_schedule_usage_records_large_interval(
        self, since: dt.datetime, until: dt.datetime, meter_serial: Optional[str] = None, frt_code: Optional[str] = None
    ) -> list[ScheduleUsageRecord]:
        _validate_query_parameters(frt_code, meter_serial)
        
        number_of_requests = math.ceil((until - since) / MAX_REQUEST_RANGE)
        logger.debug(f"Fetching usages in {number_of_requests} requests")
        usage_records = []
        
        for i in range(0, number_of_requests):
            fi = since + i * MAX_REQUEST_RANGE
            ff = min(fi + MAX_REQUEST_RANGE, until)
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    client = self._get_client()
                    this_usage_records = get_schedule_usage_records(
                        client, frt_code=frt_code, since=fi, until=ff, meter_serial=meter_serial
                    )
                    usage_records.extend(this_usage_records)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401 and attempt < max_retries - 1:
                        logger.warning(f"Authentication error on attempt {attempt + 1}, retrying...")
                        self._handle_auth_error(e)
                        continue
                    else:
                        raise
                        
        return usage_records

    def fetch_schedule_measurements_records_large_interval(
        self, since: dt.datetime, until: dt.datetime, meter_serial: Optional[str] = None, frt_code: Optional[str] = None
    ) -> list[ScheduleMeasurementRecord]:
        _validate_query_parameters(frt_code, meter_serial)
        
        number_of_requests = math.ceil((until - since) / MAX_REQUEST_RANGE)
        logger.debug(f"Fetching schedules in {number_of_requests} requests")
        schedule_records = []
        
        for i in range(0, number_of_requests):
            fi = since + i * MAX_REQUEST_RANGE
            ff = min(fi + MAX_REQUEST_RANGE, until)
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    client = self._get_client()
                    this_schedule_records = get_schedule_measurement_records(
                        client, frt_code=frt_code, since=fi, until=ff, meter_serial=meter_serial
                    )
                    schedule_records.extend(this_schedule_records)
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401 and attempt < max_retries - 1:
                        logger.warning(f"Authentication error on attempt {attempt + 1}, retrying...")
                        self._handle_auth_error(e)
                        continue
                    else:
                        raise
                        
        return schedule_records

    def close(self) -> None:
        """Cierra la conexión HTTP explícitamente"""
        if self._client:
            self._client.close()
            self._client = None
        logger.debug("HTTP client closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cierra la conexión automáticamente"""
        self.close()
