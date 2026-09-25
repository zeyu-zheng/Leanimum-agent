# ReuF2F

!!! abstract "Overview"

    * `leani-extra reuf2f` runs tasks in batch mode and saves Git patches.
    * [ReuF2F](https://github.com/zeyu-zheng/ReuF2F) builds the dataset
      (`test.jsonl`) and the shared image, and grades predictions independently.
    * One agent chooses a proof or refutation within one task budget.

## Usage

Pass the dataset built by `reuf2f dataset build`, one JSON record per task.

!!! tip "Quickstart"

    ```bash
    leani-extra reuf2f --subset /path/to/ReuF2F/test.jsonl \
      --filter '^gu2020hat$' -m YOUR_MODEL -o /tmp/reuf2f-run
    ```

To run several tasks in parallel:

```bash
leani-extra reuf2f --subset /path/to/ReuF2F/test.jsonl --slice 0:5 -w 2 \
  -m YOUR_MODEL -o /tmp/reuf2f-batch
```

Basic flags:

- `-o`, `--output` - Output directory (default: current directory).
- `-m`, `--model` - Model name.
- `-c`, `--config` - Config file or key-value override (default: `reuf2f.yaml`).
- `-w`, `--workers` - Number of parallel tasks (default: `1`).

Data selection flags:

- `--subset` - Path to the dataset, `test.jsonl` (required).
- `--filter` - Match instance IDs by regular expression.
- `--slice` - Python-style slice, such as `0:5`.
- `--shuffle` - Shuffle deterministically before filtering and slicing.
- `--redo-existing` - Rerun IDs already present in `preds.json`.

Advanced flags:

- `--environment-class` - Execution backend (default: `docker`).
- `--model-class` - Model adapter name or Python import path.

See `leani-extra reuf2f --help` for all options.

!!! warning "Configuration overrides"

    Passing `-c` replaces the default config selection. Include `-c reuf2f.yaml`
    before overrides, for example `-c reuf2f.yaml -c agent.step_limit=100`.

## Environment

Each task runs in the Docker image named by its record's `image` field, with
`/testbed` as the working directory; the image is built for `linux/amd64`, so run
on an x86_64 host. Build and validate it using the
[image guide](https://github.com/zeyu-zheng/ReuF2F/blob/main/docker/README.md).
To use Podman, pass `-c reuf2f.yaml -c environment.executable=podman`.

??? note "Task workspace"

    All tasks share one image, which has no task in it. Before the first model
    query, the runner copies the record's `challenge` into `/testbed` as
    `INSTANCE_ID.lean`, changes the Project root from `Main` to that module,
    builds it and commits the result, as a per-instance image would contain it.

    ```text
    /testbed/
      gu2020hat.lean
      lean-toolchain
      lakefile.toml
      lake-manifest.json
      .gitignore
      .git/
      .lake/
    ```

    The file keeps its original definitions and theorem, plus a `<theorem>_neg`
    target for the full negation. The task prompt names both.

### Budgets

| Setting | Default |
| --- | --- |
| `agent.step_limit` | `250` |
| `agent.cost_limit` | `$3` |
| `environment.timeout` | `1200` seconds per command |
| `agent.wall_time_limit_seconds` | `0` (no limit) |
| `environment.container_timeout` | `2h` (Docker only) |

These controls are independent. Removing the agent's wall-clock limit does not
remove the Docker container lifetime.

## Predictions and evaluation

The runner saves the agent's submitted diff in `preds.json`, plus trajectories
and logs. It does not collect unsubmitted edits or files omitted from the diff.
See [output files](output_files.md) for formats and failure/resume behavior.

Evaluate with the same dataset and a ReuF2F installation:

```bash
reuf2f eval /path/to/ReuF2F/test.jsonl -p /tmp/reuf2f-run/preds.json --run-id experiment
```

The evaluator starts a fresh container from the same image, replays the patch
and runs both Comparator checks. Either accepted direction resolves the task.
A `Submitted` status or successful `lake build` with `sorry` warnings is not
independent proof acceptance. See the
[evaluation guide](https://github.com/zeyu-zheng/ReuF2F/blob/main/docs/guides/evaluation.md)
for scoring and reports.

## FAQ

> Why is an instance skipped after I delete its trajectory?

Resume checks `preds.json`, not trajectory files. Use `--redo-existing` or remove
the intended prediction record. Keep each run tied to one dataset and config.

> Why does startup take a long time?

The engine may be pulling an image. Check `leanimum.log`; if necessary, increase
`environment.pull_timeout` (default: 120 seconds) through `-c`.

> Can I set global cost limits?

Use `LEANA_GLOBAL_CALL_LIMIT` and `LEANA_GLOBAL_COST_LIMIT`. See
[global configuration](../advanced/global_configuration.md).

> Can I run a startup command?

Set `run.env_startup_command` in a config. It is rendered with task variables and
runs before task preparation. A nonzero exit fails setup.

## Implementation

??? note "Default config"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/config/benchmarks/reuf2f.yaml)

    ```yaml
    --8<-- "src/leanimum/config/benchmarks/reuf2f.yaml"
    ```

??? note "Batch runner"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/run/benchmarks/reuf2f.py)
    - [API reference](../reference/run/reuf2f.md)

    ```python
    --8<-- "src/leanimum/run/benchmarks/reuf2f.py"
    ```

{% include-markdown "../_footer.md" %}
