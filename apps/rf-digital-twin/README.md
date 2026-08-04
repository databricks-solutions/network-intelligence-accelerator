# RF Digital Twin

A Shiny app that renders Sionna RT coverage results for a 7-cell mmWave network
over the Arc de Triomphe (`etoile`) scene. Every render is cached in Lakebase
Postgres keyed by a hash of its configuration, so a ray-trace that costs minutes
on a GPU becomes a sub-second point lookup.

Deployment is handled by the bundle at the repo root — see the
**[deployment guide](../../docs/deployment.md)**. Design rationale is in
[architecture.md](../../docs/architecture.md). The
[preset gallery](../../README.md#preset-gallery) lists the configurations that
resolve to a cache hit.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Shiny UI + server. Non-blocking: a cache miss submits a job and returns, and a background poller picks the results up. |
| `app.yaml` | Runtime command. Env vars are injected by the bundle, not committed here. |
| `requirements.txt` | App runtime deps only — Sionna is job-side. |
| `defaults.py` | The 19 presets and the default 7-cell layout. |
| `lakebase_client.py` | Postgres connection, schema DDL, config hashing, reads/writes. |
| `sionna_compute.py` | The Sionna RT pipeline. Shared by the setup notebook and the render job. |
| `setup/setup_rf_digital_twin.py` | One-time setup: UC schema, Lakebase provisioning, preset precompute. |
| `jobs/sionna_compute_job.py` | The cache-miss render job the app triggers. |

## Lakebase tables

| Table | Purpose |
| --- | --- |
| `scene_configs` | One row per saved scene config + its sha256 `config_hash`. |
| `cell_configs` | 7 rows per `scene_configs.id` — per-TX position, look-at, power. |
| `cached_renders` | PNG bytea for scene / SINR / association / CDFs, plus KPI JSONB, keyed by `config_hash`. |
| `compute_jobs` | Tracking row per submitted render (PENDING / RUNNING / SUCCEEDED / FAILED). |

## Demo flow

1. Open the app — Config 1 (8×2 TX) auto-loads from the cache.
2. Walk the tabs: **Scene render → SINR association → Users → CDFs → KPIs**.
3. Edit the sidebar to match another row in the
   [preset gallery](../../README.md#preset-gallery) — flipping to 16×16 for
   Config 2 shows the densification story. Click **Render**: instant, from cache.
4. Then type something off-menu. The Status banner shows
   `Sionna job submitted (run_id=…)`. Keep clicking cached presets while it runs;
   results appear on their own when the job lands. **Cancel pending job** kills
   the cluster if you change your mind.

The Status tab shows the live `config_hash` — use it to confirm you're about to
hit the cache before clicking Render.

## Editing the cell layout

The canonical 7-cell layout lives in Unity Catalog at
`<catalog>.<schema>.cell_configs_default`, written by the setup notebook. Edit
that table to change the network, then re-run the setup job to re-render.

Changing the layout changes every config hash, so the hashes in the preset
gallery no longer apply — use the cheat sheet the setup job prints instead.

## Local development

The app only reads `cached_renders`, so Sionna isn't needed locally:

```bash
pip install -r requirements.txt
export LAKEBASE_INSTANCE=rf-digital-twin-pg PGDATABASE=rf_digital_twin
shiny run --reload app.py:app
```

`lakebase_client.py` resolves the host and mints a token through the Databricks
SDK, so a configured CLI profile is enough — no `PGPASSWORD` required.

> `--reload` is fine locally but **must not** appear in `app.yaml`. On Databricks
> Apps it kills the Shiny session websocket and every panel renders blank.
