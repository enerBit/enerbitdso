import asyncio
import os
import time
import traceback
from datetime import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd

from enerbitdso.enerbit import DSOClient

colombia_tz = ZoneInfo("America/Bogota")

since = dt.strptime("2026-02-01T00:00-05:00", "%Y-%m-%dT%H:%M%z")
until = dt.strptime("2026-02-08T00:00-05:00", "%Y-%m-%dT%H:%M%z")

with open("frt_prueba.txt", "r") as f1:
    frontiers = [line.strip() for line in f1 if line.strip()]

usage_records_dict = []
fronteras_fallidas = []

print("Generando archivo...")


async def main():
    start = time.perf_counter()
    total_frontiers = len(frontiers)

    async with DSOClient(
        api_base_url=os.getenv("DSO_HOST"),
        api_username=os.getenv("DSO_USERNAME"),
        api_password=os.getenv("DSO_PASSWORD"),
        connection_timeout=20,
        read_timeout=120,
    ) as ebconnector:
        for i, frontier in enumerate(frontiers, 1):
            try:
                usage_records = await ebconnector.fetch_schedule_usage_records_large_interval(
                    frt_code=frontier, since=since, until=until
                )

                if not usage_records:
                    print(f"[INFO] No se encontraron datos para la frontera {frontier}.")
                else:
                    usage_records_dict.extend(
                        [
                            {
                                "Frontera": usage_record.frt_code
                                if usage_record.frt_code is not None
                                else "SIN_FRONTERA",
                                "Serial": usage_record.meter_serial,
                                "time_start": str(
                                    usage_record.time_start.astimezone(colombia_tz).strftime("%Y-%m-%d %H:%M:%S%z")
                                ),
                                "time_end": str(
                                    usage_record.time_end.astimezone(colombia_tz).strftime("%Y-%m-%d %H:%M:%S%z")
                                ),
                                "kWhD": usage_record.active_energy_imported,
                                "kWhR": usage_record.active_energy_exported,
                                "kVarhD": usage_record.reactive_energy_imported,
                                "kVarhR": usage_record.reactive_energy_exported,
                            }
                            for usage_record in usage_records
                        ]
                    )

            except Exception as e:
                print(f"[ERROR] Error procesando la frontera {frontier}: {e}")
                fronteras_fallidas.append(frontier)
                traceback.print_exc()

            if i % 500 == 0 or i == total_frontiers:
                print(f"📊 Progreso: {i}/{total_frontiers} fronteras procesadas ({i / total_frontiers * 100:.1f}%)")

    # Generar reporte de fronteras fallidas
    if fronteras_fallidas:
        timestamp_failed = dt.now().strftime("%Y%m%d_%H%M")
        failed_filename = f"fronteras_fallidas_{timestamp_failed}.txt"

        # with open(failed_filename, "w") as out:
        #     out.write("\n".join(fronteras_fallidas))

        print(f"\n❌ {len(fronteras_fallidas)} fronteras fallaron y se guardaron en: {failed_filename}")
        print(f"Fronteras exitosas: {total_frontiers - len(fronteras_fallidas)}/{total_frontiers}")
    else:
        print(f"\n✅ Todas las {total_frontiers} fronteras se procesaron exitosamente.")

    if not usage_records_dict:
        print("⚠️ No se encontraron registros para ninguna frontera. Terminando script.")
        return

    print("\n🔄 Procesando datos y generando Excel...")

    df = pd.DataFrame(usage_records_dict)
    df["time_start"] = pd.to_datetime(df["time_start"])

    df["Año"] = df["time_start"].dt.year
    df["Mes"] = df["time_start"].dt.month
    df["Día"] = df["time_start"].dt.day
    df["hora_en_punto"] = df["time_start"].dt.hour

    cuadrante = ["kWhD", "kWhR", "kVarhD", "kVarhR"]
    df_long = df.melt(
        id_vars=["Frontera", "Serial", "Año", "Mes", "Día", "hora_en_punto"],
        value_vars=cuadrante,
        var_name="Tipo",
        value_name="valor_cuadrante",
    )

    horas = list(range(24))
    resultado = (
        df_long.pivot_table(
            index=["Serial", "Frontera", "Tipo", "Año", "Mes", "Día"],
            columns="hora_en_punto",
            values="valor_cuadrante",
            aggfunc="first",
        )
        .reindex(columns=horas, fill_value=0)
        .reset_index()
    )
    resultado.columns.name = None
    resultado = resultado.rename(columns={col: f"Hora {col}" for col in resultado.columns if isinstance(col, int)})

    timestamp = dt.now().strftime("%Y%m%d_%H%M")
    filename = f"Matrices_{timestamp}.xlsx"
    # resultado.to_excel(filename, index=False)

    print(f"\n✅ Archivo generado correctamente: {filename}")

    # Resumen final
    print("\n📋 RESUMEN FINAL:")
    print(f"   • Total fronteras: {total_frontiers}")
    print(f"   • Exitosas: {total_frontiers - len(fronteras_fallidas)}")
    print(f"   • Fallidas: {len(fronteras_fallidas)}")
    print(f"   • Registros procesados: {len(usage_records_dict)}")
    print(time.perf_counter() - start)


asyncio.run(main())
