import requests
import json
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import time
import re
import unicodedata

dataset_id = "E17D25"

fecha_inicio = date(2020, 1, 1)
fecha_fin = datetime.today().date()

ruta_maestro = Path("../data/processed/maestro_plantas.csv")
ruta_operadores = Path("../data/processed/mapa_operadores.csv")
ruta_salida = Path("../data/processed/generacion_limpia.csv")


# -----------------------
# Función limpieza nombre
# -----------------------
def limpiar_nombre(nombre):
    if pd.isna(nombre):
        return nombre

    nombre = str(nombre).upper()

    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = "".join(c for c in nombre if not unicodedata.combining(c))

    nombre = re.sub(r"\s\d+$", "", nombre)
    nombre = re.sub(r"\sG\d+$", "", nombre)
    nombre = re.sub(r"\sCC\s*\d*$", " CC", nombre)

    return nombre.strip()


# Ajustes manuales (los mismos de oferta)
ajustes_manual_nombre = {
    "FLORES": "FLORES",
    "GUADALUPE": "GUADALUPE",
    "RIO PIEDRAS": "RIO PIEDRAS",
    "TEBSA": "TEBSA",
    "TERMOCENTRO": "TERMOCENTRO",
    "TERMOEMCALI": "TERMOEMCALI",
    "TERMOSIERRA": "TERMOSIERRA CC",
    "TERMOVALLE": "TERMOVALLE",
}

ajustes_operador_codigo = {
    "TSR1": "EMPRESAS PUBLICAS DE MEDELLIN E.S.P."
}


# -----------------------
# Generar meses
# -----------------------
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


# -----------------------
# Consulta API
# -----------------------
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


# -----------------------
# Descarga mensual
# -----------------------
meses = generar_meses(fecha_inicio, fecha_fin)
lista_df = []

print(f"Meses a consultar: {len(meses)}")
print("-" * 60)

for i, (inicio_mes, fin_mes) in enumerate(meses, start=1):
    print(f"[{i}/{len(meses)}] {inicio_mes} a {fin_mes}")

    try:
        df_mes = consultar_simem(inicio_mes, fin_mes)

        if df_mes.empty:
            print("   Sin datos")
            continue

        print(f"   Registros: {len(df_mes):,}")

        df_mes["Fecha"] = pd.to_datetime(df_mes["Fecha"])

        for col in [
            "GeneracionRealEstimada",
            "GeneracionProgramadaDespacho",
            "GeneracionProgramadaRedespacho"
        ]:
            df_mes[col] = pd.to_numeric(df_mes[col], errors="coerce")

        df_mes = (
            df_mes
            .groupby(
                ["Fecha", "CodigoPlanta"],
                as_index=False
            )[[
                "GeneracionRealEstimada",
                "GeneracionProgramadaDespacho",
                "GeneracionProgramadaRedespacho"
            ]]
            .sum()
        )

        lista_df.append(df_mes)

        time.sleep(0.5)

    except Exception as e:
        print(f"Error en {inicio_mes}: {e}")


if not lista_df:
    raise ValueError("No se descargaron datos")

df = pd.concat(lista_df, ignore_index=True)

# -----------------------
# Renombrar columnas
# -----------------------
df = df.rename(columns={
    "Fecha": "fecha",
    "GeneracionRealEstimada": "gen_real",
    "GeneracionProgramadaDespacho": "gen_prog",
    "GeneracionProgramadaRedespacho": "gen_redesp"
})

# -----------------------
# Merge con maestro
# -----------------------
maestro = pd.read_csv(ruta_maestro)
mapa_operadores = pd.read_csv(ruta_operadores)

df = df.merge(
    maestro,
    on="CodigoPlanta",
    how="left"
)

# -----------------------
# Merge con operador
# -----------------------
df["NombreUnidad_clean"] = df["NombreUnidad"].apply(limpiar_nombre)
df["NombreUnidad_clean"] = df["NombreUnidad_clean"].replace(ajustes_manual_nombre)

df = df.merge(
    mapa_operadores[["Nombre_clean", "Operador"]],
    left_on="NombreUnidad_clean",
    right_on="Nombre_clean",
    how="left"
)

# Ajustes manuales por código
for codigo, operador in ajustes_operador_codigo.items():
    df.loc[df["CodigoPlanta"] == codigo, "Operador"] = operador

df["Operador"] = df["Operador"].fillna("SIN OPERADOR")

# -----------------------
# Selección final
# -----------------------
df = df[[
    "fecha",
    "Operador",
    "CodigoPlanta",
    "NombreUnidad",
    "TipoGeneracion",
    "gen_real",
    "gen_prog",
    "gen_redesp"
]]

df = df.sort_values(["fecha", "gen_real"], ascending=[True, False])

# -----------------------
# Guardar
# -----------------------
ruta_salida.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("-" * 60)
print("Archivo creado:", ruta_salida)
print("Filas:", len(df))
print("Desde:", df["fecha"].min(), "hasta:", df["fecha"].max())

print("\nOperadores faltantes:", df["Operador"].isna().sum())