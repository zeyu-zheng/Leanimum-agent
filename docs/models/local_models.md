# Local models

!!! abstract "Local models"

    * This guide shows how to set up local models.
    * You should already be familiar with the [quickstart guide](../quickstart.md).
    * You should also quickly skim the [global configuration guide](../advanced/global_configuration.md) to understand
      the global configuration and [yaml configuration files guide](../advanced/yaml_configuration.md).


## Using litellm

Currently, models are supported via [`litellm`](https://www.litellm.ai/) by default.

There are typically two steps to using local models:

1. Editing the agent config file to add settings like `custom_llm_provider` and `api_base`.
2. Either ignoring errors from cost tracking or updating the model registry to include your local model.

### Setting API base/provider

If you use local models, you most likely need to add some extra keywords to the `litellm` call.
This is done with the `model_kwargs` dictionary which is directly passed to `litellm.completion`.

In other words, this is how we invoke litellm:

```python
litellm.completion(
    model=model_name,
    messages=messages,
    **model_kwargs
)
```

You can set `model_kwargs` in an agent config file like the following one:

??? note "Default configuration file"

    ```yaml
    --8<-- "src/leanimum/config/mini.yaml"
    ```

Add these model settings to a YAML overlay and load it after a base config,
for example `leani -c mini.yaml -c /path/to/local-model.yaml`:

```yaml
model:
  model_name: "my-local-model"
  model_kwargs:
    custom_llm_provider: "openai"
    api_base: "https://..."
```

!!! tip "Updating the default `leani` configuration file"

    You can set the `LEANA_MINI_CONFIG_PATH` setting to set path to the default `leani` configuration file.
    This will allow you to override the default configuration file with your own.
    See the [global configuration guide](../advanced/global_configuration.md) for more details.

If this is not enough, our model class should be simple to modify:

??? note "Complete model class"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/models/litellm_model.py)
    - [API reference](../reference/models/litellm.md)

    ```python
    --8<-- "src/leanimum/models/litellm_model.py"
    ```

The other part that you most likely need to figure out are costs.
There are two ways to do this with `litellm`:

1. You set up a litellm proxy server (which gives you a lot of control over all the LM calls)
2. You update the model registry (next section)

### Cost tracking

If you run with the above, you will most likely get an error about missing cost information.

If you do not need cost tracking, you can ignore these errors, ideally by editing your agent config file to add:

```yaml
model:
  cost_tracking: "ignore_errors"
```

Alternatively, you can set the global setting:

```bash
export LEANA_COST_TRACKING="ignore_errors"
```

This affects all adapters that read the global cost-tracking setting. To track
costs instead, register the model with its actual token prices.

LiteLLM gets its cost and model metadata from [this file](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json). You can override or add data from this file if it's outdated or missing your desired model by including a custom registry file.

The model registry JSON file should follow LiteLLM's format:

```json
{
  "my-custom-model": {
    "max_tokens": 4096,
    "input_cost_per_token": 0.0001,
    "output_cost_per_token": 0.0002,
    "litellm_provider": "openai",
    "mode": "chat"
  },
  "my-local-model": {
    "max_tokens": 8192,
    "input_cost_per_token": 0.0,
    "output_cost_per_token": 0.0,
    "litellm_provider": "ollama",
    "mode": "chat"
  }
}
```

!!! note "Zero-cost models"

    Keep `cost_tracking: "ignore_errors"` for zero-cost models even when they are
    registered: the default cost check requires a positive cost.

!!! warning "Model names"

    Model names are case sensitive. Please make sure you have an exact match.

!!! warning "Model provider"

    If you use the `custom_llm_provider` or have a provider prefixed to the model name (e.g., `openai/...`),
    then this must also match `litellm_provider` in the config!

There are two ways of setting the path to the model registry:

1. Set `LITELLM_MODEL_REGISTRY_PATH` (e.g., `leani-extra config set LITELLM_MODEL_REGISTRY_PATH /path/to/model_registry.json`)
2. Set `litellm_model_registry` in the agent config file

```yaml
model:
  litellm_model_registry: "/path/to/model_registry.json"
```

## Concrete examples

### Generating ReuF2F trajectories with a local model

After starting a compatible local inference server, put its model settings in
an overlay configuration and merge that with `reuf2f.yaml`:

```bash
leani-extra reuf2f --subset /tmp/reuf2f-tasks --slice 0:1 \
  -c reuf2f.yaml -c /path/to/local-model.yaml -o /tmp/reuf2f-local-run
```

Use a tool-call-capable model for the default benchmark prompt. For ordinary Lean
tasks with a text-only model, use `leani -c mini_textbased.yaml` with your model
settings. See [ReuF2F](../usage/reuf2f.md) for preparation and independent grading.

{% include-markdown "../_footer.md" %}
