# Upstream provenance and synchronization

Leanimum-agent is derived from mini-SWE-agent. Its complete Git history is
retained rather than importing a source snapshot into an unrelated history.

- Development repository: `https://github.com/zeyu-zheng/Leanimum-agent`
- Upstream repository: `https://github.com/SWE-agent/mini-swe-agent`
- Initial upstream commit: `04d809ceab9df28f9adaed044884180159172930`
- Inherited package version: `2.4.6`

## Initial naming revision

The initial changes establish the `Leanimum-agent` display name,
`leanimum-agent` distribution, `leanimum` Python package, and `leani` CLI.
Imports, packaging references, tests, and user-facing names are updated together.

In that initial revision, agent behavior, prompts, tool protocols, model backends, environments (including
SWE-ReX), benchmark runners, dependency requirements, configuration variables,
and the trajectory format were otherwise unchanged. The upstream CLI aliases
remained available. Existing upstream issue links and historical references were
retained where they explained inherited behavior.

## Lean adaptation

Following the initial naming revision, the built-in task prompts target Lean
proofs/programs and native Comparator setup/use. ReuF2F is now the only built-in
benchmark; SWE-bench and ProgramBench runners/configs and their exclusive tests
were removed, together with the unused `datasets` dependency. Generic model,
execution, shell-tool, and trajectory interfaces remain based on upstream.

ReuF2F data and grading stay in the separate benchmark checkout. The benchmark
runner follows the original SWE-bench batch structure and defaults to Docker/Podman;
explicit local execution reuses the upstream LocalEnvironment.
Benchmark images are supplied externally; this repository does not build or publish them.
Filtering, progress tracking, thread dispatch, skip/redo, and result handling are
reused. The benchmark exports a task release; a separate helper module transports
its original-named source into the shared image, changes only Main in the existing
TOML root, and checks retained toolchain/locked dependencies rather than replacing them.
The submission command and `info["submission"]` -> `model_patch` flow are upstream
code: the agent creates `patch.txt` and prints it after the completion marker.
The patch command is ordinary `git diff -- PATHS > patch.txt`, with Lean source
and TOML layout paths and `git add -N` for new helpers under agent-chosen names. The prompt retains upstream's instruction
not to commit changes. There is no fixed commit parameter, commit-object transfer, automatic
source collection or extra task/result JSON schema. Generic agent, model, and
environment implementations remain unchanged. Neither generation nor
agent self-checks claim independent proof acceptance.

## ReuF2F adaptation boundary

Pinned runner: mini-SWE-agent `04d809ceab9df28f9adaed044884180159172930`,
`src/minisweagent/run/benchmarks/swebench.py`.

- Unchanged Python AST: `update_preds_file`, `remove_from_preds_file`,
  `filter_instances`, `process_futures`, and the Live/thread-pool dispatch block.
  Regression tests pin these blocks to upstream fingerprints.
- `process_instance`: retain `agent.run(task)` and run/save/prediction flow; add shared-image injection,
  release provenance in the trajectory, and cleanup of the selected environment.
  Model initialization is before the per-instance try/finally, as upstream:
  initialization errors write no prediction/trajectory and remain eligible for
  the next run. Later environment failures keep upstream empty-prediction handling;
  there is no model-name fallback or synthetic prediction for failed initialization.
- Dataset loading: a prepared local release instead of Hugging Face datasets.
  `source_file` supplies the original item filename. Exact theorem names live in
  `problem_statement`, so `agent.run(task)` needs no naming parameters.
- Data loading uses upstream's `--subset` (a local release path), with `--filter`/`--slice`
  for selection. Custom `--tasks`, `--problem` and `--list` options are removed; no
  meaningless split option is added. Image configuration uses upstream's `-c`
  options. There are no `--limit` or `--image` shortcuts. Shared image, platform
  and working-directory defaults live only in the benchmark YAML; generic
  environment defaults are unchanged.
- `utils/reuf2f.py`: only task loading/injection and locked Lean preflight.
  After checking file contents, initialize a local Git repository and commit normally.
  The public image is not a prebuilt per-problem SWE-bench image. The release's
  commit identifies which files to read, not the container's Git history.
- The upstream `--environment-class` option, config merge and environment factory
  are retained, with only `docker` and `local` enabled for ReuF2F. Local creates
  a fresh per-attempt workspace under the run directory and reuses dependencies
  from the prepared project at `environment.cwd`, without altering the release.
  Docker is never retried as local. Other backends are not enabled for ReuF2F.
- This is an agent runtime choice, not a field added to task records or predictions.
  SWE-bench's scoring harness does not share this agent-side selector; ReuF2F's
  independent Docker grading containers run Comparator as root with its upstream
  Landrun calls; the solver container is never reused by the evaluator. Both use the same shared
  versioned Lean image from ReuF2F's `docker/tags/<version>/`; the generic verifier
  tools are installed in that image, not in a second grading image.
- Default output is the current directory, as upstream; `-o/--output` selects another
  directory. No custom timestamp-directory default is added.
- ReuF2F's per-command timeout is 1200 seconds; its agent wall-clock limit is unset.
  The existing 3-hour container lifetime remains. These use upstream configuration
  mechanisms and do not change the generic agent/environment implementations.
- No changes to the generic agent, model, environment or progress utilities.
- Intentional trade-off: errors/budget exits do not salvage unsubmitted edits.
  Staged/committed edits omitted by ordinary `git diff` are not recovered either.
  Patch validity and proof acceptance belong exclusively to the benchmark.

## Remotes

Git remotes are local configuration and are not copied when someone clones this
repository. A fresh clone can establish the upstream remote with:

```bash
git remote add upstream https://github.com/SWE-agent/mini-swe-agent.git
git config remote.pushDefault origin
git fetch upstream
```

`origin` is the Leanimum-agent development repository. `upstream` is used to
inspect and fetch mini-SWE-agent changes; development commits are pushed to
`origin`, not upstream.

## Future updates

- Review upstream changes on a separate integration branch before merging them.
- Prefer focused bug fixes and their regression tests when the projects diverge.
- Record the upstream commit when cherry-picking or manually adapting a fix.
- Keep mechanical renaming separate from behavior changes where possible.
- Run the retained test suite and any future Lean-specific tests before merging.

The upstream license, copyright notice, and attribution are preserved.
