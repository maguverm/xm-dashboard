import pandas as pd
from pathlib import Path

# rutas
ruta_entrada = Path("../data/raw/maestro_plantas.xlsx")
ruta_salida = Path("../data/processed/maestro_plantas.csv")

# leer archivo
df = pd.read_excel(ruta_entrada)

# columnas relevantes
df = df[[
    "CodigoPlanta",
    "NombreUnidad",
    "TipoGeneracion",
    "FPO"
]].copy()

# eliminar duplicados por CodigoPlanta
df = df.drop_duplicates(subset=["CodigoPlanta"])

# limpiar nombres
df["NombreUnidad"] = df["NombreUnidad"].str.strip()

# guardar
df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("Maestro procesado listo:", ruta_salida)
print(df.head())
print("Filas:", len(df))