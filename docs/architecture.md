# Architecture

Three stages: a one-time setup pass populates the cache, the app reads it on the
hot path, and off-menu configs fall through to a GPU job that writes back.

```
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  ① ONE-TIME SETUP — populates the cache                                 │
   │                                                                         │
   │     job: setup_rf_digital_twin  (once, GPU cluster, ~30–50 min)         │
   │     ─ creates the UC schema, Lakebase instance + database, tables       │
   │     ─ renders the 19 presets through Sionna RT                          │
   │     ─ writes scene render + SINR map + association + CDFs + KPIs        │
   └────────────────────────────────────────┬────────────────────────────────┘
                                            ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  LAKEBASE POSTGRES                                                      │
   │  ─ scene_configs       one row per saved scene-level config + hash      │
   │  ─ cell_configs        7 TX rows per scene config                       │
   │  ─ cached_renders      PNG bytea + KPI JSONB keyed by config_hash       │
   │  ─ compute_jobs        run-id and status for live re-renders            │
   └────────────┬─────────────────────────────────────────┬──────────────────┘
                ▲ reads (cache hit, psycopg)              ▲ writes (on done)
                │                                         │
   ┌────────────┴───────────────────┐  cache miss   ┌─────┴─────────────────┐
   │  ② RUNTIME APP                 │ ── Jobs API ─▶│  ③ LIVE RE-RENDER     │
   │  Shiny on Databricks Apps      │               │  job: sionna_compute  │
   │  ─ user types sidebar values   │               │  Sionna RT on a       │
   │  ─ Render → sha256(config)     │               │  g5.xlarge GPU job    │
   │  ─ hit: load cache in <1 s     │               │  cluster              │
   │  ─ miss: submit job, poll cache│               │  ~5–8 min cold,       │
   │  ─ Cancel button kills the run │               │  ~2–3 min warm        │
   └────────────────────────────────┘               └───────────────────────┘
```

## The two paths

**Cache hit (the demo path).** Sidebar values → `config_hash` → Postgres row →
tabs render in under a second. This is what makes the app demo-able: a
ray-trace that takes minutes becomes an instant flip between configurations.

**Cache miss (the live-edit path).** An off-menu config submits the
`sionna_compute` job and returns immediately. A background reactive poller checks
Lakebase every 10 seconds; when the job writes its results, the tabs update on
their own. The user can keep clicking cached presets while it runs, and the
Cancel button kills the cluster.

## Why the cache is keyed by hash

`config_hash` is a sha256 over the canonicalised scene config plus the ordered
cell list (`lakebase_client.compute_config_hash`). Because it's deterministic,
two users who type the same values hit the same cached row — the cache works
across sessions and across users without any coordination.

It also makes setup idempotent: re-running the setup job only renders presets
whose hash isn't already in `cached_renders`, so adding a preset later costs one
render rather than nineteen.

The flip side is that the hash covers *every* field. A partial match — 20 MHz
bandwidth without also setting the TX array the preset used — hashes to
something new and falls through to the live job. The Status tab shows the live
hash so you can confirm a match before clicking Render.

## Why Lakebase rather than Delta

The hot path is a single-row primary-key lookup returning a few hundred KB of
PNG bytes, on every user interaction. That's an OLTP access pattern: Postgres
answers in tens of milliseconds from an always-warm instance, with no cluster to
spin up. Delta is the right home for the *source* data (the canonical cell
layout lives in Unity Catalog, and the setup job reads it from there), but not
for interactive point lookups behind a UI.

## Authentication

No `PGPASSWORD` anywhere. The Lakebase resource binding populates `PGHOST`,
`PGPORT`, `PGDATABASE`, and `PGUSER` in the app container and provisions a
Postgres role for the app's service principal. `lakebase_client.py` mints a
fresh OAuth token at runtime via the Databricks SDK
(`generate_database_credential`) and caches it for 45 minutes against a ~1 hour
token lifetime.

The `sionna_compute` job gets no resource binding, so the app passes
`lakebase_instance` and `lakebase_database` as job parameters; the job resolves
the host through the SDK and mints its own token the same way.

One consequence worth knowing: the setup job creates the tables **as your user**,
so the app's service-principal role can connect but can't read them until you
grant access. That's step 4 of the [deployment guide](deployment.md).
