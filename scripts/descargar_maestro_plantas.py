import requests
import json
import pandas as pd
from pathlib import Path
import time

dataset_id = "670221"
url = f"https://www.simem.co/backend-files/api/datos-publicos?datasetId={dataset_id}"

def consultar_api(url, intentos=3):
    for intento in range(1, intentos + 1):
        try:
            print(f"Intento {intento}...")

            buffer = ""

            with requests.post(url, json=[], stream=True, timeout=180) as response:
                response.raise_for_status()

                for chunk in response.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        buffer += chunk.decode("utf-8")

            data = json.loads(buffer)
            return pd.DataFrame(data)

        except Exception as e:
            print(f"Falló intento {intento}: {e}")
            time.sleep(3)

    raise RuntimeError("No se pudo descargar el maestro de plantas.")

df = consultar_api(url)

print(df.head())
print(df.columns)
print(df.shape)

ruta_salida = Path("../data/processed/maestro_plantas.csv")
df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")

print("Maestro guardado en:", ruta_salida)