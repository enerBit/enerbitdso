from enerbitdso.enerbit import DSOClient
from datetime import datetime as dt
import pandas as pd
import pytz
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random

colombia_tz = pytz.timezone('America/Bogota')

ebconnector = DSOClient(
    api_base_url=os.getenv("DSO_HOST"),
    api_username=os.getenv("DSO_USERNAME"),
    api_password=os.getenv("DSO_PASSWORD"),
    connection_timeout=20,
    read_timeout=120
)
since = dt.strptime("2025-09-04T00:00-05:00", "%Y-%m-%dT%H:%M%z")
until = dt.strptime("2025-09-08T00:00-05:00", "%Y-%m-%dT%H:%M%z")   

with open("frt_prueba.txt", "r") as f1:
    frontiers = [line.strip() for line in f1 if line.strip()]

usage_records_dict = []
fronteras_fallidas = []

print("Generando archivo...")

def fetch_usage_records(frontier, max_retries=3):
    for attempt in range(max_retries):
        try:
            usage_records = ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=frontier, since=since, until=until
            )

            if not usage_records:
                print(f"[INFO] No se encontraron datos para la frontera {frontier}.")
                return []

            return [{
                "Frontera": usage_record.frt_code if usage_record.frt_code is not None else "SIN_FRONTERA",
                "Serial": usage_record.meter_serial,
                "time_start": str(usage_record.time_start.astimezone(colombia_tz).strftime('%Y-%m-%d %H:%M:%S%z')),
                "time_end": str(usage_record.time_end.astimezone(colombia_tz).strftime('%Y-%m-%d %H:%M:%S%z')),
                "kWhD": usage_record.active_energy_imported,
                "kWhR": usage_record.active_energy_exported,
                "kVarhD": usage_record.reactive_energy_imported,
                "kVarhR": usage_record.reactive_energy_exported
            } for usage_record in usage_records]

        except Exception as e:
            if attempt < max_retries - 1:
                # Backoff exponencial con jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"[RETRY] Frontera {frontier}, intento {attempt + 1}/{max_retries}. Esperando {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[ERROR] Error procesando la frontera {frontier} después de {max_retries} intentos: {e}")
                fronteras_fallidas.append(frontier)
                return []

with ThreadPoolExecutor(max_workers=30) as executor:
    future_to_frontier = {executor.submit(fetch_usage_records, frontier): frontier for frontier in frontiers}
    
    processed_count = 0
    total_frontiers = len(frontiers)
    
    for future in as_completed(future_to_frontier):
        usage_records_dict.extend(future.result())
        processed_count += 1
        
        # Mostrar progreso cada 500 fronteras o al final
        if processed_count % 500 == 0 or processed_count == total_frontiers:
            print(f"📊 Progreso: {processed_count}/{total_frontiers} fronteras procesadas ({processed_count/total_frontiers*100:.1f}%)")

# Generar reporte de fronteras fallidas
if fronteras_fallidas:
    timestamp_failed = dt.now().strftime("%Y%m%d_%H%M")
    failed_filename = f"fronteras_fallidas_{timestamp_failed}.txt"
    
    with open(failed_filename, "w") as out:
        out.write("\n".join(fronteras_fallidas))
    
    print(f"\n❌ {len(fronteras_fallidas)} fronteras fallaron y se guardaron en: {failed_filename}")
    print(f"Fronteras exitosas: {total_frontiers - len(fronteras_fallidas)}/{total_frontiers}")
else:
    print(f"\n✅ Todas las {total_frontiers} fronteras se procesaron exitosamente.")

if not usage_records_dict:
    print("⚠️ No se encontraron registros para ninguna frontera. Terminando script.")
    exit()

print("\n🔄 Procesando datos y generando Excel...")

df = pd.DataFrame(usage_records_dict)
df['time_start'] = pd.to_datetime(df['time_start'])

df['Año'] = df['time_start'].dt.year
df['Mes'] = df['time_start'].dt.month
df['Día'] = df['time_start'].dt.day
df['hora_en_punto'] = df['time_start'].dt.hour

cuadrante = ["kWhD", "kWhR", "kVarhD", "kVarhR"]
df_long = df.melt(
    id_vars=["Frontera", "Serial", "Año", "Mes", "Día", "hora_en_punto"],
    value_vars=cuadrante,
    var_name="Tipo",
    value_name="valor_cuadrante"
)

horas = list(range(24))
resultado = (
    df_long.pivot_table(
        index=["Serial", "Frontera", "Tipo", "Año", "Mes", "Día"],
        columns="hora_en_punto",
        values="valor_cuadrante",
        aggfunc="first"
    )
    .reindex(columns=horas, fill_value=0)
    .reset_index()
)
resultado.columns.name = None
resultado = resultado.rename(columns={col: f"Hora {col}" for col in resultado.columns if isinstance(col, int)})

timestamp = dt.now().strftime("%Y%m%d_%H%M")
filename = f"Matrices_{timestamp}.xlsx"
resultado.to_excel(filename, index=False)

print(f"\n✅ Archivo generado correctamente: {filename}")

# Resumen final
print(f"\n📋 RESUMEN FINAL:")
print(f"   • Total fronteras: {total_frontiers}")
print(f"   • Exitosas: {total_frontiers - len(fronteras_fallidas)}")
print(f"   • Fallidas: {len(fronteras_fallidas)}")
print(f"   • Registros procesados: {len(usage_records_dict)}")
