# Spec Delta

## Purpose

Estandarizar cómo se configuran y ejecutan las capturas SBD a CSV para que cualquier máquina del taller reproduzca el mismo entorno sin secretos hardcodeados.

## ADDED Requirements

### Requirement: Captura Dobot lee configuración desde .env

El sistema SHALL obtener todos los parámetros de red, muestreo y destino CSV de la captura Dobot desde el fichero `sbd/.env`, sin contener IPs, puertos, intervalos ni rutas de salida hardcodeados en el código.

#### Scenario: Arranque con .env completo

- **WHEN** existe `sbd/.env` con las claves Dobot definidas y se ejecuta la captura Dobot
- **THEN** la captura conecta al host y puerto configurados, muestrea al intervalo configurado y añade filas al CSV configurado bajo `sbd/datos/`

#### Scenario: Variable Dobot ausente

- **WHEN** falta alguna clave Dobot obligatoria en `sbd/.env`
- **THEN** la captura Dobot no intenta conectar y termina con un mensaje de error que nombra la variable ausente

### Requirement: Captura Bambu multi-impresora lee configuración desde .env

El sistema SHALL obtener la lista de impresoras Bambu (nombre, IP, número de serie y código de acceso por impresora) y el destino CSV desde `sbd/.env`, sin contener IPs, series ni códigos de acceso hardcodeados en el código.

#### Scenario: Arranque con dos impresoras configuradas

- **WHEN** `sbd/.env` define dos impresoras con sus cuatro campos cada una y se ejecuta la captura Bambu
- **THEN** la captura abre una conexión MQTT por impresora configurada y añade filas de ambas al CSV configurado con las columnas actuales (`timestamp, printer_name, serial_number, gcode_state, mc_print_stage, tray_type, mc_percent, layer_num, total_layer_num, nozzle_temp, bed_temp`)

#### Scenario: Credencial de impresora ausente

- **WHEN** falta el número de serie o el código de acceso de una impresora en `sbd/.env`
- **THEN** la captura Bambu no intenta conectar con esa impresora y muestra un mensaje de error que nombra la variable ausente

### Requirement: Formato CSV de capturas sin cambios

El sistema SHALL mantener el esquema y destino actual de los CSV: cabeceras existentes, modo append sin borrar datos previos y creación automática de `sbd/datos/` si no existe.

#### Scenario: CSV existente

- **WHEN** el CSV de destino ya existe en `sbd/datos/`
- **THEN** la captura añade filas al final sin modificar ni borrar las filas previas ni la cabecera

#### Scenario: Carpeta de datos ausente

- **WHEN** `sbd/datos/` no existe al arrancar una captura
- **THEN** el sistema crea la carpeta y el CSV con su cabecera antes de la primera fila de datos

### Requirement: Entorno Python reproducible para sbd

El sistema SHALL declarar todas las dependencias de captura en `sbd/requirements.txt` de forma que una instalación limpia en un único entorno virtual `sbd/.venv` permita ejecutar ambos scripts sin instalaciones manuales adicionales.

#### Scenario: Instalación limpia

- **WHEN** se crea `sbd/.venv`, se activa y se instala `sbd/requirements.txt`
- **THEN** ambos scripts de captura arrancan sin errores de importación ausente (incluido el cliente MQTT)

### Requirement: Secretos y artefactos fuera del control de versiones

El sistema SHALL proveer un `sbd/.env.example` con los nombres de todas las variables y valores ficticios, y el repositorio SHALL ignorar `sbd/.env`, `sbd/.venv/` y los CSV generados en `sbd/datos/`.

#### Scenario: Clonado por un compañero

- **WHEN** una persona clona el repositorio y copia `sbd/.env.example` a `sbd/.env` rellenando valores reales
- **THEN** puede ejecutar las capturas sin modificar código y sin que sus secretos queden registrados en git
