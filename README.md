# Leanimum-agent

A minimal, bash-only agent for theorem proving and programming in Lean.
Derived from [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent), with its
model adapters, execution backends, and linear agent loop retained.

## What it does

- Searches project and Mathlib source with shell commands, edits Lean files, and
  iterates on compiler feedback. The model has one tool: `bash`.
- Uses Lean-specific prompts for both native tool calls and text command blocks.
- Can inspect, set up, and invoke the native Comparator CLI through bash when the
  task and environment permit it. No LSP, custom verifier CLI, or Comparator Python
  dependency is added. Compatible binaries and isolation must be available.
- Supports one built-in benchmark: [ReuF2F](https://github.com/zeyu-zheng/ReuF2F).
  Its catalog and evaluator remain in the separate benchmark repository.

**Candidate generation is not grading.** Compilation, the agent's completion
marker, and self-reported verification do not establish a proof. The ReuF2F runner
stores the agent's patch and termination status, not a score; use the trusted
ReuF2F evaluator to obtain acceptance results. No benchmark performance claim is made here.

## Names and installation

| Purpose | Name |
| --- | --- |
| Display name | Leanimum-agent |
| Python distribution | `leanimum-agent` |
| Python package | `leanimum` |
| Main command | `leani` |
| Auxiliary commands | `leani-extra`, `leani-e` |

Use Python 3.10 or newer and install from this checkout:

```bash
git clone https://github.com/zeyu-zheng/Leanimum-agent.git
cd Leanimum-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
leani-extra config setup
```

This does not assume a PyPI release exists. `leanimum-agent` is another main-command
alias. Upstream aliases (`mini`, `mini-swe-agent`, `mini-extra`, `mini-e`) remain;
use a separate environment to avoid alias conflicts with upstream installations.
The `MSWEA_*` settings and `mini-swe-agent-1.1` trajectory schema remain compatible.
Set `MSWEA_GLOBAL_CONFIG_DIR` to separate configuration from an upstream installation.

## Work in a Lean project

```bash
leani -c mini.yaml -c environment.cwd=/absolute/path/to/lean-project \
  -t "Complete the proof of Example.target in Example.lean and verify it."
```

The prompts retain upstream's structure, command rules, and examples, with small
Lean-specific substitutions. Comparator setup is linked rather than embedded as a manual.
For text-based models use `-c mini_textbased.yaml`; the matching model class is
selected by that configuration. `default.yaml` is the text-based Python example.
All three configurations use a 600-second per-command timeout, which is overridable.

The interactive CLI asks for command confirmation by default. Local execution is
not a sandbox. Network access, installations, and verification depend on the
chosen environment's permissions. Docker, Singularity, SWE-ReX, Bubblewrap, and
ConTree backends remain available to the generic CLI. Do not use a fake sandbox
or weaken a verifier to make a proof appear accepted.

## ReuF2F: the only benchmark

First export tasks with ReuF2F's `prepare-tasks` command, then pass the prepared
release to this runner. The default shared image is `zeyuzhenghub/lean4:v4.33.0`
on `linux/amd64`; no per-task image build is needed.

```bash
# Run one instance, or omit --filter for the whole release.
leani-extra reuf2f --subset /tmp/reuf2f-tasks \
  --filter '^berger-modified-egz$' -m YOUR_MODEL -o /tmp/reuf2f-run
```

Each task runs in its own Docker container at `/testbed`. The runner injects one
self-contained Lean file with its original name/theorem and an appended `_neg`
target. It keeps the image TOML, changes only its Project root from Main to the
task module, retains/verifies toolchain and lockfile, checks dependencies/build and creates
a local initial Git commit before the first
model query. The benchmark checkout and per-task grading inputs are not copied in.
The updated shared image includes generic Comparator tools; official grading still
runs independently in a fresh container, never against the solver's modified state.
Use `-c reuf2f.yaml -c environment.image=IMAGE_OR_DIGEST` to override or pin the shared image.

The batch flow reuses the upstream progress-tracking agent, filtering/slicing,
worker pool, result locking, skip-existing/`--redo-existing`, and failure/trajectory
handling. Standard three-field patch predictions and per-instance trajectories are saved on the driver;
no host checkout or Docker socket is mounted into task containers by default.

Solver Docker is not the grader. ReuF2F creates a separate trusted grading
container for each task, applies the patch and runs Comparator there, then collects
reports and destroys it. Both containers use the same versioned Lean image, built
with `reuf2f images build ./docker` from the benchmark checkout; there is no
separate grading image. Older images without the verifier tools need rebuilding.
The benchmark runner exposes `--environment-class docker|local`, defaulting to
Docker/Podman. Local must be selected explicitly and needs a prepared Lean project
at `environment.cwd`; it provides no additional isolation, even though each task
gets a fresh workspace. There is no automatic host fallback. Other ReuF2F backends
are unsupported. Shared image build/push and independent grading stay in ReuF2F.

See [the ReuF2F guide](docs/usage/reuf2f.md) for outputs and the native scoring command.
SWE-bench and ProgramBench runners/configurations are no longer included.

## Development and provenance

```bash
python -m pip install -e '.[dev]'
pytest --ignore=tests/test_fire.py -m 'not slow'
```

Optional-backend tests need the corresponding dependencies. Real model API tests
are opt-in and may incur charges. ReuF2F grading requires its external verification
stack; running the unit suite does not exercise trusted production grading.

```text
src/leanimum/
  agents/        Generic agent loop and interactive mode
  models/        Model adapters and action/response handling
  environments/  Command execution backends
  config/        Lean prompts and the ReuF2F benchmark configuration
  run/           CLI, utilities, and ReuF2F runner
  utils/         Logging and serialization
```

The upstream Git history, [MIT license](LICENSE.md), and original authors' credit
are retained. [UPSTREAM.md](UPSTREAM.md) records the baseline and sync policy.
