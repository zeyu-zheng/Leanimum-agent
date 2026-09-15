# Output files

## Agent trajectories

The `.traj.json` schema retains `trajectory_format: mini-swe-agent-1.1` for
compatibility with the inspector. It stores messages, configuration, cost and
termination status. `Submitted` means the agent requested completion, not that a
proof has been independently accepted.

## ReuF2F batch outputs

- `preds.json`: an ID-keyed mapping of exactly `instance_id`, `model_name_or_path`,
  and `model_patch`. The runner stores the agent's `submission` as patch text,
  following upstream mini-SWE-agent. Errors or budget exits without a patch have
  an empty prediction; workspaces are not automatically collected.
  Existing IDs are skipped unless `--redo-existing` is set.
- `leanimum.log`: runner log, including pre-agent setup errors.
- `exit_statuses_TIMESTAMP.yaml`: batch progress termination report.
- `INSTANCE_ID/INSTANCE_ID.traj.json`: messages, config, costs and termination;
  release `source_revision` and `base_commit` are also recorded as data provenance,
  not the container's initial commit or final HEAD. Saved whenever
  an agent was constructed, including model errors and budget exits.

With explicitly selected local execution, `INSTANCE_ID/workspace-*` also retains
each attempt's source and build files. These are diagnostic output, not grading
authority; submission is still solely the patch in `preds.json`.

No separate `task.json`, `result.json`, submission archive, or agent-side score is
produced. `Submitted` only identifies the upstream termination protocol; even an
arbitrary success string is stored as untrusted patch text, not a proof verdict.
ReuF2F's independent evaluator consumes predictions and the original trusted release.

See [ReuF2F](reuf2f.md) for preparation, container preflight and independent grading.

```bash
leani-extra inspect /path/to/INSTANCE_ID.traj.json
```
