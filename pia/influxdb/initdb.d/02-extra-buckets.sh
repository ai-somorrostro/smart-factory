#!/bin/bash
# Se ejecuta una vez durante la primera inicializacion (volumen vacio) a traves del punto de entrada de InfluxDB 2.x,
# DESPUeS de que se haya creado `DOCKER_INFLUXDB_INIT_BUCKET` (el bucket MiR).
# Crea los buckets de los robots restantes de forma idempotente.

# -e  para el script falle si algun comando falla
# -u  para el script falle si alguna variable no esta definida
# -o pipefail  para que falle si algun comando de un pipe falla
set -euo pipefail

# Configuracion de variables de entorno, son necesarias
TOKEN="${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN:?DOCKER_INFLUXDB_INIT_ADMIN_TOKEN is required}"
ORG="${INFLUXDB_ORG:?INFLUXDB_ORG is required}"
# Inizializamos la variable HOST con la URL de InfluxDB temporal, en este caso localhost:9999
HOST="http://localhost:9999"

# Buscamos los buckets de los robots, si existen no hacemos nada, si no existen los creamos
# Recordamos que /dev/null es un "agujero negro" donde se redirijen los mensajes de error para que no se muestren en pantalla
for BUCKET in "${INFLUXDB_BUCKET_PRINTER:?}" "${INFLUXDB_BUCKET_DOBOT:?}"; do
  if influx bucket list -n "$BUCKET" -o "$ORG" -t "$TOKEN" --host "$HOST" --hide-headers 2>/dev/null | grep -q .; then
    echo "initdb.d: bucket $BUCKET already exists, skipping"
  else
    influx bucket create -n "$BUCKET" -o "$ORG"  -t "$TOKEN" --host "$HOST"
    echo "initdb.d: bucket $BUCKET created"
  fi
done
