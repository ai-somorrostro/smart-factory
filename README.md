# Smartek
Somos una consultoría de datos especializada en la carga y gestión de datos de robots.
Recopilamos, validamos y centralizamos la información de telemetría y operación de flotas robóticas en un único repositorio fiable.
Este proyecto convierte esos datos en una base lista para análisis, monitorización y toma de decisiones.

# Requisitos

    Docker Engine.
    Docker Compose v2.
    Git, si se clona el proyecto desde un repositorio.

Para regenerar el dataset desde los ficheros originales también se necesita Python 3.12 o superior y las dependencias de requirements.txt.

## Despliegue

El despliegue se realiza desde la raíz del repositorio con el `docker-compose.yml`
principal. El archivo Compose construye las imágenes de Node-RED y de los
capturadores, y descarga las imágenes de InfluxDB, Grafana y del MCP de Grafana.

```bash
git clone <URL_DEL_REPOSITORIO>
cd smart-factory
```

### 1. Preparar la configuración

No se debe modificar ni compartir el `.env.example` con credenciales reales.
Crear el archivo local `.env` y completar los valores de los robots, tokens,
contraseñas y configuración SMTP:

```bash
cp .env.example .env
```

Como mínimo, hay que revisar estas variables antes de arrancar:

- `INFLUXDB_INIT_PASSWORD` e `INFLUXDB_TOKEN`.
- `GRAFANA_ORG_NAME`, `GF_SECURITY_ADMIN_PASSWORD` y las variables SMTP.
- `MIR1_TOKEN` y `MIR2_TOKEN`.
- `DOBOT_IP`, `DOBOT_PORT_FEEDBACK` y `DOBOT_CSV_FILE`.
- IP, número de serie y código de cada impresora `BAMBU_H2D_*`.

Los valores de `DOBOT_CSV_FILE` y `BAMBU_CSV_FILE` son nombres de archivo,
no rutas absolutas. Los capturadores los guardan en `sbd/datos`, que se monta
en los contenedores como `/app/datos`.

### 2. Validar y arrancar el stack

Antes del primer arranque, validar la interpolación de variables y la
configuración de Compose:

```bash
docker compose --env-file .env config --quiet
```

Construir las imágenes locales y arrancar todos los servicios:

```bash
docker compose --env-file .env up -d --build
```

El orden de arranque es el siguiente:

1. InfluxDB se inicializa y debe superar su healthcheck.
2. Node-RED y Grafana arrancan después de InfluxDB.
3. `grafana-init-org` renombra la organización y genera el token de servicio
   para el MCP.
4. `mcp-grafana` arranca después de completar correctamente la inicialización
   de Grafana.
5. Los capturadores se construyen desde `sbd/DockerFile` y comienzan a enviar
   datos cuando los robots están disponibles.

No es necesario ejecutar `docker pull` manualmente: Compose descarga las
imágenes declaradas cuando son necesarias.

### 3. Comprobar el despliegue

```bash
docker compose ps
docker compose logs -f
```

Servicios publicados:

| Servicio | Imagen o build | Acceso desde el host |
|---|---|---|
| InfluxDB | `influxdb:2.9.1` | `http://localhost:${INFLUXDB_PORT:-8086}` |
| Node-RED | `./bda/nodered/DockerFile` | `http://localhost:${NODE_RED_PORT:-1880}` |
| Grafana | `grafana/grafana:13.2.2` | `http://localhost:${GRAFANA_PORT:-3000}` |
| MCP Grafana | `grafana/mcp-grafana:latest` | `http://127.0.0.1:8000` |

El MCP de Grafana solo se publica en `127.0.0.1`. No queda expuesto
directamente a otras máquinas de la red.

### Detener y actualizar

Detener los contenedores sin eliminar los datos persistentes:

```bash
docker compose down
```

Después de modificar el Compose, los Dockerfile o las dependencias, reconstruir
las imágenes:

```bash
docker compose up -d --build
```

Los volúmenes `influxdb2-data`, `grafana-data` y `mcp-secrets` se conservan al
ejecutar `docker compose down`. No usar `docker compose down -v` salvo que se
quiera borrar la configuración y los datos persistentes, incluido el estado
inicializado de InfluxDB.
