import pandas as pd
import re
import unicodedata
from pathlib import Path


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

# -----------------------
# Rutas
# -----------------------
ruta_entrada = Path("../data/raw/Paratec.xlsx")
ruta_salida = Path("../data/processed/mapa_operadores.csv")

# -----------------------
# Leer archivo Paratec
# -----------------------
paratec = pd.read_excel(ruta_entrada)

print(paratec.head())
print(paratec.columns)

# -----------------------
# Crear nombre limpio
# -----------------------
paratec["Nombre_clean"] = paratec["Nombre"].apply(limpiar_nombre)

# -----------------------
# Dejar columnas útiles
# -----------------------
mapa_operadores = paratec[[
    "Nombre",
    "Nombre_clean",
    "Operador",
    "Estado",
    "Departamento",
    "Municipio"
]].copy()

# Eliminar duplicados
mapa_operadores = mapa_operadores.drop_duplicates(subset=["Nombre_clean"])

# Guardar
mapa_operadores.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("Mapa de operadores creado:")
print(ruta_salida)
print(mapa_operadores.head())
print("Filas:", len(mapa_operadores))