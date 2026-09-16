# ReuF2F

!!! abstract "Overview"

    * `leani-extra reuf2f` runs tasks in batch mode and saves Git patches.
    * [ReuF2F](https://github.com/zeyu-zheng/ReuF2F) prepares task releases, builds
      the shared image and grades predictions independently.
    * One agent chooses a proof or refutation within one task budget.

## Usage

Export tasks with `reuf2f prepare-tasks /tmp/reuf2f-tasks` in the benchmark
checkout. Pass the release directory, not the checkout, to the runner.

!!! tip "Quickstart"

    ```bash
    leani-extra reuf2f --subset /tmp/reuf2f-tasks \
      --filter '^berger-modified-egz$' -m YOUR_MODEL -o /tmp/reuf2f-run
    ```

To run several tasks in parallel:

```bash
leani-extra reuf2f --subset /tmp/reuf2f-tasks --slice 0:5 -w 2 \
  -m YOUR_MODEL -o /tmp/reuf2f-batch
```

Basic flags:

- `-o`, `--output` - Output directory (default: current directory).
- `-m`, `--model` - Model name.
- `-c`, `--config` - Config file or key-value override (default: `reuf2f.yaml`).
- `-w`, `--workers` - Number of parallel tasks (default: `1`).

Data selection flags:

- `--subset` - Prepared release directory (required).
- `--filter` - Match instance IDs by regular expression.
- `--slice` - Python-style slice, such as `0:5`.
- `--shuffle` - Shuffle deterministically before filtering and slicing.
- `--redo-existing` - Rerun IDs already present in `preds.json`.

Advanced flags:

- `--environment-class` - Execution backend: `docker` or `local`.
- `--model-class` - Model adapter name or Python import path.

See `leani-extra reuf2f --help` for all options. Keep the output and release in
separate directories; neither can contain the other.

!!! warning "Configuration overrides"

    Passing `-c` replaces the default config selection. Include `-c reuf2f.yaml`
    before overrides, for example `-c reuf2f.yaml -c agent.step_limit=100`.

## Environment

=== "Docker (default)"

    The default image is `zeyuzhenghub/lean4:v4.33.0` on `linux/amd64`, with
    `/testbed` as the working directory. Build and validate it using the
    [image guide](https://github.com/zeyu-zheng/ReuF2F/blob/main/docker/README.md).

    To select an image or use Podman:

    ```bash
    leani-extra reuf2f --subset /tmp/reuf2f-tasks --slice 0:1 \
      -c reuf2f.yaml -c environment.image=IMAGE_OR_DIGEST \
      -c environment.executable=podman -m YOUR_MODEL -o /tmp/reuf2f-run
    ```

    Keep `linux/amd64` when changing Docker run arguments. Updating the checkout
    does not rebuild or publish the image.

=== "Local"

    Local execution needs a prepared Lean project and explicit selection:

    ```bash
    leani-extra reuf2f --subset /tmp/reuf2f-tasks --slice 0:1 \
      --environment-class local \
      -c reuf2f.yaml -c environment.cwd=/path/to/prepared-lean-project \
      -m YOUR_MODEL -o /tmp/reuf2f-local-run
    ```

    The project needs the image-style `lakefile.toml` (Project root `Main`),
    matching toolchain/lockfile, cached `.lake/packages`, and Lean on PATH.
    Each attempt uses `OUTPUT/INSTANCE_ID/workspace-*` with linked dependencies,
    not the prepared project or release itself. Attempt workspaces are retained.

!!! warning "Local execution is not sandboxed"

    Local workspaces share the host and dependency cache. Use a disposable
    environment without secrets. Docker failures never fall back to local.
    The generic `leani` CLI supports additional [backends](../advanced/environments.md).

??? note "Task workspace"

    Before the first model query, the runner checks the release files, toolchain
    and locked dependencies. It changes the Project root from `Main` to the task
    module, adds the task source, builds it and creates a local Git commit.
    A mismatch fails setup rather than updating dependencies.

    ```text
    /testbed/
      berger2019modified.lean
      lean-toolchain
      lakefile.toml
      lake-manifest.json
      .gitignore
      .git/
      .lake/
    ```

    The file keeps its original name, definitions and theorem, plus a
    `<theorem>_neg` target for the full negation. The task prompt names both.
    The unchosen proof may remain `sorry`; the chosen proof must not depend on
    any admission. Other benchmark tasks are not injected.

### Budgets

| Setting | Default |
| --- | --- |
| `agent.step_limit` | `250` |
| `agent.cost_limit` | `$3` |
| `environment.timeout` | `1200` seconds per command |
| `agent.wall_time_limit_seconds` | `0` (no limit) |
| `environment.container_timeout` | `3h` (Docker only) |

These controls are independent. Removing the agent's wall-clock limit does not
remove the Docker container lifetime.

## Predictions and evaluation

The runner saves the agent's submitted diff in `preds.json`, plus trajectories
and logs. It does not collect unsubmitted edits or files omitted from the diff.
See [output files](output_files.md) for formats and failure/resume behavior.

Evaluate with the original release and a ReuF2F installation:

```bash
reuf2f eval /tmp/reuf2f-tasks -p /tmp/reuf2f-run/preds.json --run-id experiment
```

The evaluator starts a fresh container from the same image, replays the patch
and runs both Comparator checks. Either accepted direction resolves the task.
A `Submitted` status or successful `lake build` with `sorry` warnings is not
independent proof acceptance. See the
[evaluation guide](https://github.com/zeyu-zheng/ReuF2F/blob/main/docs/COMPARATOR_PILOT.md)
for scoring and reports.

## FAQ

> Why is an instance skipped after I delete its trajectory?

Resume checks `preds.json`, not trajectory files. Use `--redo-existing` or remove
the intended prediction record. Keep each run tied to one release and config.

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
