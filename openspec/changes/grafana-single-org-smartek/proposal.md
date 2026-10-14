# Proposal

## Why

Grafana siempre arranca con su org interna `Main Org. (id=1)` aunque el usuario no cree ninguna. El stack ya tiene la org de InfluxDB (`smartek`) correcta y no se quiere tocar; falta que el lado Grafana quede fijado en una única organización `Smartek` y que `Main Org.` no vuelva a aparecer en siguientes arranques.

## What Changes

- Al levantar el stack con volumen de Grafana nuevo o existente, la única organización visible de Grafana es `Smartek` (id=1).
- Se bloquea la creación de organizaciones adicionales desde la configuración para que todos los usuarios y todo lo aprovisionado caigan siempre en id=1.
- El datasource InfluxDB y los dashboards provisionados siguen funcionando en la org `Smartek` sin cambios de queries.
- Camino de migración elegido (Camino A): se permite borrar solo el volumen `grafana-data` y rearrancar limpio; no se edita `grafana.db` a mano ni se cambian ids por SQL.
- InfluxDB queda explícitamente fuera de alcance: no se toca org, buckets, tokens, URL ni volúmenes de InfluxDB.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- `monitoring-stack`: añade el requisito de organización única de Grafana (`Smartek`, id=1) y el candado de no-creación de orgs, manteniendo el resto del contrato del stack (puertos, volúmenes, datasource único Flux, secretos por `.env`).

## Impact

- Afecta solo a Grafana: `pia/docker-compose.yml` (variables `GF_USERS_*`), posible script/init de renombrado de org 1, y documentación de rearranque.
- No afecta a `influxdb` (servicio, volumen `influxdb2-data`, `initdb.d`), ni a Node-RED, ni a los capturadores `sbd`.
- Operativo: un rearranque con borrado de `grafana-data` pierde solo estado manual hecho por UI y no guardado en `bda/grafana/` (usuarios extra, alertas manuales, dashboards no provisionados); lo provisionado se regenera solo.
