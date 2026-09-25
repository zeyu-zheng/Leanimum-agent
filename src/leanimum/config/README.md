# Configs

* `mini.yaml` - Default Lean workflow for `leani`, using bash tool calls.
* `mini_textbased.yaml` - The same Lean workflow with one `leana_bash_command` block per response.
* `default.yaml` - Text-based Lean config for the minimal Python example.

See the [configuration guide](../../../docs/advanced/yaml_configuration.md) for
file selection, overrides and template variables.

## Benchmarks

* `benchmarks/reuf2f.yaml` - Config for `leani-extra reuf2f`. Uses the ReuF2F dataset
  (`test.jsonl`) and starts a Docker container per instance by default. See the
  [runner guide](../../../docs/usage/reuf2f.md) for setup and outputs.
