import csv
from datetime import datetime
import os
import socket
import struct
import sys
import time
from dotenv import load_dotenv

# ==============================================================================
# 1. CONFIGURACIÓN DE RUTAS Y ARCHIVOS DE ENTORNO
# ==============================================================================

# Ubicación absoluta de la carpeta donde se encuentra este script (sbd/scripts)
RUTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))

# El archivo .env vive en la carpeta raíz "sbd" (un nivel arriba)
RUTA_ENV = os.path.abspath(os.path.join(RUTA_SCRIPT, "..", ".env"))
load_dotenv(RUTA_ENV)

# Carpeta de destino de datos (sbd/datos)
CARPETA_DATA = os.path.abspath(os.path.join(RUTA_SCRIPT, "..", "datos"))

# Crea la carpeta "sbd/datos" si aún no existe
os.makedirs(CARPETA_DATA, exist_ok=True)


def _require_env(name):
  """Lee una variable obligatoria desde sbd/.env o interrumpe la ejecución con error."""
  value = os.getenv(name)
  if value is None or str(value).strip() == "":
    print(
        f"ERROR: falta la variable obligatoria '{name}' en sbd/.env"
        f" ({RUTA_ENV}).\n"
        f"Copia sbd/.env.example a sbd/.env y rellena el valor."
    )
    sys.exit(1)
  return str(value).strip()


def _require_env_int(name):
  """Lee una variable entera obligatoria desde sbd/.env."""
  try:
    return int(_require_env(name))
  except ValueError:
    print(
        f"ERROR: la variable '{name}' debe ser un número entero (revisa"
        " sbd/.env)."
    )
    sys.exit(1)


def _require_env_float(name):
  """Lee una variable decimal obligatoria desde sbd/.env."""
  try:
    return float(_require_env(name))
  except ValueError:
    print(
        f"ERROR: la variable '{name}' debe ser un número decimal (revisa"
        " sbd/.env)."
    )
    sys.exit(1)


# Configuración del archivo de salida CSV
DOBOT_CSV_FILE = _require_env("DOBOT_CSV_FILE")
CSV_FILE = os.path.join(CARPETA_DATA, DOBOT_CSV_FILE)

# ==============================================================================
# 2. CONFIGURACIÓN DE RED Y MUESTREO (desde sbd/.env)
# ==============================================================================
DOBOT_IP = _require_env("DOBOT_IP")  # IP asignada al Dobot
PORT_FEEDBACK = _require_env_int(
    "DOBOT_PORT_FEEDBACK"
)  # Puerto TCP de telemetría (habitualmente 29999 o 30004 según la interfaz)
SAMPLE_INTERVAL = _require_env_float(
    "DOBOT_SAMPLE_INTERVAL"
)  # Intervalo de captura en segundos (ej: 0.5s)

# ==============================================================================
# 3. MAPEO Y TRADUCCIÓN DEL ESTADO DEL ROBOT (robot_mode)
# ==============================================================================
# Mapeo oficial de códigos de estado de los robots Dobot serie CR
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


def get_robot_mode_str(mode_code):
  """Traduce el número entero de 'robot_mode' a una descripción legible.

  Si el código no existe en el diccionario, devuelve 'Desconocido'.
  """
  return ROBOT_MODE_MAP.get(int(mode_code), f"Desconocido ({mode_code})")


# ==============================================================================
# 4. GESTIÓN DEL ARCHIVO CSV
# ==============================================================================
def initialize_csv():
  """Inicializa el archivo CSV con la cabecera correspondiente.

  Si el archivo ya existe, mantiene los datos existentes sin sobrescribirlos.
  """
  try:
    # Modo 'x': Crea el archivo sólo si no existe
    with open(CSV_FILE, "x", newline="", encoding="utf-8") as f:
      writer = csv.writer(f)
      writer.writerow([
          "timestamp",  # Marca de tiempo en UTC
          "robot_mode",  # Código numérico original del estado
          "robot_mode_desc",  # Descripción en texto del estado
          # --- Posición y Orientación del Tool Center Point (TCP) ---
          "pos_x",
          "pos_y",
          "pos_z",
          "rot_rx",
          "rot_ry",
          "rot_rz",
          # --- Temperaturas de las 6 articulaciones (°C) ---
          "j1_temp",
          "j2_temp",
          "j3_temp",
          "j4_temp",
          "j5_temp",
          "j6_temp",
          # --- Consumo de corriente de las 6 articulaciones (A) ---
          "j1_current",
          "j2_current",
          "j3_current",
          "j4_current",
          "j5_current",
          "j6_current",
      ])
      print(f" Dataset creado correctamente en: '{CSV_FILE}'")
  except FileExistsError:
    print(f" Guardando datos en el dataset existente: '{CSV_FILE}'")


