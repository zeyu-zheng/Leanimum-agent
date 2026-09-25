# Global configuration

!!! abstract "Overview"

    * Global settings include provider credentials, the default model and cost limits.
    * For prompts and per-run options, see [YAML configuration](yaml_configuration.md).
    * See [model setup](../models/quickstart.md) for provider-specific settings.

## Setting global configuration

Settings come from environment variables or the global `.env` file. At startup,
environment variables take precedence over values in that file. The default
location is the platform-specific configuration directory for `leanimum-agent`;
set `LEANA_GLOBAL_CONFIG_DIR` before launch to use another directory.

Configure a model and API key interactively:

```bash
leani-extra config setup
```

Use [config commands](../usage/config.md) to set, remove or edit saved values.
For a temporary shell setting:

=== "Bash"

    ```bash
    export LEANA_MODEL_NAME="YOUR_MODEL"
    ```

=== "PowerShell"

    ```powershell
    $env:LEANA_MODEL_NAME = "YOUR_MODEL"
    ```

The Bash examples below use `export`. In the `.env` file, use `KEY="value"`
without `export`.

## Models, keys, costs

`LEANA_MODEL_NAME` supplies the default model when neither the CLI nor the YAML
configuration selects one. Provider credentials use their own names, such as
`ANTHROPIC_API_KEY`.

```bash
# Process-wide call and cost limits (default: 0, no limit)
export LEANA_GLOBAL_CALL_LIMIT="100"
export LEANA_GLOBAL_COST_LIMIT="10.00"

# Retry attempts for model API calls (default: 10)
export LEANA_MODEL_RETRY_STOP_AFTER_ATTEMPT="10"
```

To add cost metadata for a model, set `model.litellm_model_registry` in YAML or:

```bash
export LITELLM_MODEL_REGISTRY_PATH="/path/to/model_registry.json"
```

See [local models](../models/local_models.md#cost-tracking) for the registry format.
For models without usable cost information:

```bash
export LEANA_COST_TRACKING="ignore_errors"
```

!!! warning "Cost tracking"

    Ignoring cost errors can leave spending untracked. Cost-based limits cannot
    account for charges the model adapter cannot measure.

## Default config files

```bash
# Additional directory for YAML configs selected by name
export LEANA_CONFIG_DIR="/path/to/configs"

# Default leani config (default: bundled mini.yaml)
export LEANA_MINI_CONFIG_PATH="/path/to/agent.yaml"

# Inspector stylesheet (default: bundled inspector.tcss)
export LEANA_INSPECTOR_STYLE_PATH="/path/to/inspector.tcss"
```

## Settings for environments

These variables choose the backend executable; the values shown are the defaults:

```bash
export LEANA_DOCKER_EXECUTABLE="docker"
export LEANA_SINGULARITY_EXECUTABLE="singularity"
export LEANA_BUBBLEWRAP_EXECUTABLE="bwrap"
```

See [environments](environments.md) for backend selection and requirements.

{% include-markdown "../_footer.md" %}
