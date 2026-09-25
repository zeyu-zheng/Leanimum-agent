# `leani-extra config`

!!! abstract "Overview"

    * Manage the global `.env` file with `leani-extra config`.
    * Run `leani-extra config --help` to list commands and show the file location.

## Commands

### `setup`

Configure the default model and a provider API key interactively.

```bash
leani-extra config setup
```

This will prompt you for:

1. Your default model (e.g., `anthropic/claude-sonnet-4-5-20250929`)
2. Your API key name and value (e.g., `ANTHROPIC_API_KEY`)

### `set`

Set a specific key in the global config file.

```bash
leani-extra config set LEANA_MODEL_NAME YOUR_MODEL

# Prompt for the key and value
leani-extra config set
```

### `unset`

Remove a key from the global config file.

```bash
leani-extra config unset LEANA_MODEL_NAME
```

### `edit`

Open the global config file in your default editor (uses `$EDITOR` or `nano`).

```bash
leani-extra config edit
```

## Configuration keys

For more configuration options, see [global configuration](../advanced/global_configuration.md).

## Implementation

??? note "Run script"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/run/utilities/config.py)
    - [API reference](../reference/run/config.md)

    ```python
    --8<-- "src/leanimum/run/utilities/config.py"
    ```

{% include-markdown "../_footer.md" %}
