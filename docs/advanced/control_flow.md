# Agent control flow

!!! note "Understanding AI agent basics"

    For an introduction to agent design, see [this tutorial](https://minimal-agent.com).

!!! abstract "Understanding the default agent"

    * This guide shows the control flow of the default agent.
    * See the [cookbook](cookbook.md) to extend the agent.

The following diagram shows the control flow of the agent:

```mermaid
flowchart TD
    subgraph run["<b><code>Agent.run(task)</code></b>"]
        direction TB
        A["<b><code>Initialize messages</code></b>"] --> B
        B["<b><code>Agent.step</code></b>"] --> C{"<b><code>Exception?</code></b>"}
        C -->|Yes| D["<b><code>Record exception</code></b><br/>Unexpected errors are re-raised"]
        C -->|No| E{"<b><code>messages[-1].role == exit?</code></b>"}
        D -->|Handled| E
        E -->|No| B
        E -->|Yes| F["<b><code>Return result</code></b>"]
    end

    subgraph step["<b><code>Agent.step()</code></b><br>Single iteration</br>"]
        direction TB
        S1["<b><code>Agent.query</code></b>"] --> S2["<b><code>Agent.execute_actions</code></b>"]
    end

    subgraph query["<b><code>Agent.query()</code></b><br>Also checks for cost limits</br><br></br>"]
        direction TB
        Q3["<b><code>Model.query</code></b>"] --> Q4["<b><code>Agent.add_messages</code></b>"]
    end

    subgraph execute_actions["<b><code>Agent.execute_actions(message)</code></b>"]
        direction TB
        E2["<b><code>Environment.execute</code></b><br/>Also raises the Submitted exception if we're done"] --> E3["<b><code>Model.format_observation_messages</code></b>"]
        E3 --> E4["<b><code>Agent.add_messages</code></b>"]
    end

    B -.-> step
    S1 -.-> query
    S2 -.-> execute_actions
```

The implementation is embedded below so the guide follows the current code:

??? note "Default agent class"

    - [Read on GitHub](https://github.com/zeyu-zheng/Leanimum-agent/blob/main/src/leanimum/agents/default.py)
    - [API reference](../reference/agents/default.md)

    ```python
    --8<-- "src/leanimum/agents/default.py"
    ```

`DefaultAgent.run` renders the task and repeatedly calls `step`, which queries the
model, executes its actions and appends observations. Model implementations format
those observations for their own API.

- `Submitted` finishes the task after a zero-exit command emits the completion marker.
- `LimitsExceeded` and `TimeExceeded` stop work at configured budgets.
- `FormatError` adds corrective feedback; repeated format errors can end the run.
- `UserInterruption` lets the interactive agent add feedback or change modes.
- Command timeouts are returned as environment observations. They are not an
  agent `TimeoutError` exception.

Unexpected exceptions are recorded and re-raised. The `finally` path saves the
trajectory, and an exit message supplies the returned submission/status.

See [Python bindings](../usage/python_bindings.md) for construction and
[the cookbook](cookbook.md) for subclassing.

{% include-markdown "../_footer.md" %}
