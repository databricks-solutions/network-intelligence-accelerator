# Network Intelligence Accelerator

An RF digital twin for cellular network planning, built on Databricks with
[NVIDIA Sionna RT](https://nvlabs.github.io/sionna/rt/index.html).

Edit a cell-network configuration in a sidebar and immediately see the resulting
scene render, SINR coverage map, user-to-tower association, and SINR/RSS CDFs.
The demo scene is the Arc de Triomphe (`etoile`) with a 7-cell mmWave network.

The problem this solves: a Sionna ray-trace takes minutes on a GPU, which makes
it useless for interactive exploration. Precomputing a gallery of configurations
into a Lakebase Postgres cache turns those minutes into a sub-second lookup, so
an RF engineer can flip between designs in real time — and anything off-menu
still falls through to a live GPU render.

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

These 19 sidebar combinations resolve to a **cached render** (instant load).
Anything outside this list triggers a live Sionna job.

> **Reading the tables:** every column is a sidebar input. To reach a row, type
> **all** of its values — a partial match (e.g. 20 MHz bandwidth without also
> setting the TX array) hashes to something new and falls through to the live
> job. Values not called out keep their Config 1 defaults (28 GHz, 100 MHz,
> tr38901, V, 44 dBm, max_depth 5, RX 2×2).

Each group holds everything else steady and varies one knob, so you can compare
like for like.

### A — Antenna densification

Only the TX array changes.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `4d99ce0ad66c` | **2 × 2** | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `1947611f5ab1` | **4 × 4** | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `07934c589015` | **8 × 2** *(= Config 1)* | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `9dc696f16498` | **8 × 8** | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `7d40e2f4cf67` | **16 × 16** *(= Config 2)* | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `1f83af551835` | **32 × 8** | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | 5 |

### B — Frequency band ladder

TX held at 8 × 2. Frequency and bandwidth change together, scaled to what each
band realistically deploys with.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `c97b934ed651` | 8 × 2 | **1.8 GHz** | **20 MHz** | tr38901 | V | 44 dBm | 5 |
| `8e58d2b3aa3b` | 8 × 2 | **2.6 GHz** | **20 MHz** | tr38901 | V | 44 dBm | 5 |
| `2b4207dac650` | 8 × 2 | **3.5 GHz** | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `07934c589015` | 8 × 2 | **28 GHz** *(= Config 1)* | 100 MHz | tr38901 | V | 44 dBm | 5 |
| `411bcd0ac9fc` | 8 × 2 | **39 GHz** | **400 MHz** | tr38901 | V | 44 dBm | 5 |

The low end of this ladder is 1.8 GHz, not 700 MHz: the etoile scene's ITU
`marble` material is only defined for 1–100 GHz.

### C — Antenna pattern

TX held at 16 × 16.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `7d40e2f4cf67` | 16 × 16 | 28 GHz | 100 MHz | **tr38901** *(= Config 2)* | V | 44 dBm | 5 |
| `74315cd0c5a0` | 16 × 16 | 28 GHz | 100 MHz | **iso** | V | 44 dBm | 5 |
| `4d5194498776` | 16 × 16 | 28 GHz | 100 MHz | **dipole** | V | 44 dBm | 5 |

### D — Polarization

TX held at 16 × 16, tr38901 pattern.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `7d40e2f4cf67` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | **V** *(= Config 2)* | 44 dBm | 5 |
| `1dcfea9eb314` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | **VH** | 44 dBm | 5 |

### E — TX power

TX held at 16 × 16. Power applied uniformly across all 7 cells.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `4d3b2585ea77` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | V | **38 dBm** | 5 |
| `7d40e2f4cf67` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | V | **44 dBm** *(= Config 2)* | 5 |
| `c9960aa40101` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | V | **50 dBm** | 5 |

### F — Bandwidth

TX held at 16 × 16.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1b0bae11e49c` | 16 × 16 | 28 GHz | **20 MHz** | tr38901 | V | 44 dBm | 5 |
| `7d40e2f4cf67` | 16 × 16 | 28 GHz | **100 MHz** *(= Config 2)* | tr38901 | V | 44 dBm | 5 |
| `d7d1abe8d6b0` | 16 × 16 | 28 GHz | **400 MHz** | tr38901 | V | 44 dBm | 5 |

### G — Ray tracing fidelity

TX held at 16 × 16. Only `max_depth` (reflection bounces) changes.

| Hash prefix | TX array | Freq | BW | Pattern | Pol | TX power | max_depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1bfc66c11279` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | **3** |
| `7d40e2f4cf67` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | **5** *(= Config 2)* |
| `74c31dcc5ea6` | 16 × 16 | 28 GHz | 100 MHz | tr38901 | V | 44 dBm | **8** |

> The hashes above were generated against the default 7-cell layout. If you edit
> `cell_configs_default` in Unity Catalog, every hash changes — re-run the setup
> job and use the cheat sheet it prints instead of this table.

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
