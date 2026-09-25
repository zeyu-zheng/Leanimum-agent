# `leani`

!!! abstract "Overview"

    * `leani` is the interactive Leanimum-agent CLI.
    * It runs locally by default. Select another backend for untrusted code or
      use the [ReuF2F runner](reuf2f.md) for batch tasks.

## Usage

Run in a Lean project with its toolchain and dependencies installed:

```bash
leani -c mini.yaml -c environment.cwd=/absolute/path/to/lean-project \
  -t "Complete the proof of Example.target in Example.lean and check it."
```

## Command line options

Useful switches:

- `--help` - Show help and all options.
- `-t`, `--task` - Task to run; prompts when omitted.
- `-m`, `--model` - Model name; otherwise uses configuration or `LEANA_MODEL_NAME`.
- `-c`, `--config` - Config file or key-value override. The default is `mini.yaml`,
  or the file selected by `LEANA_MINI_CONFIG_PATH`.
- `-o`, `--output` - Trajectory file; defaults to `last_mini_run.traj.json` in the
  global config directory.
- `-y`, `--yolo` - Execute commands without confirmation.
- `-l`, `--cost-limit` - Cost limit; `0` disables it.

!!! note "Configuration overrides"

    If you pass `-c`, include a base config before overrides, for example
    `-c mini.yaml -c agent.step_limit=100`. See the
    [configuration guide](../advanced/yaml_configuration.md).

## Modes of operation

- `confirm` (`/c`) - Confirm or reject each proposed command.
- `yolo` (`/y`) - Execute proposed commands immediately.
- `human` (`/u`) - Type and execute commands yourself.

The default is `confirm`; use `-y` to start in `yolo`. Enter `/c`, `/y` or `/u`
when the agent is waiting for input to switch modes. `Ctrl+C` interrupts the
agent and returns control to you.

!!! warning "Local execution"

    Confirmation is not a filesystem sandbox. Use a suitable
    [environment](../advanced/environments.md) for untrusted commands.

See [output files](output_files.md) to inspect the saved trajectory. The global
config directory is printed at startup.

## Implementation

??? note "Default config"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/config/mini.yaml)

    ```yaml
    --8<-- "src/leanimum/config/mini.yaml"
    ```

??? note "Run script"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/run/mini.py)
    - [API reference](../reference/run/mini.md)

    ```python
    --8<-- "src/leanimum/run/mini.py"
    ```

??? note "Agent class"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/agents/interactive.py)
    - [API reference](../reference/agents/interactive.md)

    ```python
    --8<-- "src/leanimum/agents/interactive.py"
    ```

{% include-markdown "../_footer.md" %}
