# Leanimum-agent

A minimal, bash-only agent, evolving toward theorem proving and programming in Lean.
Derived from [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent).

> **Current status:** this initial revision establishes the project name, Python
> package, CLI names, and repository documentation. It does **not** add Lean-specific
> prompts, proof validation, or benchmark logic. The upstream agent loop, models,
> execution environments, and benchmark runners are retained without functional changes.

## Names

| Purpose | Name |
| --- | --- |
| Display name | Leanimum-agent |
| Python distribution | `leanimum-agent` |
| Python package | `leanimum` |
| Main command | `leani` |
| Auxiliary commands | `leani-extra`, `leani-e` |

`leanimum-agent` is also an alias for the main command. The upstream CLI aliases
(`mini`, `mini-swe-agent`, `mini-extra`, and `mini-e`) remain available during this
naming-only transition. Installing both distributions into the same Python
environment can overwrite those shared aliases; use a separate virtual environment.

## Install from source

Use Python 3.10 or newer:

```bash
git clone https://github.com/zeyu-zheng/Leanimum-agent.git
cd Leanimum-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The commands above install this checkout; they do not assume that a
`leanimum-agent` release has been published to PyPI.

## Run

```bash
leani --help
leani-extra --help
python -m leanimum --help
```

Configure a model and credentials using the existing configuration interface:

```bash
leani-extra config setup
```

Then run a task from the project directory you want the agent to work in:

```bash
leani -t "Inspect this project and describe its structure."
```

The default interactive mode asks for confirmation before executing commands.
The local environment executes commands on your machine; it is not a sandbox.
All upstream execution backends, including Docker and SWE-ReX, remain available.

The existing `MSWEA_*` environment variables, default `mini-swe-agent` configuration
directory, configuration filenames, and `mini-swe-agent-1.1` trajectory format are
unchanged. To keep configuration separate from an upstream installation, set
`MSWEA_GLOBAL_CONFIG_DIR` to a different directory before running the CLI.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

Some integration tests require optional backends or container tooling. Real model
API tests are opt-in and may incur charges.

```text
src/leanimum/
  agents/        Agent loop and interactive mode
  models/        Model adapters and response handling
  environments/  Command execution backends
  config/        Existing configuration templates
  run/           CLI, utilities, and benchmark runners
  utils/         Logging and serialization
```

The documentation under `docs/` is inherited from upstream. Python import paths
are updated, but the upstream guides, benchmark claims, and feature descriptions
are historical reference, not a report of Leanimum-agent evaluation results.
See the [upstream documentation](https://mini-swe-agent.com/latest/) for the
inherited interfaces, substituting `leanimum` for `minisweagent` and `leani` for
`mini` when using this checkout.

## Upstream and license

The complete upstream Git history is retained. See [UPSTREAM.md](UPSTREAM.md) for
the baseline commit, remote setup, and future synchronization policy.

Leanimum-agent retains the upstream [MIT license and copyright notice](LICENSE.md).
Credit for mini-SWE-agent belongs to its original authors and contributors.
