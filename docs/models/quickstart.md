# Model setup quickstart

!!! tip "Setup"

    * In most cases, you can simply run `leani-extra config setup` to set up your default model and API keys.
      This should be run the first time you run `leani`.
    * By default we support all models using [`litellm`](https://github.com/BerriAI/litellm).
    * We also offer support for models via [Openrouter](https://openrouter.ai/) and [Portkey](https://portkey.ai/).

## Setting API keys

There are several ways to set your API keys:

* **Recommended**: Run our setup script: `leani-extra config setup`. This should also run automatically the first time you run `leani`.
* Use `leani-extra config set ANTHROPIC_API_KEY <your-api-key>` to put the key in the `leani` [config file](../advanced/global_configuration.md).
* Export your key as an environment variable: `export ANTHROPIC_API_KEY=<your-api-key>` (this is not persistent if you restart your shell, unless you add it to your shell config, like `~/.bashrc` or `~/.zshrc`).

??? note "All the API key names"

    We use [`litellm`](https://github.com/BerriAI/litellm) to support most models.
    Here's a list of all the API key names available in `litellm`:

    ```
    ALEPH_ALPHA_API_KEY
    ALEPHALPHA_API_KEY
    ANTHROPIC_API_KEY
    ANYSCALE_API_KEY
    AZURE_AI_API_KEY
    AZURE_API_KEY
    AZURE_OPENAI_API_KEY
    BASETEN_API_KEY
    CEREBRAS_API_KEY
    CLARIFAI_API_KEY
    CLOUDFLARE_API_KEY
    CO_API_KEY
    CODESTRAL_API_KEY
    COHERE_API_KEY
    DATABRICKS_API_KEY
    DEEPINFRA_API_KEY
    DEEPSEEK_API_KEY
    FEATHERLESS_AI_API_KEY
    FIREWORKS_AI_API_KEY
    FIREWORKS_API_KEY
    FIREWORKSAI_API_KEY
    GEMINI_API_KEY
    GROQ_API_KEY
    HUGGINGFACE_API_KEY
    INFINITY_API_KEY
    MARITALK_API_KEY
    MISTRAL_API_KEY
    NEBIUS_API_KEY
    NLP_CLOUD_API_KEY
    NOVITA_API_KEY
    NVIDIA_NIM_API_KEY
    OLLAMA_API_KEY
    OPENAI_API_KEY
    OPENAI_LIKE_API_KEY
    OPENROUTER_API_KEY
    OR_API_KEY
    PALM_API_KEY
    PERPLEXITYAI_API_KEY
    PREDIBASE_API_KEY
    PROVIDER_API_KEY
    REPLICATE_API_KEY
    TOGETHERAI_API_KEY
    VOLCENGINE_API_KEY
    VOYAGE_API_KEY
    WATSONX_API_KEY
    WX_API_KEY
    XAI_API_KEY
    XINFERENCE_API_KEY
    ```

    In addition, Portkey models use the `PORTKEY_API_KEY` environment variable.

## Selecting a model

!!! note "Model names and providers."

    We support most models using [`litellm`](https://github.com/BerriAI/litellm).
    You can find a list of their supported models [here](https://docs.litellm.ai/docs/providers).
    Please always include the provider in the model name, e.g., `anthropic/claude-...`.

* **Recommended**: `leani-extra config setup` (should be run the first time you run `leani`) can set the default model for you
* All command line interfaces allow you to set the model name with `-m` or `--model`.
* In addition, you can set the default model with `leani-extra config set LEANA_MODEL_NAME <model-name>`, by editing the global [config file](../advanced/global_configuration.md) (shortcut: `leani-extra config edit`), or by setting the `LEANA_MODEL_NAME` environment variable.
* You can also set your model in a config file (key `model_name` under `model`).
* If you want to use local models, please check this [guide](local_models.md).

!!! note "Popular models"

    Here's a few examples of popular models:

    ```
    anthropic/claude-opus-4-6-20260205
    openai/gpt-5.4
    openai/gpt-5.4-mini
    gemini/gemini-2.5-pro
    deepseek/deepseek-chat
    ```

    ??? note "List of all supported models"

        Here's a list of all model names supported by `litellm` as of Aug 29th 2025.
        For even more recent models, check the [`model_prices_and_context_window.json` file from litellm](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json).

        ```
        --8<-- "docs/data/all_models.txt"
        ```

To find the corresponding API key, check the previous section.

## Extra model settings

Add model settings in a [YAML configuration](../advanced/yaml_configuration.md).
The snippets below are overlays, not complete agent configs. Load a base first,
for example `leani -c mini.yaml -c /path/to/model.yaml`.

Examples:

=== "Temperature"

    `litellm` allows to set model-specific settings with the `model_kwargs` key:

    ```yaml
    model:
      model_name: "anthropic/claude-sonnet-4-5-20250929"
      model_kwargs:
        temperature: 0.0
    ```

    Note that temperature isn't supported by all models.

=== "GPT-5 reasoning effort (Chat Completions API)"

    `litellm` allows to set model-specific settings with the `model_kwargs` key:

    ```yaml
    model:
      model_name: "openai/gpt-5-mini"
      model_kwargs:
        drop_params: true
        reasoning_effort: "high"
        verbosity: "medium"
    ```

    Here, `drop_params` is used to drop any parameters that are not supported by the model.

=== "GPT-5 with Responses API"

    For OpenAI models that support the Responses API, you can use the `litellm_response` model class:

    ```yaml
    model:
      model_class: "litellm_response"
      model_name: "openai/gpt-5-mini"
      model_kwargs:
        drop_params: true
        reasoning:
          effort: "high"
    ```

=== "OpenRouter"

    This example explicitly sets the model class to `openrouter` (see the next section for more details).
    It also explicitly sets the providers to disable switching between them (this is useful if you need
    very consistent cost behavior, e.g., for benchmarking, but it's not recommended if you're just interested
    in getting low latency and good prices).

    ```yaml
    model:
        model_name: "moonshotai/kimi-k2-0905"
        model_class: "openrouter"
        model_kwargs:
            temperature: 0.0
            provider:
              allow_fallbacks: false
              only: ["Moonshot AI"]
    ```

=== "Local models"

    Using `litellm` with local models:

    ```yaml
    model:
      model_name: "my-local-model"
      model_kwargs:
        custom_llm_provider: "openai"
        api_base: "https://..."
    ```

    See [this guide](local_models.md) for more details on local models.
    In particular, you need to configure token costs for local models.

Here are more examples of how to configure specific models:

=== "Gemini 3 (Openrouter)"

    ```yaml
    model:
        model_name: "google/gemini-3-pro-preview"
        model_class: openrouter
        model_kwargs:
            temperature: 0.0
    ```

=== "GPT 5.1 medium (Portkey)"

    ```yaml
    model:
        model_name: "@openai/gpt-5.1"
        model_class: portkey
        model_kwargs:
            reasoning_effort: "medium"
            verbosity: "medium"
    ```

=== "Claude Haiku 4.5"

    ```yaml
    model:
        model_name: "anthropic/claude-haiku-4-5-20251001"
        model_kwargs:
            temperature: 0.0
    ```

=== "GPT 5 mini (Portkey)"

    ```yaml
    model:
        model_name: "@openai/gpt-5-mini"
        model_class: portkey
    ```

=== "Deepseek"

    ```yaml
    model:
        model_name: "deepseek/deepseek-reasoner"
        model_kwargs:
            temperature: 0.0
    ```

=== "Minimax (Openrouter)"

    ```yaml
    model:
        model_name: "minimax/minimax-m2"
        model_class: openrouter
        model_kwargs:
            temperature: 0.0
    ```

## Model classes

The default model class is `litellm`. Select another adapter with `--model-class`
or `model.model_class` in YAML. Anthropic cache-control defaults are applied
separately from adapter selection.

For example:

=== "Openrouter model"

    ```bash
    leani -m "moonshotai/kimi-k2-0905" --model-class openrouter
    ```

    **Alternatively:** In the agent config file:

    ```yaml
    model:
        model_name: "moonshotai/kimi-k2-0905"
        model_class: openrouter
    ```

=== "Portkey model"

    ```bash
    leani -m "claude-sonnet-4-5-20250929" --model-class portkey
    ```

    **Alternatively:** In the agent config file:
    ```yaml
    model:
        model_name: "claude-sonnet-4-5-20250929"
        model_class: portkey
    ```


* **`litellm`** ([`LitellmModel`](../reference/models/litellm.md)) - **Default and recommended**. Supports most models through [litellm](https://github.com/BerriAI/litellm). Works with OpenAI, Anthropic, Google, and many other providers. Anthropic models automatically get cache control settings when the model name contains "anthropic", "claude", "sonnet", or "opus".

* **`litellm_response`** ([`LitellmResponseModel`](../reference/models/litellm_response_toolcall.md)) - Uses the Responses API with native tool calling. Each request includes the conversation history.

* **`openrouter`** ([`OpenRouterModel`](../reference/models/openrouter.md)) - Direct integration with [OpenRouter](https://openrouter.ai/) API for accessing various models through a single endpoint.

* **`portkey`** ([`PortkeyModel`](../reference/models/portkey.md)) - Integration with [Portkey](https://portkey.ai/) for accessing various models with enhanced observability, caching, and routing features. Note that this still uses `litellm` to calculate costs.

On top, there's a few more exotic model classes that you can use:

* **`deterministic`** ([`DeterministicModel`](../reference/models/test_models.md)) - Returns predefined responses for testing and development purposes.
* **`leanimum.models.extra.roulette.RouletteModel` and `leanimum.models.extra.roulette.InterleavingModel`** ([`RouletteModel`](../reference/models/extra.md) and [`InterleavingModel`](../reference/models/extra.md)) - Randomly selects or interleaves multiple configured models for each query.

As with the last two, you can also specify any import path to your own custom model class (even if it is not yet part of the Leanimum-agent package).

{% include-markdown "../_footer.md" %}
