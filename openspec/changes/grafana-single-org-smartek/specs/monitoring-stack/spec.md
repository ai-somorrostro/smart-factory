# Spec Delta

## ADDED Requirements

### Requirement: Grafana exposes a single Smartek organization
The system SHALL expose exactly one Grafana organization named `Smartek` with id `1`, and SHALL NOT leave a visible organization named `Main Org.` after the stack is ready.

#### Scenario: Fresh Grafana volume converges on Smartek
- **WHEN** the stack starts with an empty Grafana volume and a valid `.env`
- **THEN** the Grafana organizations API lists exactly one organization named `Smartek` with id `1`

#### Scenario: Existing Grafana volume converges on Smartek
- **WHEN** the stack restarts with a previously initialized Grafana volume that contains `Main Org.`
- **THEN** the Grafana organizations API lists exactly one organization named `Smartek` with id `1` and no organization named `Main Org.`

### Requirement: No additional Grafana organizations appear
The system SHALL route every user to the `Smartek` organization (id `1`) and SHALL create no additional Grafana organizations on restarts or when new users sign in.

#### Scenario: Restart creates nothing new
- **WHEN** the user runs `docker compose down` (without `-v` on the Grafana volume) followed by `docker compose up -d`
- **THEN** the Grafana organizations API still lists exactly one organization

#### Scenario: New user lands in Smartek
- **WHEN** a new user signs in to Grafana
- **THEN** that user belongs to the `Smartek` organization and no new organization is created for them

### Requirement: Provisioned observability keeps working in Smartek
The system SHALL keep the single InfluxDB datasource and all file-provisioned dashboards available inside the `Smartek` organization, and SHALL NOT modify the InfluxDB organization, buckets, tokens, or volumes as part of this change.

#### Scenario: Dashboards query through Smartek
- **WHEN** a user opens the provisioned dashboards in the `Smartek` organization
- **THEN** panels querying `mir`, `bambu_maintenance`, and `dobot` through the single InfluxDB datasource return data

#### Scenario: InfluxDB layout is untouched
- **WHEN** this change is applied and the stack restarts
- **THEN** the InfluxDB organization, bucket set, and API token remain exactly as configured before, and existing time-series points stay queryable
