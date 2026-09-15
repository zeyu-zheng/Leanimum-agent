# Configs

* `mini.yaml` - Default Lean workflow for `leani`, using bash tool calls.
* `mini_textbased.yaml` - The same Lean workflow with one `mswea_bash_command` block per response.
* `default.yaml` - Text-based Lean config for the minimal Python example.

Prompts follow the upstream mini-SWE-agent structure, wording, and command
examples, with only task-specific substitutions for Lean and ReuF2F. Comparator
setup details stay in the linked documentation. No additional model tools are
registered; submission and proof acceptance remain separate.

## Benchmarks

* `benchmarks/reuf2f.yaml` - The only benchmark config, for `leani-extra reuf2f`.
  Uses the trusted ReuF2F catalog and starts a Linux Docker environment per instance.
