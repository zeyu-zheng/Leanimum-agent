# Inspector

!!! abstract "Overview"

    * Browse `.traj.json` files with `leani-extra inspector` or `leani-e i`.
    * See [output files](output_files.md) for the trajectory format.
    * Use [jless](https://jless.io/) to inspect raw JSON.

## Usage

```bash
# Search the current directory recursively
leani-extra inspector

# Open one trajectory
leani-extra inspector /path/to/task.traj.json

# Search another directory
leani-extra inspector /path/to/results
```

Use `--no-reasoning` to hide reasoning initially.

## Key bindings

- `q`: Quit the inspector
- `h`/`LEFT`: Previous step
- `l`/`RIGHT`: Next step
- `j`/`DOWN`: Scroll down
- `k`/`UP`: Scroll up
- `H`: Previous trajectory
- `L`: Next trajectory
- `e` / `E`: Open the current step / full trajectory in jless
- `r`: Toggle reasoning
- `R`: Reload the trajectory from disk

## FAQ

> How can I select/copy text on the screen?

Hold down the `Alt`/`Option` key and use the mouse to select the text.

## Implementation

The inspector is implemented with [textual](https://textual.textualize.io/).

??? note "Implementation"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/run/utilities/inspector.py)

    ```python linenums="1"
    --8<-- "src/leanimum/run/utilities/inspector.py"
    ```

{% include-markdown "../_footer.md" %}
