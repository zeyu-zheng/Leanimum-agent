# Leanimum-agent

A minimal bash-only agent for Lean proofs and programs. It reads and edits files,
searches Mathlib, and iterates on compiler feedback through one shell tool.

## Installation

Use Python 3.10 or newer and install from source:

```bash
git clone https://github.com/zeyu-zheng/Leanimum-agent.git
cd Leanimum-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
leani-extra config setup
```

Use `leani` for interactive tasks and `leani-extra` for utilities and batch runs.
The Python package is `leanimum`. See [configuration](docs/advanced/global_configuration.md)
for `LEANA_*` settings.

## Usage

Run in a prepared Lean project:

```bash
leani -c mini.yaml -c environment.cwd=/absolute/path/to/lean-project \
  -t "Complete the proof of Example.target in Example.lean and check it."
```

Commands require confirmation by default. Use `mini_textbased.yaml` instead of
`mini.yaml` for text command blocks. See [CLI usage](docs/usage/mini.md) for options.

Local execution is not sandboxed. Choose a suitable
[environment](docs/advanced/environments.md) for untrusted commands.

## ReuF2F

Run the built-in benchmark on the dataset built by ReuF2F:

```bash
leani-extra reuf2f --subset /path/to/ReuF2F/test.jsonl \
  --filter '^gu2020hat$' -m YOUR_MODEL -o /tmp/reuf2f-run
```

The runner starts a Docker container per task and saves patch predictions.
ReuF2F owns task preparation, shared images and independent Comparator grading;
an agent's completion message is not proof acceptance. Follow the
[ReuF2F guide](docs/usage/reuf2f.md) for setup, options and evaluation.

## Documentation

- [Quick start](docs/quickstart.md)
- [Configuration](docs/advanced/yaml_configuration.md)
- [Python bindings](docs/usage/python_bindings.md)
- [Output files and inspector](docs/usage/output_files.md)
- [FAQ](docs/faq.md)

## Development

See the [contributing guide](docs/contributing.md#development-setup) for dependency
installation, tests and documentation builds.

## License

Original project code and modifications are licensed under MIT.
Third-party notices are included in [LICENSE.md](LICENSE.md).
