# Design

## Context

See proposal.md (Why) and `specs/monitoring-stack/spec.md` for required behavior.

Current state (observed in repo):
- `pia/docker-compose.yml` runs Grafana 13.2.2 with `grafana-data` named volume, `GF_SECURITY_ADMIN_*` + SMTP from `.env`, and file provisioning for one InfluxDB datasource + `Verify buckets` dashboard (no `org_id` set, so both land in org id=1).
- No `GF_USERS_*` org-lockdown vars are set today.
- Grafana auto-creates `Main Org. (id=1)` on first boot with an empty volume; there is no `GF_ORG_NAME`-style variable to choose the initial name. Rename must happen after boot via API/UI.
- `smart-factory_grafana-data` volume already exists (Grafana up), `influxdb2-data` is a separate volume and must not be touched.

## Goals / Non-Goals

**Goals:**
- Converge org id=1 to name `Smartek` on both fresh and existing volumes, idempotently across restarts.
- Lock assignment so all users land in id=1 and UI/API creation of extra orgs is disabled for non-server-admins.

**Non-Goals:**
- No hard block against a server admin deliberately creating an org via API (Grafana does not offer one); policy + config is the boundary.
- No changes to dashboard queries, bucket names, or InfluxDB provisioning.

## Decisions

### D1: Rename via Grafana HTTP API (`PUT /api/org`), not via SQLite edits
- Approach: after Grafana is healthy, authenticate as admin (credentials from the same `.env` values Grafana itself uses) and `PUT /api/org {"name":"Smartek"}` against the current org context, retried until healthy/200. No-op when the name is already `Smartek`.
- Alternative considered: editing `grafana.db` (`org` table) with Grafana stopped. Rejected: unsupported, fragile across versions, and breaks the "next `up` just works" goal because ids/foreign keys (`datasource.org_id`, dashboards) must be hand-repaired.
- Alternative considered: manual one-time rename from UI with no automation. Rejected as the steady state (it satisfies the spec once, but a future fresh volume silently regresses to `Main Org.`).

### D2: Org lockdown via `GF_USERS_*` env on the Grafana service
- Set `GF_USERS_ALLOW_ORG_CREATE=false`, `GF_USERS_AUTO_ASSIGN_ORG=true`, `GF_USERS_AUTO_ASSIGN_ORG_ID=1` (plus keep existing admin vars). Defaults already lean this way, but pinning makes the single-org posture explicit and reviewable in compose instead of implicit.
- Alternative considered: relying on operator discipline alone. Rejected: a single OAuth/signup or misclick recreates the multi-org state this change removes.

### D3: Camino A migration — deliberate `grafana-data` reset, InfluxDB volumes untouched
- The supported path to a clean single-org state is `down` + remove **only** the Grafana volume + `up`, then let rename + provisioning reconverge. Datasource and `Verify buckets` reappear from `bda/grafana/` with no manual import.
- Explicitly out: `down -v` without a volume filter (would also drop `influxdb2-data`), and deleting/recreating orgs from the UI to "fix ids" on the live volume.

## Risks / Trade-offs

- [Grafana recreates `Main Org.` for an instant on every fresh volume] → Mitigation: rename step runs on every start (idempotent), so the steady state observed by the spec (exactly one org named `Smartek`) still holds after readiness.
- [Admin password from env only seeds the first boot; later `.env` changes do not rotate the DB password] → Mitigation: rename job reads the same credential source as the running DB (document the "password changed after first boot" caveat in migration notes); failure surfaces as 401 in the rename step, not as silent skip.
- [Reset drops UI-made state not stored in `bda/grafana/`] → Mitigation: migration plan inventories manual state first; provisioned assets are verified after `up` before declaring done.
- [Dodot sin dashboard provisionado] → Mitigation: fuera de alcance; el bucket `dobot` existe en InfluxDB y el datasource único puede consultarlo, solo falta el dashboard.

## Migration Plan

1. Inventory UI-made Grafana state worth keeping (users, alert rules, manual dashboards/keys); export or accept loss.
2. Apply compose/config changes, then `down` + remove only the Grafana volume + `up`.
3. Wait for Grafana healthy, run idempotent rename to `Smartek`, verify org list shows exactly one org.
4. Verify datasource + `Verify buckets` panels return data; verify InfluxDB org/buckets/points unchanged.
5. Rollback: config-only revert + (if needed) restore of the pre-change `grafana-data` volume backup; InfluxDB needs no rollback.

## Open Questions

- None that change specs, approach, or tasks. Only runtime detail (exact rename trigger: compose `depends_on`-style waiter vs small one-shot service) is left to implementation within the approach above.
