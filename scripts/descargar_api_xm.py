import requests
import json
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import time

dataset_id = "EC6945"

fecha_inicio = date(2020, 1, 1)
fecha_fin = datetime.today().date()

ruta_salida = Path("../data/processed/precio_bolsa_limpio.csv")
ruta_salida.parent.mkdir(parents=True, exist_ok=True)

orden_version = {
    "TX1": 1,
    "TX2": 2,
    "TX3": 3,
    "TXF": 4,
    "TXR": 5
}

def generar_meses(inicio, fin):
    meses = []
    actual = date(inicio.year, inicio.month, 1)

    while actual <= fin:
        if actual.month == 12:
            siguiente = date(actual.year + 1, 1, 1)
        else:
            siguiente = date(actual.year, actual.month + 1, 1)

        inicio_mes = actual
        fin_mes = min(siguiente - pd.Timedelta(days=1), fin)

        meses.append((inicio_mes, fin_mes))
        actual = siguiente

    return meses


def consultar_simem(start_date, end_date):
    url = (
        "https://www.simem.co/backend-files/api/datos-publicos"
        f"?datasetId={dataset_id}"
        f"&startDate={start_date}"
        f"&endDate={end_date}"
    )

    parameters = []
    buffer = ""

    with requests.post(url, json=parameters, stream=True, timeout=120) as response:
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                buffer += chunk.decode("utf-8")

    if not buffer.strip():
        return pd.DataFrame()

    data = json.loads(buffer)
    return pd.DataFrame(data)


lista_df = []
meses = generar_meses(fecha_inicio, fecha_fin)

print(f"Meses a consultar: {len(meses)}")
print("-" * 50)

for i, (inicio_mes, fin_mes) in enumerate(meses, start=1):
    print(f"[{i}/{len(meses)}] Consultando {inicio_mes} a {fin_mes}...")

    try:
        df_mes = consultar_simem(inicio_mes, fin_mes)

        if df_mes.empty:
            print("   Sin datos.")
            continue

        print(f"   Registros recibidos: {len(df_mes):,}")

        lista_df.append(df_mes)

        time.sleep(0.5)

    except Exception as e:
        print(f"   Error en {inicio_mes:%Y-%m}: {e}")


if not lista_df:
    raise ValueError("No se descargaron datos.")

df = pd.concat(lista_df, ignore_index=True)

print("-" * 50)
print("Total registros brutos:", len(df))

df = df[df["CodigoVariable"] == "PB_Nal"].copy()

df["FechaHora"] = pd.to_datetime(df["FechaHora"])
df["precio"] = pd.to_numeric(df["Valor"], errors="coerce")
df["orden_version"] = df["Version"].map(orden_version)

df = df.sort_values(["FechaHora", "orden_version"])

df = df.drop_duplicates(
    subset=["FechaHora"],
    keep="last"
)

df_limpio = pd.DataFrame({
    "fecha": df["FechaHora"].dt.date,
    "hora": df["FechaHora"].dt.hour,
    "precio": df["precio"]
})

df_limpio = df_limpio.dropna(subset=["precio"])
df_limpio = df_limpio.sort_values(["fecha", "hora"])

df_limpio.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("-" * 50)
print("Archivo limpio creado correctamente.")
print("Ruta:", ruta_salida)
print("Primera fecha:", df_limpio["fecha"].min())
print("Última fecha:", df_limpio["fecha"].max())
print("Filas finales:", len(df_limpio))