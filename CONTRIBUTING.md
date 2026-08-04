# Contributing

Thanks for your interest in contributing. This project is maintained by the
Databricks Field Engineering team on a best-effort basis — see [NOTICE.md](NOTICE.md).

## Reporting bugs and requesting features

Open a [GitHub issue](https://github.com/databricks-solutions/network-intelligence-accelerator/issues).
For bugs, please include:

- Repro steps, and observed vs expected behaviour.
- Deploy target (`databricks.yml` target name, cloud, GPU instance type).
- Relevant logs: `databricks apps logs rf-digital-twin-<target> -p <profile>`,
  or the run output from the failing job.

For security vulnerabilities follow [SECURITY.md](SECURITY.md) instead — don't
file them as public issues.

## Pull requests

1. Open an issue describing the change first, so we can align on direction before
   you spend time on a PR.
2. Fork the repo and create a feature branch.
3. Match the style of the surrounding code: Python 3.11+, type hints, and
   `from __future__ import annotations` where the existing modules use it.
4. Verify the bundle still validates: `databricks bundle validate -t dev -p <profile>`.
5. If you touched the app, check it still starts locally — see the local
   development section in [docs/deployment.md](docs/deployment.md).
6. Open the PR with a clear description and link the issue.

## Things to know before changing code

- **`compute_config_hash` is load-bearing.** It's the cache key. Any change to
  the hashed field list, the canonicalisation, or the default cell layout
  invalidates every cached render and every hash in the preset gallery table in
  the README. If you change it, say so explicitly in the PR.
- **Adding a preset is cheap.** Add it to `PRESETS` in `defaults.py` *and* to the
  `PRESETS` list in the setup notebook, then re-run the setup job. It skips
  presets that are already cached, so only the new one renders.
- **The setup notebook duplicates `sionna_compute.py` on purpose.** It has to run
  standalone on a cluster before the app source is importable. If you change the
  render pipeline, change both.
- **Don't add `--reload` to `app.yaml`.** It kills the Shiny session websocket on
  Databricks Apps.

## Security and hygiene

This is a public repo. Before submitting a PR:

- Don't commit workspace URLs, catalog or schema names, job IDs, Lakebase
  hostnames, customer names, or `.env` files. Everything workspace-specific
  belongs in a `databricks.yml` variable with a generic default.
- Don't commit notebook outputs — they often embed workspace paths and data.
- If GitHub push protection blocks your push, treat it as a real finding and
  rotate the credential rather than working around it.

## License

By contributing you agree that your contributions will be licensed under the
[Databricks License](LICENSE.md) covering this repo.
