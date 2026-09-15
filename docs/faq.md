# FAQ

## What tools can the model use?

One: `bash`. Reading files, searching Mathlib, editing Lean code, compiling, and
calling external verification programs all happen through shell commands. Native
tool-call and text-command formats are both supported; they are two encodings of
the same command interface, not different tool sets.

## Does it work with any Lean repository?

The generic CLI can work in a prepared Lean repository using its own toolchain.
The prompt keeps the project's Lean toolchain and points to Comparator's setup
instructions rather than assuming one fixed Lean version. Network,
installation, build, and sandbox support depend on the execution environment.
Compatibility with every historical Lean release is not guaranteed.

## What benchmarks are included?

Only [ReuF2F](usage/reuf2f.md). Its catalog and trusted evaluator remain in a separate
checkout. The runner generates independent submission workspaces and candidate
artifacts; it does not turn the agent's exit marker into a proof score.

## Is Comparator built into the agent?

No. Comparator remains an external CLI invoked through bash. The model can reuse
or set up compatible tools when authorized. A supported isolated environment and
trusted task/configuration are needed for independent verification. A missing
verifier or unsupported platform must be reported, not replaced with a fake success.

## Is local execution sandboxed?

No. A separate working directory is not a security boundary. Use an appropriate
execution backend or a disposable, no-secret environment for untrusted code.
The ReuF2F runner defaults to Docker and never silently falls back to local execution.
Local debugging must be selected explicitly. Generic model and remote execution
adapters are retained.

## Where is configuration stored?

The CLI prints the global configuration directory on startup. Existing `MSWEA_*`
variables and the upstream default directory remain compatible. Set
`MSWEA_GLOBAL_CONFIG_DIR` to isolate this project's settings from an upstream install.
Use `leani-extra config setup` to configure a model and credentials.

## Why no shell session?

<a name="why-no-shell-session"></a>

Commands run independently, while files persist. `cd` and `export` do not carry
across calls. Use explicit working directories or source the same environment
file in every command that needs it. This keeps the command/observation loop small
and makes it straightforward to switch execution backends.

## What does Submitted mean?

The agent requested termination. Compilation, a `Submitted` status, and a model's
claim that a proof passed are not independent proof verification. Read the native
ReuF2F evaluator's per-problem and per-polarity results for acceptance.
