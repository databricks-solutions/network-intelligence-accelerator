# Preset gallery

The setup job precomputes 19 configurations into the Lakebase cache. Typing any
of them into the app sidebar resolves to a **cached render** that loads in under
a second; anything else falls through to a live GPU ray-trace.

See the [architecture doc](architecture.md#why-the-cache-is-keyed-by-hash) for how
the hash keying works, and the [deployment guide](deployment.md) for how to
populate the cache.

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
