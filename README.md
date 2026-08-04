# Network Intelligence Accelerator

**An interactive RF digital twin for cellular network planning — [NVIDIA Sionna RT](https://nvlabs.github.io/sionna/rt/index.html) ray tracing on Databricks.**

✅ &nbsp;Ray-trace real 3D city geometry with NVIDIA Sionna RT on GPU compute.
<br>✅ &nbsp;Flip between **19 precomputed network configurations in under a second** — a Lakebase Postgres cache turns a minutes-long ray-trace into a point lookup.
<br>✅ &nbsp;Edit antenna arrays, frequency, bandwidth, power, polarization, and ray-tracing depth from a Shiny sidebar.
<br>✅ &nbsp;Off-menu configurations fall through to a **live GPU render** that writes back to the cache — no dead ends.
<br>✅ &nbsp;See SINR coverage maps, user-to-tower association, SINR/RSS CDFs, and KPI summaries per configuration.
<br>✅ &nbsp;Deploy the whole stack — Lakebase, GPU jobs, and both apps — with one `databricks bundle deploy`.

<!-- TODO: replace with the demo GIF (see docs/media.md for what to capture) -->
<!-- ![RF Digital Twin demo](images/rf-digital-twin-demo.gif) -->

---

## Why this exists

A Sionna ray-trace takes minutes on a GPU, which makes it useless for
interactive exploration — an RF engineer can't explore a design space one
five-minute render at a time.

Precomputing a gallery of configurations into a Lakebase Postgres cache turns
those minutes into a sub-second lookup, so designs become browsable in real
time. Anything off-menu still falls through to a live GPU render, so the cache
is an accelerator rather than a cage.

The demo scene is the Arc de Triomphe (`etoile`) with a 7-cell mmWave network.

## What's in here

| Component | What it is |
| --- | --- |
| [`apps/rf-digital-twin/`](apps/rf-digital-twin/) | **The digital twin.** Shiny app over a Lakebase Postgres render cache. Sub-second cache hits; off-menu configs ray-trace live on a GPU job. |
| [`apps/rf-agent-showcase/`](apps/rf-agent-showcase/) | **Chapter 0.** A self-running showcase that opens the story — "the network that fixes itself." Static front-end, no cluster or database needed. |
| [`notebooks/explore/`](notebooks/explore/) | The original exploratory notebook: two configurations, run once, compared by hand. Start here to understand the physics before the app abstracts it. |

Deploy the showcase first if you're presenting: it sets up *why* the twin
matters, then the twin lets you drive it by hand.

## Quickstart

Prerequisites, GPU requirements, and troubleshooting are in the
[deployment guide](docs/deployment.md). The short version:

```bash
# 1. Deploy the Lakebase instance, both Sionna jobs, and both apps.
databricks bundle deploy -t dev -p <profile>

# 2. Populate the render cache (~30-50 min on g5.xlarge, renders 19 presets).
databricks bundle run setup_rf_digital_twin -t dev -p <profile>

# 3. Grant the app's service principal Postgres access — run the grant cell in
#    section 11 of apps/rf-digital-twin/setup/setup_rf_digital_twin.py.
#    The setup job created the tables as *you*; the app connects as its own SP.

# 4. Open it.
databricks apps get rf-digital-twin-dev -p <profile> --output json | jq -r .url
```

Step 3 is the one thing the bundle can't do for you. Skip it and the app will
connect to Lakebase and then fail to read anything.

> **Sionna RT requires NVIDIA OptiX**, which ships only with `g4dn` / `g5` / `g6`
> instances on AWS. CPU and ARM nodes fail with `libnvoptix.so.1 could not be
> loaded`. The bundle defaults to `g5.xlarge`.

## Architecture

A one-time setup pass populates the cache, the app reads it on the hot path, and
off-menu configs fall through to a GPU job that writes back:

```
  setup job (once, GPU)  ──renders 19 presets──▶  ┌──────────────────┐
                                                  │ LAKEBASE POSTGRES│
  Shiny app ──hit: <1s point lookup────────────▶  │ cached_renders   │
      │                                           │ keyed by sha256  │
      └── miss ──▶ GPU job ──writes back────────▶  └──────────────────┘
```

Full diagram, the reasoning behind the hash-keyed cache, why Lakebase rather than
Delta, and the token-minting auth model: [docs/architecture.md](docs/architecture.md).

## Preset gallery

The setup job precomputes **19 configurations** into the cache — sweeps over
antenna densification, frequency band, antenna pattern, polarization, TX power,
bandwidth, and ray-tracing depth. Each group holds everything else steady and
varies one knob, so you can compare like for like.

Typing any of them into the sidebar loads in under a second. The full table of
sidebar values and their config hashes: **[docs/presets.md](docs/presets.md)**.

## Repo layout

```
.
├── databricks.yml                  # Asset Bundle — apps, jobs, Lakebase
├── docs/
│   ├── deployment.md               # full deployment guide + troubleshooting
│   └── architecture.md             # diagram and design rationale
├── apps/
│   ├── rf-digital-twin/            # the digital twin (Lakebase cache)
│   │   ├── app.py                  # Shiny UI + non-blocking server
│   │   ├── app.yaml                # runtime config (env injected by bundle)
│   │   ├── requirements.txt        # app deps — no Sionna, that's job-side
│   │   ├── defaults.py             # 19-preset gallery + 7-cell layout
│   │   ├── lakebase_client.py      # Postgres connection, hashing, queries
│   │   ├── sionna_compute.py       # Sionna RT pipeline (setup + job share it)
│   │   ├── setup/                  # one-time setup + preset precompute
│   │   └── jobs/                   # cache-miss render job
│   └── rf-agent-showcase/          # Chapter 0 — static showcase
│       ├── index.html / app.js / style.css
│       ├── towers.json             # baked cell-site locations
│       └── app.yaml
└── notebooks/
    └── explore/
        ├── simulation_RT_light.ipynb    # original single-shot notebook
        └── images/
```

## Further reading

- [Sionna RT documentation](https://nvlabs.github.io/sionna/rt/index.html) — official ray-tracing docs and tutorials.
- [Lakebase docs](https://docs.databricks.com/aws/en/oltp/) — managed Postgres on Databricks.
- [Databricks Apps docs](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/) — running Shiny / FastAPI / etc. apps.
- [Databricks Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/) — the deployment mechanism used here.
- Medium series this project is built on:
  - [Part I — "NVIDIA's AI-Native Digital Twin on Databricks"](https://medium.com/@razibayati20/nvidias-ai-native-digital-twin-on-databricks-true-ai-democratization-for-telecom-bdb81ef87b70)
  - [Part II](https://medium.com/@razibayati20/nvidias-ai-native-digital-twin-on-databricks-true-ai-democratization-for-telecom-ii-065938ca112c)

## Support

See [NOTICE.md](NOTICE.md) — this is a Databricks Solutions accelerator, not an
officially supported product. Open a GitHub issue and the team will look on a
best-effort basis.
