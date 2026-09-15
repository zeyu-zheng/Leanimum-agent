# Entry points / run scripts

## Work locally (i.e., without a sandbox)

* `hello_world.py` - Extremely simple example of how to use the `default.py` agent.
* `mini.py` - The `leani` CLI, using the interactive agent and Lean prompt by default.

## Extras

* `benchmarks/reuf2f.py` - Generate ReuF2F candidates with the default agent.
  Uses Docker/Podman by default or explicit `--environment-class local`, and reuses the upstream batch flow; shared image build/push belongs to ReuF2F.
  Comparator grading is performed by ReuF2F's own CLI, separately from agent submission.
