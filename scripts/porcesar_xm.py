from pathlib import Path
import pandas as pd

carpeta_raw = Path("../data/raw")
ruta_salida = Path("../data/processed/precio_bolsa_limpio.csv")

lista_df = []

for archivo in carpeta_raw.glob("precio_bolsa_*.xlsx"):
    print(f"Procesando {archivo.name}")

    df = pd.read_excel(archivo, header=2)

    if "Versión" in df.columns:
        df = df.drop(columns=["Versión"])

    df_largo = df.melt(
        id_vars=["Fecha"],
        var_name="hora",
        value_name="precio"
    )

    df_largo["fecha"] = pd.to_datetime(df_largo["Fecha"])
    df_largo["hora"] = df_largo["hora"].astype(int)
    df_largo["precio"] = pd.to_numeric(df_largo["precio"], errors="coerce")

    df_largo = df_largo[["fecha", "hora", "precio"]]

    lista_df.append(df_largo)

df_total = pd.concat(lista_df, ignore_index=True)

df_total = df_total.dropna(subset=["fecha", "precio"])
df_total = df_total.drop_duplicates(subset=["fecha", "hora"])
df_total = df_total.sort_values(["fecha", "hora"])

df_total.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("Archivo consolidado creado correctamente")
print(df_total.head())
print(df_total.tail())
print(df_total.shape)