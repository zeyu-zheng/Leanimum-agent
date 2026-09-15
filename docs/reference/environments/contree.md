# ConTree

!!! note "ConTree Environment class"

    - [Read on GitHub](https://github.com/swe-agent/mini-swe-agent/blob/main/src/leanimum/environments/extra/contree.py)
    - Requires [ConTree](https://contree.dev) token

    ??? note "Full source code"

        ```python
        --8<-- "src/leanimum/environments/extra/contree.py"
        ```

::: leanimum.environments.extra.contree

This environment executes commands in [ConTree](https://contree.dev) sandboxes using [ConTree SDK](https://github.com/nebius/contree-sdk)

## Setup

1. Install the dependencies:
   ```bash
   pip install -e ".[contree]"
   ```

2. Set up ConTree token and base_url:
   ```bash
   export CONTREE_TOKEN="your-contree-token"
   export CONTREE_BASE_URL="your-given-base-url-for-contree"
   ```

## Usage

Use this backend through the general Lean CLI with a prepared environment config:

```bash
leani -c mini.yaml -c /path/to/environment.yaml -t "Complete and check the Lean task."
```

Set `environment.environment_class` to `contree` and provide the backend's
required image, workspace, and credentials. The dedicated ReuF2F runner currently
integrates task preparation only for Docker/Podman and explicit local execution; it does not provision this backend automatically.

{% include-markdown "../../_footer.md" %}
