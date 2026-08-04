# Databricks notebook source
# MAGIC %md
# MAGIC # Sionna RT compute job
# MAGIC
# MAGIC Triggered by the RF Digital Twin app when a user submits a custom
# MAGIC configuration that is not in the Lakebase cache.
# MAGIC
# MAGIC Parameters (notebook widgets):
# MAGIC
# MAGIC | name              | description                                  |
# MAGIC | ----------------- | -------------------------------------------- |
# MAGIC | config_hash       | sha256 hash to write back into the cache row |
# MAGIC | scene_json        | JSON of scene-level config                   |
# MAGIC | cells_json        | JSON of cell list                            |
# MAGIC | lakebase_instance | Lakebase instance holding the cache          |
# MAGIC | lakebase_database | Database inside that instance                |
# MAGIC
# MAGIC The job must run on a GPU cluster with `drjit`, `mitsuba`, and `sionna-rt`
# MAGIC available. The bundle installs these as task libraries, so the `%pip`
# MAGIC cell below is only needed when running this notebook by hand.

# COMMAND ----------

# MAGIC %pip install drjit mitsuba sionna-rt psycopg[binary]

# COMMAND ----------

import json
import os
import sys

dbutils.widgets.text("config_hash", "")
dbutils.widgets.text("scene_json", "")
dbutils.widgets.text("cells_json", "")
dbutils.widgets.text("lakebase_instance", "rf-digital-twin-pg")
dbutils.widgets.text("lakebase_database", "rf_digital_twin")

config_hash = dbutils.widgets.get("config_hash")
scene_cfg = json.loads(dbutils.widgets.get("scene_json"))
cells = json.loads(dbutils.widgets.get("cells_json"))

# lakebase_client reads these to resolve the host and mint an OAuth token.
# Unlike the app, a job gets no resource binding, so pass them through the env.
os.environ["LAKEBASE_INSTANCE"] = dbutils.widgets.get("lakebase_instance")
os.environ["PGDATABASE"] = dbutils.widgets.get("lakebase_database")

assert config_hash, "config_hash widget is empty"
print(f"config_hash = {config_hash}")
print(f"scene_cfg   = {scene_cfg}")
print(f"cells       = {len(cells)} TXs")

# COMMAND ----------

# The app modules (lakebase_client, sionna_compute) live one level up, in
# apps/rf-digital-twin/. Resolve that from the notebook's own path rather than
# os.getcwd(), which isn't the notebook directory on every runtime.
_nb_path = (
    dbutils.notebook.entry_point.getDbutils()
    .notebook().getContext().notebookPath().get()
)
APP_DIR = f"/Workspace{os.path.dirname(os.path.dirname(_nb_path))}"
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
print(f"APP_DIR = {APP_DIR}")

import lakebase_client as lb
from sionna_compute import run_simulation

# COMMAND ----------

try:
    lb.set_job_status(config_hash, "RUNNING")
    results = run_simulation(scene_cfg, cells)
    lb.write_render(config_hash, results)
    lb.set_job_status(config_hash, "SUCCEEDED")
    print(f"Done in {results['compute_seconds']:.1f}s")
except Exception as e:
    lb.set_job_status(config_hash, "FAILED", error_message=str(e))
    raise
