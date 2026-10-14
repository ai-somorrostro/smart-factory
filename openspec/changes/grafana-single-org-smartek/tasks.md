# Tasks

## 1. Fijar organización única en la configuración de Grafana

- [ ] 1.1 Añadir `GF_USERS_ALLOW_ORG_CREATE=false`, `GF_USERS_AUTO_ASSIGN_ORG=true` y `GF_USERS_AUTO_ASSIGN_ORG_ID=1` al servicio `grafana` en `pia/docker-compose.yml` y documentarlas en `pia/.env.example`, y verificar con `docker compose config` que las variables renderizan desde `.env`
- [ ] 1.2 Verificar que ningún otro fichero (provisioning, dashboards, `.env`) crea organizaciones o fija `org_id` distinto de 1 mediante búsqueda en `pia/` y `bda/grafana/`, y que el datasource sigue sin `orgId` explícito para heredar la org 1

## 2. Renombrado idempotente de la org 1 a Smartek

- [ ] 2.1 Añadir el mecanismo de renombrado (espera a Grafana healthy + `PUT /api/org {"name":"Smartek"}` con credenciales admin del `.env`, no-op si el nombre ya es `Smartek`), y verificar que el script/fichero existe y que una segunda ejecución no cambia nada
- [ ] 2.2 Integrar el renombrado en el arranque (orden tras Grafana healthy, reintentos hasta 200) sin tocar los servicios `influxdb`, `nodered` ni capturadores, y verificar con un rearranque que el paso corre solo y no altera otros servicios

## 3. Migración Camino A y aceptación

- [ ] 3.1 Inventariar estado manual de Grafana (usuarios, alertas, dashboards no provisionados, keys) y respaldar el volumen `grafana-data`, y verificar que existe copia restorable antes de borrar nada
- [ ] 3.2 Borrar solo el volumen de Grafana, levantar el stack y ejecutar el renombrado, y verificar vía API (`/api/orgs`) que existe exactamente una organización llamada `Smartek` con id 1 y ninguna `Main Org.`
- [ ] 3.3 Verificar aceptación: el datasource único responde, los dashboards provisionados (`INFO_MIRS`, `INFO_MIR_RESPONSABLES`, `Info_Bambu`) devuelven datos de `mir` y `bambu_maintenance`, un `down/up` no crea orgs nuevas, y la org/buckets/puntos de InfluxDB siguen intactos
