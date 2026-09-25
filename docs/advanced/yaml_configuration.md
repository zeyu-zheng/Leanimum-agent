# YAML configuration

!!! abstract "Overview"

    * YAML files configure the agent, model and execution environment.
    * Start with the [quick start](../quickstart.md), then add overrides.
    * Provider credentials and global defaults are covered in
      [global configuration](global_configuration.md).

## Load and override a configuration

```bash
leani -c mini.yaml -c agent.step_limit=100 \
  -c environment.cwd=/absolute/path/to/lean-project
```

You can pass several files and key-value overrides. They are merged recursively
in order; later values replace earlier values.

!!! warning "Include a base configuration"

    If you pass `-c`, the default config is not selected automatically. Use
    `-c mini.yaml` for the generic CLI or `-c reuf2f.yaml` for the benchmark,
    followed by your overrides.

## Overall structure

- `agent` - Prompt templates, step/cost limits and agent options.
- `model` - Model class/name, API options, action parsing and observations.
- `environment` - Backend, working directory, command timeout and environment variables.
- `run` - Entry-point options; supported keys depend on the runner.

??? note "Built-in tool-call configuration"

    ```yaml
    --8<-- "src/leanimum/config/mini.yaml"
    ```

For the generic CLI, `agent.agent_class` and `environment.environment_class` may
name a built-in class or Python import path. The ReuF2F runner uses its fixed
progress-tracking agent and supports Docker/Podman or explicit local execution.
See [agent APIs](../reference/agents/default.md),
[models](../models/quickstart.md), and [environments](environments.md).

## Prompt templates

Templates use [Jinja2](https://jinja.palletsprojects.com/). For example,
`{{task}}` inserts the task passed to `agent.run`.

Agent templates receive agent/model/environment configuration, platform details,
run-time template variables, and counters such as `n_model_calls` and `model_cost`.
Local environments also expose environment variables. Observation templates
receive each command result as `output`; it is not an agent-global shell session.

Keep observations bounded. The built-in model configuration renders short output
in full and longer output as a head/tail excerpt. Reuse that template rather than
copying it into a second prompt.

## Tool calls or text commands

Use `mini.yaml` with a native tool-call model. For text command blocks:

```bash
leani -c mini_textbased.yaml -t "Complete the specified Lean proof."
```

This config selects `litellm_textbased` and the `leana_bash_command` parser.
To use a custom regex, set `model.action_regex` and update the prompt to emit the
same format.

!!! warning "Regex escaping"

    YAML block scalars can include a trailing newline in a regex. A single-quoted
    scalar preserves backslashes without YAML escape processing, for example
    `action_regex: '<action>(.*?)</action>'`.

## Next steps

- [ReuF2F configuration and budgets](../usage/reuf2f.md)
- [Global configuration](global_configuration.md)
- [Python bindings](../usage/python_bindings.md)
- [Subclassing](cookbook.md)

{% include-markdown "../_footer.md" %}
