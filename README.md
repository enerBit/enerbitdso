```txt
███████╗██████╗     ██████╗ ███████╗ ██████╗ 
██╔════╝██╔══██╗    ██╔══██╗██╔════╝██╔═══██╗
█████╗  ██████╔╝    ██║  ██║███████╗██║   ██║
██╔══╝  ██╔══██╗    ██║  ██║╚════██║██║   ██║
███████╗██████╔╝    ██████╔╝███████║╚██████╔╝
╚══════╝╚═════╝     ╚═════╝ ╚══════╝ ╚═════╝ 
                                             
```

# Introducción

Un programa de línea de comandos para preparar y empujar reportes de lectura desde el api de enerBit al MDM.

Se distribuye como un paquete de Python ejecutable.

# Como empezar

## Instalación

1. Crear un ambiente virtual de Python para aislar la instalación del paquete de otros paquetes.

    ```powershell
    python3 -m venv venv
    source ./venv/Scripts/activate
    ```

2. Instalar paquete usando pip (asegurarse de tener activo el ambiente virtual).

    ```powershell
    python -m pip install enerbitdso
    ```

3. Comprobar la instalación con el comando de ayuda

    ```powershell
    enerbitdso --help
    ```

# Uso

El comando es `enerbitdso`.

Se tiene una ayuda usando la opción `--help`.
Esta explica los sub-comandos y las opciones disponibles de cada uno.

Esta herramienta usa las variables de entorno para configurar su ejecución.

## Sub-comandos

### `enerbitdso usages fetch`

Consulta los consumos usando el API para DSO de enerBit para un conjunto de fronteras.

#### Variables de entorno **requeridas**

Para ejecutar este sub-comando se requieren tres variables de entorno configuradas con sus respectivos valores.

- ENERBIT_API_BASE_URL: La URL base del API del DSO, su valor debe ser `https://dso.enerbit.me/`
- ENERBIT_API_USERNAME: El nombre de usuario para autenticarse contra el API, ejemplo: `pedro.perez@example.com`
- ENERBIT_API_PASSWORD: La contraseña del usuario para autenticarse, ejemplo: `mIClaVeSUperseCRETa`

Para configurar estas variables de entorno se pueden ejecutar los siguientes comandos en la terminal de PowerShell:

```powershell
$env:ENERBIT_API_BASE_URL='https://dso.enerbit.me/'
$env:ENERBIT_API_USERNAME='pedro.perez@example.com'
$env:ENERBIT_API_PASSWORD='mIClaVeSUperseCRETa'
```

#### Especificación de fronteras a consultar

Las fronteras a consultar se pueden especificar como una lista al final del comando separadas por espacios:

```powershell
> enerbitdso usages fetch Frt00000 Frt00001
```

También se puede usar un archivo de texto con un código de frontera por línea usando la opción `--frt-file` y pasando la ubicación de dicho archivo.

```powershell
> enerbitdso usages fetch --frt-file "D://Mi CGM/misfronteras.txt"
```

Donde el archivo `D://Mi CGM/misfronteras.txt` tiene un contenido así:

```txt
Frt00000
Frt00001
```

También se puede consultar por serial de medidor usando la opción `--meter-serial`:

```powershell
> enerbitdso usages fetch --meter-serial "S4AM22060202018" --since 20230401 --until 20230405
```

> **Nota:** `--meter-serial` es mutuamente excluyente con los códigos de frontera (`--frt-file` o argumentos FRTS).

#### Especificación de intervalo de tiempo para la consulta

El intervalo de tiempo se define a través de los parámetros de tipo fecha `--since` y `--until` (desde y hasta, respectivamente).
*Por defecto*, se consultan los 24 periodos del día de ayer.

Para consultar los periodos entre 2023-04-01 a las 09:00 y el 2023-04-05 a las 17:00:

```powershell
> enerbitdso usages fetch Frt00000 Frt00001 --since 20230401 --until 20230405
```

#### Salida tipo CSV

Para que el formato de salida sea CSV (valores separados por coma) se puede usar el parámetro `--out-format` con el valor `csv` (*por defecto* se usa `jsonl` que es una línea de JSON por cada registro).

```powershell
> enerbitdso usages fetch Frt00000 Frt00001 --since 20230401 --until 20230405 --out-format csv
```

#### Salida a archivo local

Tanto en sistemas Linux, macOS y Windows se puede usar el operador de **redirección** `>` para enviar a un archivo la salida de un comando.
En este caso el comando seria así:

```powershell
> enerbitdso usages fetch --frt-file "D://Mi CGM/misfronteras.txt" --since 20230401 --until 20230405 --out-format csv > "D://Mi CGM/mi_archivo_de_salida.csv" 
```

#### Opción de ayuda

También tiene opción `--help` que muestra la ayuda particular de este sub-comando.

```powershell
> enerbitdso usages fetch --help

 Usage: enerbitdso usages fetch [OPTIONS] [FRTS]...

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   frts      [FRTS]...  List of frt codes separated by ' ' [default: None]                                         │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --api-base-url        TEXT               [env var: ENERBIT_API_BASE_URL] [default: None] [required]            │
│ *  --api-username        TEXT               [env var: ENERBIT_API_USERNAME] [default: None] [required]            │
│ *  --api-password        TEXT               [env var: ENERBIT_API_PASSWORD] [default: None] [required]            │
│    --since               [%Y-%m-%d|%Y%m%d]  [default: (yesterday)]                                                │
│    --until               [%Y-%m-%d|%Y%m%d]  [default: (today)]                                                    │
│    --timezone            TEXT               [default: America/Bogota]                                             │
│    --out-format          [csv|jsonl]        Output file format [default: jsonl]                                   │
│    --frt-file            PATH               Path file with one frt code per line [default: None]                  │
│    --connection_timeout  INTEGER RANGE      The timeout used for HTTP connection in seconds[0<=x<=20][default: 10]│
│    --read_timeout        INTEGER RANGE      The timeout used for HTTP requests in seconds[60<=x<=120][default: 60]│
│    --meter-serial        TEXT               Serial del medidor a consultar [default: None]                        │
│    --help                                   Show this message and exit.                                           │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

# Librería DSO

Para uso programático, `DSOClient` es un cliente asíncrono que debe usarse con `async with` y `await`.

## Uso básico

```python
import asyncio
import datetime as dt
from enerbitdso.enerbit import DSOClient

