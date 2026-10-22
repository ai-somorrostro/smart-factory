import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv, find_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuración ---
CSV_FILE = "/app/datos/dataset_bambu_multi_printer.csv"
BATCH_SIZE = 500


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


def fila_a_punto(row):
    return (
        Point("bambu_telemetry")
        .tag("printer_name", str(row["printer_name"]))
        .tag("serial_number", str(row["serial_number"]))
        .tag("tray_type", str(row["tray_type"]))
        .tag("gcode_state", str(row["gcode_state"]))
        .field("nozzle_temp", float(row["nozzle_temp"]))
        .field("bed_temp", float(row["bed_temp"]))
        .field("mc_percent", int(row["mc_percent"]))
        .field("layer_num", int(row["layer_num"]))
        .field("total_layer_num", int(row["total_layer_num"]))
        .time(row["timestamp"], WritePrecision.NS)
    )


def main():
    env_file = cargar_env()
    url = required_env("INFLUX_URL", env_file)
    token = required_env("INFLUX_TOKEN", env_file)
    org = required_env("INFLUX_ORG", env_file)
    bucket = required_env("INFLUX_BUCKET_BAMBU", env_file)

    print(f"Leyendo CSV: '{CSV_FILE}'...")
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"Error: no se encuentra '{CSV_FILE}'. Verifica la ruta.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    total = len(df)

    with InfluxDBClient(url=url, token=token, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        batch = []
        print(f"Subiendo {total} registros al bucket '{bucket}'...")

        for i, (_, row) in enumerate(df.iterrows(), start=1):
            batch.append(fila_a_punto(row))
            if len(batch) >= BATCH_SIZE:
                write_api.write(bucket=bucket, org=org, record=batch)
                batch = []
                print(f"Procesadas {i}/{total} filas...")

        if batch:
            write_api.write(bucket=bucket, org=org, record=batch)

    print(f"\nImportación finalizada. {total} registros cargados en InfluxDB.")


if __name__ == "__main__":
    main()