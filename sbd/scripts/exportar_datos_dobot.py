import os
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuración ---
CSV_FILE = "/app/datos/dataset_dobot_cr5a.csv"
DEVICE_NAME = "Dobot_CR5A"  # Se asigna como Tag
BATCH_SIZE = 500

# Mapeo de estados del robot Dobot CR Series
ROBOT_MODE_MAP = {
    1: "Inicializando",
    2: "Frenos Abiertos",
    3: "Deshabilitado",
    4: "Habilitado / En espera",
    5: "Guiado Manual (Drag)",
    6: "En Ejecución",
    7: "Grabando",
    8: "Pausado",
    9: "Modo Jog",
    10: "Error / Colisión",
    11: "Paso a Paso",
}

TEMP_FIELDS = [f"j{i}_temp" for i in range(1, 7)]
CURRENT_FIELDS = [f"j{i}_current" for i in range(1, 7)]
POSE_FIELDS = ["pos_x", "pos_y", "pos_z", "rot_rx", "rot_ry", "rot_rz"]


def cargar_env():
    """Busca el .env en el directorio actual o en los superiores y lo carga."""
    env_file = find_dotenv(".env", usecwd=True)
    if not env_file:
        for candidate in (
            Path.cwd() / ".env",
            Path.cwd().parent / ".env",
            Path.cwd().parent.parent / ".env",
        ):
            if candidate.is_file():
                env_file = str(candidate)
                break
    if not env_file:
        raise FileNotFoundError("No se encontró el archivo .env")
    load_dotenv(env_file, override=True)
    return env_file


def required_env(name, env_file):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta la variable {name} en {env_file}")
    return value


def describir_modo(code):
    if pd.isnull(code):
        return "N/A"
    return ROBOT_MODE_MAP.get(int(code), f"Desconocido ({code})")


def fila_a_punto(row):
    mode_code = int(row["robot_mode"])
    mode_desc = str(row["robot_mode_desc"])

    punto = (
        Point("dobot_telemetry")
        .tag("device_name", DEVICE_NAME)
        .tag("model", "CR5A")
        .tag("robot_mode_desc", mode_desc)
        .field("robot_mode", mode_code)
        .field("robot_mode_text", mode_desc)
        .time(row["timestamp"], WritePrecision.NS)
    )
    for campo in POSE_FIELDS + TEMP_FIELDS + CURRENT_FIELDS:
        punto = punto.field(campo, float(row[campo]))
    return punto


def main():
    env_file = cargar_env()
    url = required_env("INFLUX_URL", env_file)
    token = required_env("INFLUX_TOKEN", env_file)
    org = required_env("INFLUX_ORG", env_file)
    bucket = required_env("INFLUX_BUCKET_DOBOT", env_file)

    print(f"Cargando dataset desde '{CSV_FILE}'...")
    try:
        df = pd.read_csv(CSV_FILE, engine="python", on_bad_lines="skip")
    except FileNotFoundError:
        print(f"Error: no se encontró '{CSV_FILE}'. Revisa la ruta.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Si el CSV no trae 'robot_mode_desc', se calcula a partir de 'robot_mode'
    if "robot_mode_desc" not in df.columns:
        df["robot_mode_desc"] = df["robot_mode"].apply(describir_modo)

    total = len(df)
    print(f"Registros cargados: {total} filas.")
    print(f"Subiendo al bucket '{bucket}'...")

    with InfluxDBClient(url=url, token=token, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        batch = []

        for i, (_, row) in enumerate(df.iterrows(), start=1):
            batch.append(fila_a_punto(row))
            if len(batch) >= BATCH_SIZE:
                write_api.write(bucket=bucket, org=org, record=batch)
                batch = []
                print(f"Registros cargados: {i}/{total}...")

        if batch:
            write_api.write(bucket=bucket, org=org, record=batch)

    print(f"\n¡Migración completada! {total} filas insertadas en InfluxDB.")


if __name__ == "__main__":
    main()