since = dt.datetime(2023, 4, 1, tzinfo=dt.timezone.utc)
until = dt.datetime(2023, 4, 5, tzinfo=dt.timezone.utc)

async def main():
    async with DSOClient(
        api_base_url="https://dso.enerbit.me",
        api_username="usuario@empresa.com",
        api_password="contraseña",
    ) as client:
        records = await client.fetch_schedule_usage_records_large_interval(
            frt_code="Frt00000", since=since, until=until
        )

asyncio.run(main())
```

También se puede consultar por serial de medidor:

```python
async def main():
    async with DSOClient(
        api_base_url="https://dso.enerbit.me",
        api_username="usuario@empresa.com",
        api_password="contraseña",
    ) as client:
        records = await client.fetch_schedule_usage_records_large_interval(
            meter_serial="S4AM22060202018", since=since, until=until
        )
```

Y para consultar perfiles de medición:

```python
async def main():
    async with DSOClient(
        api_base_url="https://dso.enerbit.me",
        api_username="usuario@empresa.com",
        api_password="contraseña",
    ) as client:
        schedule_records = await client.fetch_schedule_measurements_records_large_interval(
            frt_code="Frt00000", since=since, until=until
        )
```

## Parámetros de timeout

Para mejorar la estabilidad en consultas masivas se pueden configurar timeouts personalizados:

```python
async with DSOClient(
    api_base_url="https://dso.enerbit.me",
    api_username="tu_usuario@empresa.com",
    api_password="tu_contraseña",
    connection_timeout=20,  # Timeout de conexión en segundos (0-20, default: 10)
    read_timeout=120        # Timeout de lectura en segundos (60-120, default: 60)
) as client:
    ...
```

## Variables de entorno para credenciales

Una práctica recomendada es usar variables de entorno para las credenciales:

```python
import asyncio
import os
from enerbitdso.enerbit import DSOClient

async def main():
    async with DSOClient(
        api_base_url=os.getenv("DSO_HOST", "https://dso.enerbit.me"),
        api_username=os.getenv("DSO_USERNAME"),
        api_password=os.getenv("DSO_PASSWORD"),
        connection_timeout=20,
        read_timeout=120,
    ) as client:
        ...

asyncio.run(main())
```

**Linux/macOS:**
```bash
export DSO_HOST="https://dso.enerbit.me"
export DSO_USERNAME="tu_usuario@empresa.com"
export DSO_PASSWORD="tu_contraseña"
```

**Windows:**
```cmd
set DSO_HOST=https://dso.enerbit.me
set DSO_USERNAME=tu_usuario@empresa.com
set DSO_PASSWORD=tu_contraseña
```

# Ejemplos

El repositorio incluye dos archivos de ejemplo para distintos casos de uso.

## `basic_example.py` — Procesamiento secuencial

Para uso simple o pocas fronteras. Procesa cada frontera una por una, lo que lo hace fácil de entender y depurar.

- Sin concurrencia
- Sin reintentos automáticos
- Muestra el progreso cada 500 fronteras
- Genera un archivo Excel con matrices horarias de consumo

### Uso:

1. Configurar variables de entorno (como se describe arriba) o editar las constantes `DSO_USER`, `DSO_PASSWORD` y `DSO_BASE_URL` en el script.
2. Crear archivo de fronteras `frt_prueba.txt` con una frontera por línea.
3. Ejecutar:
   ```bash
   python basic_example.py
   ```

## `concurrent_example.py` — Procesamiento concurrente

Para procesamiento masivo (cientos o miles de fronteras). Lanza todas las consultas en paralelo con un límite de concurrencia.

- Usa `asyncio.Semaphore(5)` para limitar la concurrencia máxima a 5 solicitudes simultáneas
- Reintentos con backoff exponencial (hasta 3 intentos por frontera)
- Monitoreo de progreso cada 500 fronteras
- Genera un archivo Excel con matrices horarias de consumo

### Uso:

1. Configurar variables de entorno o editar las constantes en el script.
2. Crear archivo de fronteras `frt_prueba.txt` con una frontera por línea.
3. Ejecutar:
   ```bash
   python concurrent_example.py
   ```

### Archivos generados por ambos ejemplos:

- `Matrices_YYYYMMDD_HHMM.xlsx` — Datos principales organizados por matrices horarias
- `fronteras_fallidas_YYYYMMDD_HHMM.txt` — Lista de fronteras que no se pudieron procesar

### Configuración recomendada para producción:

Para ambientes de producción o consultas masivas, ajusta estos parámetros en el ejemplo:

- **semaphore**: Límite de conexiones concurrentes. Reduce de 30 a 5-10 para evitar saturar el servidor
- **Timeouts**: Usa connection_timeout=20 y read_timeout=120 como mínimo
- **Intervalos de tiempo**: Limita los rangos de fechas para consultas más eficientes

Los archivos `*_example.py` sirve como base para desarrollar tus propios scripts de procesamiento masivo de datos de enerBit DSO.
