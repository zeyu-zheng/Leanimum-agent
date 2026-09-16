# FAQ

## What tools can the model use?

One: `bash`. Files, searches, edits and compiler checks all use shell commands.
Native tool calls and text command blocks are two encodings of that interface.

## Does it work with any Lean repository?

Use a prepared project with its own toolchain and dependencies. The generic CLI
can work there without the ReuF2F task format. Compatibility with every historical
Lean release is not guaranteed.

## What benchmarks are included?

[ReuF2F](usage/reuf2f.md) is the built-in benchmark. Leanimum produces patches;
the separate benchmark repository owns task preparation and independent grading.

## Is Comparator built into the agent?

No. It is an external command-line tool. The ReuF2F image includes the verification
binaries, but official grading still runs separately from the solver container.

## Is local execution sandboxed?

No. A working directory is not a security boundary. Use an appropriate
[backend](advanced/environments.md) or a disposable host for untrusted code.
ReuF2F defaults to Docker and does not fall back to local after a Docker failure.

## Where is configuration stored?

The CLI prints the global configuration directory at startup. Run
`leani-extra config setup` to configure credentials and a model. Set
`LEANA_GLOBAL_CONFIG_DIR` to separate the settings from another installation.
See [global configuration](advanced/global_configuration.md).

## Why no shell session?

<a name="why-no-shell-session"></a>

Files persist, but commands run independently. A previous `cd` or `export` does
not carry into the next call. Use an explicit working directory or source the
required environment in each command.

## What does Submitted mean?

The agent requested completion. It is not a proof verdict; use ReuF2F's independent
evaluator for acceptance. See [output files](usage/output_files.md).

{% include-markdown "_footer.md" %}
