from datetime import datetime
import requests
from pathlib import Path

carpeta_raw = Path("../data/raw")
carpeta_raw.mkdir(parents=True, exist_ok=True)

anio_actual = datetime.now().year

for anio in range(2000, anio_actual + 1):
    url = f"https://sinergox.xm.com.co/trpr/Histricos/Precio_Bolsa_Nacional_($kwh)_{anio}.xlsx"
    ruta = carpeta_raw / f"precio_bolsa_{anio}.xlsx"

    respuesta = requests.get(url)

    if respuesta.status_code == 200:
        with open(ruta, "wb") as archivo:
            archivo.write(respuesta.content)
        print(f"Descargado: {anio}")
    else:
        print(f"No disponible: {anio}")