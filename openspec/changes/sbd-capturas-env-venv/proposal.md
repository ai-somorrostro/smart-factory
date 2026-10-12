# Proposal

## Why

Los scripts de captura `sbd/scripts/capturar_dobot.py` y `sbd/scripts/capturar_impresora.py` ya escriben CSV en `sbd/datos/`, pero llevan IPs, puertos, intervalos, series y `access_code` hardcodeados, no leen `sbd/.env`, `requirements.txt` está incompleto (`paho-mqtt` sin declarar) y no existe ningún `.venv` para `sbd/`. Esto filtra secretos si se sube a git y rompe la reproducibilidad en otra máquina del taller.

## What Changes

- Los dos scripts de captura leen toda su configuración desde `sbd/.env` vía `python-dotenv` (IPs, puerto, intervalo, nombres/series/códigos de impresoras, rutas CSV). Sin valores hardcodeados de red, credenciales o muestreo.
- `sbd/requirements.txt` declara todas las dependencias de captura (`paho-mqtt` más lo ya existente) con versiones mínimas que funcionen en Python 3.13.
- Documentado un único entorno virtual `sbd/.venv` para todo `sbd/` (capturas + notebooks): creación, activación e instalación.
- Protegidos secretos y artefactos generados vía `.gitignore` (`.venv/`, `.env`, `datos/*.csv`) más un `sbd/.env.example` sin valores reales.
- El CSV sigue siendo el mismo formato y destino (`sbd/datos/dataset_dobot_cr5a.csv` y `dataset_bambu_multi_printer.csv`); no cambia el esquema de columnas.

## Capabilities

### New Capabilities

- `sbd/capture-config`: configuración de capturas SBD vía `.env` y entorno Python reproducible (qué variables existen, cómo fallan los scripts si faltan, qué dependencias y venv se usan).

### Modified Capabilities

- Ninguna (no hay specs previas; `openspec list --specs` devuelve vacío).

## Impact

- Afectado: `sbd/scripts/capturar_dobot.py`, `sbd/scripts/capturar_impresora.py`, `sbd/requirements.txt`, `sbd/.env` (nuevas claves), nuevo `sbd/.env.example`, `.gitignore`, docs de setup del venv.
- No cambia el formato de los CSV ni el protocolo contra Dobot (TCP 30004) / Bambu (MQTT 8883); solo de dónde sale la configuración.
- Riesgo de migración: quien ya ejecuta los scripts con valores hardcodeados deberá crear/actualizar su `sbd/.env` una vez; los scripts deben fallar con mensaje claro si falta una variable.
