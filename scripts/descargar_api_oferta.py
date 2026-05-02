import requests
import json
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import time

dataset_id = "b1189f"

fecha_inicio = date(2024, 1, 1)
fecha_fin = datetime.today().date()

ruta_maestro = Path("../data/processed/maestro_plantas.csv")
ruta_salida = Path("../data/processed/precio_oferta_limpio.csv")


def generar_meses(inicio, fin):
    meses = []
    actual = date(inicio.year, inicio.month, 1)

    while actual <= fin:
        if actual.month == 12:
            siguiente = date(actual.year + 1, 1, 1)
        else:
            siguiente = date(actual.year, actual.month + 1, 1)

        fin_mes = min(siguiente - pd.Timedelta(days=1), fin)
        meses.append((actual, fin_mes))
        actual = siguiente

    return meses


def consultar_simem(start_date, end_date):
    url = (
        "https://www.simem.co/backend-files/api/datos-publicos"
        f"?datasetId={dataset_id}"
        f"&startDate={start_date}"
        f"&endDate={end_date}"
    )

    buffer = ""

    with requests.post(url, json=[], stream=True, timeout=180) as response:
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                buffer += chunk.decode("utf-8")

    if not buffer.strip():
        return pd.DataFrame()

    data = json.loads(buffer)
    return pd.DataFrame(data)


meses = generar_meses(fecha_inicio, fecha_fin)
lista_df = []

print(f"Meses a consultar: {len(meses)}")
print("-" * 60)

for i, (inicio_mes, fin_mes) in enumerate(meses, start=1):
    print(f"[{i}/{len(meses)}] Consultando {inicio_mes} a {fin_mes}...")

    try:
        df_mes = consultar_simem(inicio_mes, fin_mes)

        if df_mes.empty:
            print("   Sin datos.")
            continue

        print(f"   Registros brutos: {len(df_mes):,}")

        df_mes["FechaHora"] = pd.to_datetime(df_mes["FechaHora"])
        df_mes["precio_oferta"] = pd.to_numeric(df_mes["Valor"], errors="coerce")

        df_mes = df_mes[[
            "FechaHora",
            "CodigoPlanta",
            "precio_oferta"
        ]].copy()

        df_mes["fecha"] = df_mes["FechaHora"].dt.date

        # Promedio diario por planta
        df_mes = (
            df_mes
            .groupby(["fecha", "CodigoPlanta"], as_index=False)["precio_oferta"]
            .mean()
        )

        print(f"   Registros diarios: {len(df_mes):,}")

        lista_df.append(df_mes)

        time.sleep(0.5)

    except Exception as e:
        print(f"   Error en {inicio_mes:%Y-%m}: {e}")


if not lista_df:
    raise ValueError("No se descargaron datos de precio de oferta.")

df = pd.concat(lista_df, ignore_index=True)

# Por seguridad: eliminar duplicados entre meses
df = (
    df
    .groupby(["fecha", "CodigoPlanta"], as_index=False)["precio_oferta"]
    .mean()
)

maestro = pd.read_csv(ruta_maestro)

df = df.merge(
    maestro,
    on="CodigoPlanta",
    how="left"
)

df = df[[
    "fecha",
    "CodigoPlanta",
    "NombreUnidad",
    "TipoGeneracion",
    "FPO",
    "precio_oferta"
]]

df = df.sort_values(["fecha", "precio_oferta"], ascending=[True, False])

ruta_salida.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("-" * 60)
print("Archivo creado:", ruta_salida)
print("Filas finales:", len(df))
print("Primera fecha:", df["fecha"].min())
print("Última fecha:", df["fecha"].max())
print(df.head())