# Tasks

## 1. Base de configuración y dependencias

- [x] 1.1 Crear `sbd/.env.example` con todas las claves (Dobot, Bambu x2, CSV, Influx existentes) y valores ficticios, y verificar que no contiene ningún secreto real por inspección del fichero
- [x] 1.2 Añadir las claves nuevas a `sbd/.env` local en formato `CLAVE=valor` y verificar cargándolas con `python3 -c "from dotenv import load_dotenv; load_dotenv('sbd/.env'); ..."` que todas se resuelven
- [x] 1.3 Completar `sbd/requirements.txt` con `paho-mqtt>=2.0` y verificar con `pip install --dry-run -r sbd/requirements.txt` o instalación real que no hay conflictos en Python 3.13
- [x] 1.4 Actualizar `.gitignore` para ignorar `sbd/.venv/`, `sbd/.env`, `sbd/datos/*.csv` y `__pycache__/` y verificar con `git status --porcelain` que esos paths ya no aparecen como cambios

## 2. Captura Dobot vía .env

- [x] 2.1 Sustituir `DOBOT_IP`, `PORT_FEEDBACK`, `SAMPLE_INTERVAL` y nombre de CSV por lectura de `.env` anclada al script (`../.env` desde `__file__`) con fail-fast que nombra la variable ausente, y verificar que sin hardcodes queda `grep -rn "192.168.15.10" sbd/scripts/capturar_dobot.py` vacío
- [x] 2.2 Verificar arranque con `.env` completo: ejecutar la validación de config y comprobar que resuelve host/puerto/intervalo/CSV esperado sin abrir conexión real (o con conexión si el robot está disponible)
- [x] 2.3 Verificar escenario de variable ausente: vaciar temporalmente una clave Dobot y comprobar que el script aborta con el mensaje que nombra esa variable

## 3. Captura Bambu vía .env

- [x] 3.1 Sustituir la lista `PRINTERS` hardcodeada por construcción desde `BAMBU_H2D_1_*` / `BAMBU_H2D_2_*` más `BAMBU_CSV_FILE` con fail-fast por campo, y verificar que `grep -rn "192.168.15.32\|86bf9c6a\|bb7eb044" sbd/scripts/capturar_impresora.py` queda vacío
- [x] 3.2 Verificar arranque con dos impresoras configuradas: comprobar que se construyen dos clientes MQTT con los topic `device/<sn>/report` correctos sin publicar nada
- [x] 3.3 Verificar escenario de credencial ausente: vaciar temporalmente un `SN`/`CODE` y comprobar que esa impresora no conecta y el error nombra la variable

## 4. Venv único e integración

- [x] 4.1 Crear `sbd/.venv` con `python3 -m venv sbd/.venv`, activarlo e instalar `sbd/requirements.txt`, y verificar con `sbd/.venv/bin/python -c "import paho.mqtt.client, dotenv, pandas, influxdb_client; print('ok')"` que no hay importaciones ausentes
- [x] 4.2 Verificar integración CSV sin cambios: con `.venv` activo y `.env` completo, ejecutar ambas capturas brevemente (o su validación) y comprobar que los CSV en `sbd/datos/` conservan cabeceras y hacen append sin borrar filas previas
- [x] 4.3 Documentar en `sbd` (README o cabecera de scripts) los comandos de crear/activar venv e instalar requirements, y verificar copiando cada comando documentado que se ejecuta tal cual está escrito
