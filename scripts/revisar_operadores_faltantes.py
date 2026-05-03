import pandas as pd
from pathlib import Path

ruta = Path("../data/processed/generacion_limpia.csv")

df = pd.read_csv(ruta)

print("Columnas:")
print(df.columns)

print("\nFilas totales:", len(df))
print("Filas sin operador:", df["Operador"].isna().sum())

faltantes = (
    df[df["Operador"].isna()]
    [["CodigoPlanta", "NombreUnidad", "TipoGeneracion"]]
    .drop_duplicates()
    .sort_values("NombreUnidad")
)

print("\nPrimeras plantas sin operador:")
print(faltantes.head(80).to_string(index=False))

print("\nTotal plantas sin operador:", len(faltantes))

faltantes.to_csv(
    "../data/processed/plantas_sin_operador_generacion.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nArchivo exportado: data/processed/plantas_sin_operador_generacion.csv")