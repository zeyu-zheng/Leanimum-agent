# SWE-ReX Modal

!!! note "SWE-ReX Modal Environment class"

    - [Read on GitHub](https://github.com/swe-agent/mini-swe-agent/blob/main/src/leanimum/environments/extra/swerex_modal.py)
    - Requires [Modal](https://modal.com) account and authentication

This environment executes commands in [Modal](https://modal.com) sandboxes using [SWE-ReX](https://github.com/swe-agent/swe-rex).

## Setup

1. Install the full dependencies:
   ```bash
   pip install -e ".[full]"
   ```

2. Set up Modal authentication:
   ```bash
   modal setup
   ```

## Usage

Use this backend through the general Lean CLI with a prepared environment config:

```bash
leani -c mini.yaml -c /path/to/environment.yaml -t "Complete and check the Lean task."
```

Set `environment.environment_class` to `swerex_modal` and provide the backend's
required image, workspace, and credentials. The dedicated ReuF2F runner currently
integrates task preparation only for Docker/Podman and explicit local execution; it does not provision this backend automatically.

{% include-markdown "../../_footer.md" %}
