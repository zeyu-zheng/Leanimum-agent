# Leanimum-agent

Keep Leanimum-agent small, bash-only and readable. Third-party notices belong in
`LICENSE.md`, not repeated adaptation comments.

## Repository layout

```text
src/leanimum/
  agents/        Agent control flow and interactive mode
  models/        Model adapters and action/response formatting
  environments/  Shell execution backends
  config/        Prompts and configuration
  run/           CLI, utilities and benchmark runner
```

Each run script selects the model, agent and environment. Preserve active
execution paths; remove only demonstrably unused private helpers, not
configurable backends or public interfaces.

## ReuF2F boundary

- ReuF2F is the only built-in benchmark. Consume its dataset (`test.jsonl`, built by
  `reuf2f dataset build`) with `--subset`; do not edit trusted benchmark sources,
  export targets or grade here.
- Keep `run/benchmarks/reuf2f.py` aligned with mini-swe-agent's
  `run/benchmarks/swebench.py`. Read `instance_id`, `problem_statement`, `challenge`
  and `image` from each record; do not regenerate negation or hard-code a namespace.
- Each task runs in its record's `image` (shared, `linux/amd64`, x86_64 hosts). The
  only step beyond mini-swe-agent is `prepare_environment`: copy `challenge` to
  `/testbed/INSTANCE_ID.lean`, change only Project's `Main` root to that module,
  build it and create a local Git commit. Trust the image; no release consistency checks.
- Agents may add local Lean libraries and submit TOML layout changes. Do not impose
  a Helpers directory or generate a separate answer library.
- Retain `git add PATHS && git diff --cached > patch.txt`, `Do NOT commit your
  changes.`, completion marker and `submission` -> `model_patch` flow. No post-run
  source collector, archive or extra task/result JSON schema.
- Initialize the model before per-instance try/finally. Initialization
  errors write no prediction/trajectory and remain retryable; later setup/agent
  errors retain empty-submission handling.
- The ReuF2F runner enables `docker` (including Podman) and explicit `local` only.
  Local uses a prepared project at `environment.cwd`, separate attempt directories
  and linked dependencies; it has no task isolation. Never fall back to local after
  a Docker failure. Generic CLI backends remain available.
- Benchmark defaults: command timeout 1200 seconds, no agent wall-clock limit,
  3-hour container lifetime, 250 steps and $3 cost limit. Do not change generic
  configurations as a side effect of benchmark work.
- Image build/push and independent Comparator grading belong to ReuF2F. Solver and
  grader use the same image, not the same container. Do not forward host paths,
  Docker sockets or provider credentials by default. `Submitted` is not acceptance.
- Comparator is an external CLI. Keep the model tool interface bash-only; do not
  add LSP or a custom verifier tool.

## Documentation

Use English, short task-oriented sections and executable command examples. Keep
README as an entry point, runner details in `docs/usage/reuf2f.md`, output schemas
in `docs/usage/output_files.md`, and third-party notices in `LICENSE.md`. Use existing
MkDocs admonitions and source/API references rather than duplicating implementation
code or migration histories. Validate links, option names and defaults.

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
