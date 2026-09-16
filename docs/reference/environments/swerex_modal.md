# SWE-ReX Modal

!!! note "SWE-ReX Modal Environment class"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/environments/extra/swerex_modal.py)
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

Set `environment.environment_class` to `swerex_modal` and configure the image,
workspace and credentials. See the [ReuF2F runner](../../usage/reuf2f.md#environment)
for its supported environments.

{% include-markdown "../../_footer.md" %}
