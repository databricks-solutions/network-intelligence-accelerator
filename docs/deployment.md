# Deployment guide

Everything is deployed by the Databricks Asset Bundle at the repo root
([`databricks.yml`](../databricks.yml)). The bundle creates the Lakebase
instance, both Sionna jobs, and both apps.

There is exactly one step the bundle can't do for you — granting the app's
service principal Postgres access to tables your user owns (step 4).

## Prerequisites

| Requirement | Why |
| --- | --- |
| [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/install) v0.230+ | Bundle support. `databricks --version` to check. |
| A configured profile or `DATABRICKS_HOST`/`DATABRICKS_TOKEN` | Auth. `databricks auth login --host <workspace-url>` sets one up. |
| Permission to create a Lakebase database instance | The render cache. Workspaces cap this at 10 instances — delete an unused one if you're at the limit. |
| Permission to create GPU job clusters | Sionna RT needs NVIDIA OptiX. |
| `USE CATALOG` + `CREATE SCHEMA` on your target catalog | The setup job writes the default cell layout to `<catalog>.<schema>.cell_configs_default`. |

### GPU instance requirement

Sionna RT calls NVIDIA OptiX, which ships only with `g4dn` / `g5` / `g6`
instances on AWS. **CPU and ARM (Graviton) nodes fail** with
`libnvoptix.so.1 could not be loaded`.

The bundle defaults to `g5.xlarge` (1× A10G, 24 GB VRAM). `g4dn.xlarge` (T4)
also works and costs less, but ray-traces roughly 2–3× slower.

## 1. Validate

```bash
databricks bundle validate -t dev -p <profile>
```

Override any variable at this point if the defaults don't suit your workspace:

```bash
databricks bundle validate -t dev -p <profile> \
  --var="catalog=my_catalog" \
  --var="gpu_node_type=g4dn.xlarge"
```

Available variables (with defaults) are documented at the top of
[`databricks.yml`](../databricks.yml): `catalog` (`main`), `schema_name`
(`sionna_rf_data`), `lakebase_instance` (`rf-digital-twin-pg`),
`lakebase_database` (`rf_digital_twin`), `lakebase_capacity` (`CU_1`),
`gpu_node_type` (`g5.xlarge`), `spark_version` (`16.4.x-scala2.13`), and
`samples_per_tx` (`10000000`).

## 2. Deploy

```bash
databricks bundle deploy -t dev -p <profile>
```

This creates the Lakebase instance and database, both jobs, and both apps. The
apps will start but the digital twin has an **empty cache** until step 3 runs —
expect it to report that Config 1 isn't cached yet.

## 3. Populate the cache

```bash
databricks bundle run setup_rf_digital_twin -t dev -p <profile>
```

Wall-clock **~30–50 minutes** on `g5.xlarge` for a cold run: it renders all 19
presets through Sionna RT. The job is idempotent — re-running only renders
presets whose config hash isn't already cached, so adding presets later is cheap.

The job also prints a **cheat sheet** mapping each preset's sidebar values to its
config hash. Worth keeping open if you're demoing; it tells you what to type to
guarantee a cache hit.

## 4. Grant the app service principal Postgres access

The setup job created the Lakebase tables **as you**. The app connects as its own
service principal, which can reach the database but not read tables owned by
another role. Until you fix this the app will connect and then fail to read.

Open `apps/rf-digital-twin/setup/setup_rf_digital_twin.py` in the workspace and
run the grant cell in **section 11** (`lb_connect()` is already defined there).

> The grants in that cell are to `PUBLIC` for demo simplicity — every Postgres
> role on the instance gets read/write. For anything beyond a demo, replace
> `PUBLIC` with the app service principal's UUID and grant least privilege.

## 5. Open the apps

```bash
databricks apps list -p <profile>
```

Or straight to a URL:

```bash
databricks apps get rf-digital-twin-dev -p <profile> --output json | jq -r .url
```

The digital twin auto-loads Config 1 from the cache on first paint. The showcase
app needs no setup at all — it's a static front-end.

## Verifying a cache hit

The **Status** tab shows the live `config_hash`. When your sidebar values match a
row in the [preset gallery](../README.md#preset-gallery), the first 12 characters
of that hash equal the gallery's hash prefix. That's your confirmation you're
about to hit the cache rather than trigger a live GPU render.

## Local development

The digital twin app only *reads* `cached_renders`, so Sionna isn't needed
locally — just a reachable Lakebase instance.

```bash
cd apps/rf-digital-twin
pip install -r requirements.txt
export LAKEBASE_INSTANCE=rf-digital-twin-pg PGDATABASE=rf_digital_twin
# lakebase_client resolves the host and mints a token via the Databricks SDK,
# so a configured CLI profile is enough — no PGPASSWORD needed.
shiny run --reload app.py:app
```

The showcase app is static:

```bash
cd apps/rf-agent-showcase && python -m http.server 8000
```

It needs internet access for the CARTO basemap tiles and the MapLibre / font CDNs.

## Teardown

```bash
databricks bundle destroy -t dev -p <profile>
```

`bundle destroy` removes the apps and jobs. Check whether the Lakebase instance
went with them — it bills hourly while it exists (~$0.30/hr at `CU_1`):

```bash
databricks database list-database-instances -p <profile>
```

## Troubleshooting

### Deployment

- **`libnvoptix.so.1 could not be loaded`** — the job landed on a non-GPU or ARM
  node. Set `--var="gpu_node_type=g5.xlarge"` (or another `g4dn`/`g5`/`g6`).
- **`'WorkspaceClient' object has no attribute 'database'`** — the app base image
  ships `databricks-sdk` 0.33.0; the Lakebase API namespace needs `>=0.55.0`.
  `requirements.txt` pins this already, so redeploy from a clean checkout.
- **Lakebase instance quota** — workspaces cap Lakebase at 10 instances. Delete
  an unused one, or point `--var="lakebase_instance=..."` at an existing one.
- **`QUOTA_EXCEEDED` on app create** — each Databricks App creates an OAuth app
  integration, and accounts cap these at 10,000. An admin needs to clean up.
- **`mode: production` requires `root_path`** — already set in the `prod` target;
  if you added your own target, copy that block.

### Runtime

- **`fe_sendauth: no password supplied`** — `lakebase_client._generate_password()`
  couldn't mint an OAuth token. Confirm `LAKEBASE_INSTANCE` is set on the app and
  the app's service principal has `CAN_USE` on the Lakebase instance.
- **App loads but every render triggers a live job** — the cache is empty or was
  populated against a different Lakebase database. Re-run step 3 and confirm
  `lakebase_database` matches between the setup job and the app.
- **`Properties of ITU material 'marble' are not defined for this frequency`** —
  a frequency below 1 GHz was requested. The etoile scene's ITU `marble` material
  is only defined for 1–100 GHz; keep frequencies at 1.8 GHz or above.
- **Blank panels in the Shiny app** — something added `--reload` to the `shiny
  run` command. On Databricks Apps that kills the session websocket. Remove it.
