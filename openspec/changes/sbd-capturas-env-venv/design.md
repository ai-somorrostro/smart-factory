# Design

## Context

Ver `proposal.md` (Why). Estado observado: `sbd/scripts/capturar_dobot.py` hardcodea `DOBOT_IP`, `PORT_FEEDBACK=30004`, `SAMPLE_INTERVAL=0.5` y resuelve `sbd/datos/dataset_dobot_cr5a.csv` por ruta relativa al script; `sbd/scripts/capturar_impresora.py` hardcodea una lista `PRINTERS` de 2 entradas con `name/ip/sn/access_code` y escribe `dataset_bambu_multi_printer.csv` con `threading + csv_lock`. Solo los notebooks usan `python-dotenv` (`load_dotenv(find_dotenv)`); los scripts no. `sbd/requirements.txt` declara `pandas`, `influxdb-client`, `python-dotenv` pero no `paho-mqtt`. No existe ningún venv y `.gitignore` está vacío. Python del sistema es 3.13.

## Goals / Non-Goals

**Goals:**

- Un único `.venv` en `sbd/.venv` válido para capturas y notebooks.
- Cero secretos/IPs en código; todo sale de `sbd/.env` con fallo claro si falta algo.
- Instalación reproducible desde `requirements.txt` en máquina limpia.

**Non-Goals:**

- No se cambia el esquema de columnas de ningún CSV ni el protocolo Dobot TCP / Bambu MQTT.
- No se añade N dinámico de impresoras con formato complejo si 2 fijas bastan (ver Decisiones).
- No se migran los notebooks más allá de seguir funcionando con las mismas claves Influx.
- No se rota ni se versiona ningún secreto real.

## Decisions

1. **Carga de `.env` por ruta anclada al script, no por cwd.**
   Cada script resuelve `sbd/.env` como `../.env` desde su propio `__file__` y llama a `load_dotenv` con esa ruta explícita. Alternativa descartada: `find_dotenv()` dependiente del cwd (es lo que usan los notebooks y falla si se lanza el script desde otra carpeta). Rationale: las capturas se lanzan desde terminales y servicios con cwd impredecible.
2. **Variables indexadas para 2 impresoras fijas (`BAMBU_H2D_1_*`, `BAMBU_H2D_2_*`).**
   Alternativa considerada: cadena compuesta `BAMBU_PRINTERS="nombre,ip,sn,code;..."`. Se descarta por legibilidad y validación campo a campo (el escenario de credencial ausente exige nombrar la variable exacta). Si en el futuro hay N impresoras, se migra a conteo + índice sin romper las 2 actuales. Claves Dobot: `DOBOT_IP`, `DOBOT_PORT_FEEDBACK`, `DOBOT_SAMPLE_INTERVAL`; destinos: `DOBOT_CSV_FILE`, `BAMBU_CSV_FILE` (nombres de fichero, la carpeta sigue siendo `sbd/datos/`). Formato canónico `CLAVE=valor` sin espacios ni comillas; las claves Influx existentes se conservan tal cual.
3. **Validación fail-fast al arranque con mensaje que nombra la variable.**
   Helper mínimo que exige cada clave obligatoria (conversión de tipos para puerto/intervalo) y aborta antes de abrir sockets/MQTT. Alternativa descartada: valores por defecto silenciosos para red/credenciales (ocultan errores de configuración en el taller).
4. **`sbd/.venv` único + `requirements.txt` completado.**
   `python3 -m venv sbd/.venv`, activación e `pip install -r sbd/requirements.txt`; se añade `paho-mqtt>=2.0` (compatible con el uso actual de `mqtt.Client` + `tls_set`) manteniendo `pandas`, `influxdb-client`, `python-dotenv`. Alternativa descartada: venvs separados por script (duplica mantenimiento sin beneficio, comparten dotenv/pandas).
5. **`.env.example` + `.gitignore` (`.venv/`, `.env`, `datos/*.csv`, `__pycache__/`).**
   `.env.example` lista todas las claves con valores ficticios; nunca contiene secretos reales. Los CSV ya generados se quedan en disco pero dejan de versionarse.

## Risks / Trade-offs

- [Riesgo] `.env` actual usa `CLAVE = "valor"` con espacios/comillas; normalizar a `CLAVE=valor` puede confundir al copiar → Mitigación: `.env.example` canónico + nota de migración en `tasks.md`, `python-dotenv` acepta ambos durante la transición.
- [Riesgo] `datetime.utcnow()` deprecado en 3.13 y `sock.recv(1440)` que asume paquete completo → Mitigación: fuera de alcance de este change salvo que bloquee; se registran como deuda, no se tocan aquí para no expandir el diff.
- [Riesgo] Alguien ejecuta con el Python del sistema en vez del venv y reporta "falta paho-mqtt" → Mitigación: los scripts no auto-actvan venvs; la guía de ejecución exige activar `sbd/.venv` primero.
- [Trade-off] 2 impresoras fijas vs N dinámico: se elige simplicidad ahora; el coste de migrar después es bajo (añadir `BAMBU_PRINTER_COUNT`).

## Migration Plan

1. Añadir claves nuevas a `sbd/.env` (valores reales solo en local) y crear `sbd/.env.example` ficticio.
2. Actualizar scripts para leer `.env` con fail-fast; verificar que con `.env` completo el CSV sigue en el mismo path y formato.
3. Completar `requirements.txt`, crear `sbd/.venv`, reinstalar y humo de importaciones + arranque que valide config.
4. Aplicar `.gitignore`, `git rm --cached` de secretos/CSVs si ya estaban versionados, rollback = revert del commit (ningún dato de `datos/` se borra del disco).

## Open Questions

- Ninguna que cambie specs, enfoque o tareas. Deuda conocida fuera de alcance: reemplazo de `utcnow()` y reensamblado de tramas TCP parciales del Dobot.