# ==============================================================================
# 5. DECODIFICACIÓN DE PAQUETES BINARIOS (DESPAQUETADO STRUCT)
# ==============================================================================
def parse_cr5a_feedback(data):
  """Extrae los valores de telemetría del paquete binario de 1440 bytes de Dobot.

  Retorna un diccionario estructurado o None si el paquete está incompleto.
  """
  if len(data) < 1440:
    return None

  try:
    # robot_mode: entero de 8 bytes (q / long long) en la posición offset 24..32
    robot_mode = struct.unpack("q", data[24:32])[0]

    # tool_vector: 6 doubles (6d) en la posición offset 440..488 (X, Y, Z, Rx, Ry, Rz)
    tool_vector = struct.unpack("6d", data[440:488])

    # joint_temps: 6 doubles (6d) en la posición offset 632..680 (°C)
    joint_temps = struct.unpack("6d", data[632:680])

    # joint_currents: 6 doubles (6d) en la posición offset 680..728 (A)
    joint_currents = struct.unpack("6d", data[680:728])

    return {
        "robot_mode": robot_mode,
        "robot_mode_desc": get_robot_mode_str(robot_mode),
        "tool_vector": [round(v, 2) for v in tool_vector],
        "joint_temps": [round(t, 1) for t in joint_temps],
        "joint_currents": [round(c, 3) for c in joint_currents],
    }
  except Exception as e:
    print(f" Error al despaquetar datos del robot: {e}")
    return None


# ==============================================================================
# 6. BUCLE PRINCIPAL DE CAPTURA Y ALMACENAMIENTO
# ==============================================================================
def main():
  initialize_csv()

  print(f" Intentando conectar con el Dobot en {DOBOT_IP}:{PORT_FEEDBACK}...")

  # Configuración del socket TCP client
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(5.0)

  try:
    sock.connect((DOBOT_IP, PORT_FEEDBACK))
    print(" Conexión establecida con el Dobot CR5A. Capturando telemetría...")
    print(" Presiona Ctrl + C en la terminal para detener el script.\n")

    last_sample_time = 0.0

    while True:
      # Recepción del bloque de datos binarios
      data = sock.recv(1440)
      current_time = time.time()

      # Control de frecuencia de muestreo
      if current_time - last_sample_time >= SAMPLE_INTERVAL:
        telemetry = parse_cr5a_feedback(data)

        if telemetry:
          timestamp = datetime.utcnow().isoformat()

          # Estructuración de la fila para guardar en CSV
          row = [
              timestamp,
              telemetry["robot_mode"],
              telemetry["robot_mode_desc"],  # Texto legible del estado
              *telemetry["tool_vector"],
              *telemetry["joint_temps"],
              *telemetry["joint_currents"],
          ]

          # Escritura continua (append)
          with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

          last_sample_time = current_time

          # Feedback por terminal
          print(
              f"[{timestamp[:19]}] Estado: {telemetry['robot_mode_desc']}"
              f" ({telemetry['robot_mode']}) | Pos XYZ:"
              f" {telemetry['tool_vector'][:3]} mm | Temps:"
              f" {telemetry['joint_temps']} °C | Corrientes:"
              f" {telemetry['joint_currents']} A"
          )

  except KeyboardInterrupt:
    print(
        "\n Captura finalizada por el usuario. Datos guardados de forma"
        " segura."
    )
  except socket.timeout:
    print(
        f"\n Timeout: No se pudo conectar a {DOBOT_IP}:{PORT_FEEDBACK}."
        " Revisa si el robot está encendido y accesible."
    )
  except Exception as e:
    print(f"\n Ocurrió un error en la conexión: {e}")
  finally:
    sock.close()


if __name__ == "__main__":
  main()