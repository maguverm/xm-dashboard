import subprocess

print("Descargando datos...")
subprocess.run(["python", "descargar_xm.py"])

print("Procesando datos...")
subprocess.run(["python", "procesar_xm.py"])

print("Datos actualizados correctamente")