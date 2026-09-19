# Quick start

## Installation

Install from source with Python 3.10 or newer:

```bash
git clone https://github.com/zeyu-zheng/Leanimum-agent.git
cd Leanimum-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
leani-extra config setup
```

See [model setup](models/quickstart.md) for provider configuration and
[development setup](contributing.md#development-setup) for tests and documentation.

## Run a Lean task

Use a project with its toolchain and dependencies already installed:

```bash
leani -c mini.yaml -c environment.cwd=/absolute/path/to/lean-project \
  -t "Complete the proof of Example.target in Example.lean and check it."
```

!!! note "Configuration"

    `mini.yaml` uses native bash tool calls. Use `mini_textbased.yaml` for command
    code blocks. If you pass `-c`, include a full configuration before overrides.

!!! warning "Local execution"

    The CLI confirms commands by default. `--yolo` disables confirmation, not
    filesystem access. Local execution is not sandboxed; use a suitable
    [backend](advanced/environments.md) for untrusted code.

## Run ReuF2F

Start from a prepared ReuF2F task release, then run:

```bash
leani-extra reuf2f --subset /tmp/reuf2f-tasks --slice 0:1 \
  -m YOUR_MODEL -o /tmp/reuf2f-run
```

The default image is `zeyuzhenghub/lean4:v4.33.0` on `linux/amd64`. Image build and
independent evaluation belong to ReuF2F. Follow the [benchmark guide](usage/reuf2f.md)
to prepare the image, generate predictions and score them.

## Next steps

- [CLI usage](usage/mini.md)
- [Configuration](advanced/yaml_configuration.md)
- [Trajectories and outputs](usage/output_files.md)
- [Python bindings](usage/python_bindings.md)

{% include-markdown "_footer.md" %}
