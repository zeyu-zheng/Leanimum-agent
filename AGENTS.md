# Leanimum-agent overview

- Leanimum-agent is derived from mini-SWE-agent and provides bash-only Lean proof and programming workflows.
- ReuF2F is the only built-in benchmark. Do not edit its trusted source while preparing or running agent submissions.
- Consume a prepared ReuF2F task release via `--subset`; do not recreate mathematical targets or grading here. Each task injects one dual-target Lean file retaining its original filename/theorem name, with an appended `_neg` theorem into the shared `zeyuzhenghub/lean4:v4.33.0` image on `linux/amd64`. Read `source_file` from the prepared release and build that module; do not hard-code `Main` or reimplement negation generation. Check initial file contents, then create a normal local Git commit; do not transfer release commit objects or require matching commit IDs. Use upstream's ordinary `git diff -- PATHS` and `Do NOT commit your changes.` prompt, then store `submission` as `model_patch`. Do not add a fixed-commit prompt parameter, post-run source collector or separate task/result JSON files.
- Keep the image lakefile.toml and change only Project's Main root to source_file's module. Retain the image toolchain/lockfile; check them instead of uploading replacements. Local mode needs the same prepared TOML/lockfile. Agents may add local Lean libraries under chosen names and edit TOML library layout; submit those changes with the source diff. Do not restrict helpers to a predefined Helpers directory or generate ReuF2FAnswers. Legacy lakefile.lean releases must be regenerated.
- Keep the model tool interface bash-only. Comparator is an external CLI; no LSP or custom verification tool is required.
- Model initialization follows the pinned upstream runner: call get_model before the per-instance try/finally. An initialization exception reaches batch error handling without writing a prediction or trajectory, so the next run retries that ID. Do not synthesize an empty prediction/model-name fallback for this case. Later environment/agent failures retain upstream empty-submission handling.
- Candidate generation and independent grading are separate. Never treat Submitted or a self-reported success as a verified proof.
- ReuF2F uses a 1200-second per-command timeout, no agent wall-clock limit, and the existing 3-hour container lifetime. Keep generic agent configurations unchanged.
- The ReuF2F batch runner exposes upstream's `--environment-class` / `environment.environment_class` with exactly `docker` (default, including Podman) and explicitly selected `local`. Local uses a prepared Lean project at `environment.cwd`, creates a fresh per-attempt workspace and reuses that project's locked `.lake/packages`; it has no task isolation and never replaces a failed Docker launch. Do not restore other ReuF2F backends or any evaluator bypass. Shared image build/push belongs to ReuF2F. Independent grading uses fresh Docker
  containers owned by ReuF2F, not host execution or the solver container; no
  model API keys/host paths/sockets cross that boundary. Solver and grader use the
  same versioned Lean image (including generic verifier tools), not the same
  container. Generic agent/model/environment implementations stay unchanged.
- The idea of this project is to write the simplest, smallest, most readable agent.

The project is structured as

```bash
leanimum/__init__  # Protocols/interfaces for all base classes
leanimum/agents  # Agent control flow & loop
leanimum/environments  # Executing agent actions
leanimum/models  # LM interfaces
leanimum/run  # Run scripts that serve as an entry point
```

- The project embraces polymorphism: Every individual class should be simple, but we offer alternatives
- Every use case should start with a run script, that picks one agent, environment, and model class to run

# Style guide

1. Target python 3.10 or higher
2. Use python with type annotations. Use `list` instead of `List`.
3. Use `pathlib` instead of `os.path`. Use `Path.read_text()` over `with ...open()` constructs.
4. Use `typer` to add interfaces
5. Keep code comments to a minimum and only highlight particularly logically challenging things
6. Do not append to the README unless specifically requested
7. Use `jinja` for formatting templates
8. Use `dataclass` for keeping track config
9. Do not catch exceptions unless explicitly told to.
10. Write concise, short, minimal code.
11. In most cases, avoid initializing variables just to pass them to a function. Instead just pass the expression to the function directly.
12. Not every exception has to be caught. Exceptions are a good way to show problems to a user.
13. This repository rewards minimal code. Try to be as concise as possible.

Here's an example for rule 11:

```python
# bad
a = func()
Class(a)

# good
Class(func())
```

## Test style

1. Use `pytest`, not `unittest`.
2. <IMPORTANT>Do not mock/patch anything that you're not explicitly asked to do</IMPORTANT>
3. Avoid writing trivial tests. Every test should test for at least one, preferably multiple points of failure
4. Avoid splitting up code in multiple lines like this: `a=func()\n assert a=b`. Instead, just do `assert func() == b`
5. The first argument to `pytest.mark.parametrize` should be a tuple (not a string! not a list!), the second argument must be a list (not a tuple!).

Here's an example for rule 4:

```python
# bad
result = func()
assert result == b

# good
assert func() == b
```

# Commit messages

Use the following format for commit messages:

- `ci: description` for all testing related changes, and changes to github workflows etc.
- `dev: description` for development related changes, including updates to the cursor or claude rules
- `fix(component): description` for bug fixes
- `feat(component): description` for new features
- `enh(component): description` for enhancements
- `docs: description` for documentation
- `ref(component): description` for refactoring
- `chore: description` for maintenance tasks (pre-commit hooks, imports, etc.)

Generally, the description should focus on the intent of the changes, not the implementation details.

## Style notes

<IMPORTANT>Do **NOT** add "Co-authored-by: Cursor" lines to the commit message or to the trailer.</IMPORTANT>

## Reviewing

While preparing the commit message, flag critical issues that should be addressed before committing. Do not flag style issues or minor changes.

Flag the following:

- Anything that might raise an unhandled exception in an unintentional manner
- Anything that looks logically wrong or inconsistent
- Breaking changes to protocols/interfaces without corresponding updates to implementations

Flag the following style issue as minor:

- Imports not at top of file

## Components

Use these component names in parentheses for `fix`, `feat`, `enh`, and `ref` commits:

- `models` - Changes to model interfaces (litellm, anthropic, openai, portkey, openrouter)
- `agents` - Changes to agent classes (default, interactive, multimodal)
- `env` - Changes to environments (docker, local, singularity, bubblewrap, swerex)
- `config` - Changes to configuration files or config handling
- `run` - Changes to run scripts (mini, hello_world)
- `benchmarks` - Changes to the ReuF2F runner and batch utilities
- `cli` - Changes to CLI argument handling
- `deps` - Dependency updates
