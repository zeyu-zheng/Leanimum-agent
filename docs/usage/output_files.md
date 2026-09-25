# Output files

!!! abstract "Overview"

    Leanimum-agent saves trajectories as JSON. The ReuF2F runner also saves
    patch predictions, logs and batch termination statuses.

## Trajectory files (`.traj.json`)

A trajectory records messages, configuration, model costs and termination status.
Its format identifier is `leanimum-agent-1.1`.

!!! tip "Viewing trajectories"

    Browse a file or directory with the [inspector](inspector.md):

    ```bash
    leani-extra inspect /path/to/INSTANCE_ID.traj.json
    ```

### Structure

| Field | Contents |
| --- | --- |
| `info.model_stats` | `instance_cost` and `api_calls` for the run |
| `info.config` | Agent/model/environment configuration and class names |
| `info.mini_version` | Installed agent package version |
| `info.exit_status` | Termination status, such as `Submitted` or `LimitsExceeded` |
| `info.submission` | Submitted text, or an empty value if none was produced |
| `messages` | Full conversation, including command observations |
| `trajectory_format` | Format identifier |

The ReuF2F runner adds `instance_id` at the top level. Exceptions may add
`exception_str` and `traceback` under `info`.

Messages contain model-specific fields and an `extra` dictionary for parsed
actions, costs and execution results. Tool-call observations use the provider's
tool message format; text-based models use rendered user messages. The terminal
message has `role: "exit"`.

!!! note "Submitted is not a proof verdict"

    `Submitted` means the agent requested completion. ReuF2F evaluates the patch
    independently to decide whether a proof or refutation is accepted.

## ReuF2F batch outputs

| Path | Contents |
| --- | --- |
| `preds.json` | ID-keyed patch predictions |
| `leanimum.log` | Runner messages and failures |
| `exit_statuses_TIMESTAMP.yaml` | Batch termination statuses |
| `INSTANCE_ID/INSTANCE_ID.traj.json` | Agent trajectory |

### `preds.json` format

Each record has three fields:

```json
{
  "gu2020hat": {
    "instance_id": "gu2020hat",
    "model_name_or_path": "my-model",
    "model_patch": "diff --git a/gu2020hat.lean b/gu2020hat.lean\n..."
  }
}
```

`model_patch` contains diff text, not a filename or verdict. Pass predictions and
the same dataset to the [evaluator](reuf2f.md#predictions-and-evaluation).

## Failures and resume

- Model initialization errors write no prediction or trajectory and can be retried
  by resuming the run.
- Later setup/agent failures can write an empty prediction. Trajectories are saved
  when an agent was constructed.
- Existing IDs in `preds.json`, including empty predictions, are skipped unless
  `--redo-existing` is set. Deleting a trajectory alone does not rerun an ID.
- Unsubmitted edits are not recovered.

{% include-markdown "../_footer.md" %}
