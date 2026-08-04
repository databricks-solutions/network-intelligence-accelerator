# Chapter 0 — RF Agent Showcase

A self-running showcase that opens the story: **"the network that fixes itself."**
It's the prequel to the [digital twin](../rf-digital-twin/README.md) — where that
app lets you drive the twin by hand, Chapter 0 shows *why* it matters.

Pure static front-end (HTML/CSS/JS + a baked `towers.json`). No cluster,
database, or resource bindings.

## The narrative (auto-plays)

1. **The network at rest** — a bird's-eye of Seattle with every real cell site.
2. **Alarm** — a new 14-story building goes up downtown; UEs on Tower #978 (5G NR)
   start reporting poor data experience.
3. **Zoom** — the camera flies down to the affected tower; its coverage sector and
   the new building (casting an NLOS shadow) are drawn on the map.
4. **Agent on the case** — the console streams its reasoning: it correlates UE
   telemetry with the 3D scene, reads the current radio config + KPIs, then
   ray-traces candidate configs with Sionna RT and scores them.
5. **Recommendation** — a card animates in with the config diff (tilt / azimuth /
   power) and the *why*, with before→after SINR p10, RSS p50, and edge-user KPIs.

## What's real vs. illustrative

Worth being precise about this if you're presenting it:

- **Real:** every tower location, type (LTE / NR / GSM / UMTS), and the total
  count, baked into `towers.json` from public cell-site data filtered to central
  Seattle. Hero site is tower #978, a downtown 5G NR cell.
- **Illustrative:** the alarm, the radio configs, the KPIs, the candidate scores,
  and the building geometry. All scripted in `SCN` at the top of `app.js` — this
  is a narrative, not a live agent.

For a real ray-trace you can drive yourself, that's the
[digital twin](../rf-digital-twin/README.md).

## Run locally

```bash
python -m http.server 8000
# open http://localhost:8000
```

Needs internet access for the CARTO dark basemap tiles and the MapLibre / font CDNs.

## Deploy

Handled by the bundle at the repo root as `rf-agent-showcase-<target>`:

```bash
databricks bundle deploy -t dev -p <profile>
```

See the [deployment guide](../../docs/deployment.md).

## Refresh the tower data

`towers.json` has the shape `{ hero_id, count, towers: [{id, type, r, lat, lon}] }`.
To regenerate it from a cell-tower table in Unity Catalog:

```sql
SELECT tower_id, tower_type, coverage_radius_m,
       round(latitude, 5)  AS lat,
       round(longitude, 5) AS lon
FROM <catalog>.<schema>.cell_towers
WHERE latitude  BETWEEN 47.49 AND 47.74
  AND longitude BETWEEN -122.46 AND -122.22;
```

Reshape into the structure above and overwrite the file. `hero_id` must match an
`id` present in `towers` — `app.js` falls back to the first tower if it doesn't,
which will put the alarm in the wrong place.
