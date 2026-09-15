# Leanimum-agent

Leanimum-agent is a minimal bash-only assistant for Lean proofs and programs,
derived from mini-SWE-agent. It searches libraries, edits files, and iterates on
compiler output through one model-facing `bash` tool.

- [Quick start](quickstart.md): install from source and run a Lean task.
- [ReuF2F](usage/reuf2f.md): the only built-in benchmark, using a separate local checkout.
- [Configuration](advanced/yaml_configuration.md): tool-call and text-based Lean prompts.
- [Execution environments](advanced/environments.md): retained local and remote backends.
- [Trajectories and outputs](usage/output_files.md): inspect runs without confusing submission with acceptance.

Comparator remains an external CLI. Prompts describe how to reuse or prepare
compatible tools and invoke them through bash. A trusted final verdict requires
independent verification, not an agent's self-report.

The ReuF2F runner defaults to one Linux Docker container per instance, following
the upstream batch runner. Use the benchmark's documented verifier in a separate
trusted environment for final scoring. No Leanimum-agent benchmark score is claimed here.

The [upstream project](https://github.com/SWE-agent/mini-swe-agent) provides the
underlying agent architecture. Upstream performance claims are not Lean results.
