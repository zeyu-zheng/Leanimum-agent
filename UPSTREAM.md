# Upstream provenance and synchronization

Leanimum-agent is derived from mini-SWE-agent. Its complete Git history is
retained rather than importing a source snapshot into an unrelated history.

- Development repository: `https://github.com/zeyu-zheng/Leanimum-agent`
- Upstream repository: `https://github.com/SWE-agent/mini-swe-agent`
- Initial upstream commit: `04d809ceab9df28f9adaed044884180159172930`
- Inherited package version: `2.4.6`

## Initial scope

The initial changes establish the `Leanimum-agent` display name,
`leanimum-agent` distribution, `leanimum` Python package, and `leani` CLI.
Imports, packaging references, tests, and user-facing names are updated together.

Agent behavior, prompts, tool protocols, model backends, environments (including
SWE-ReX), benchmark runners, dependency requirements, configuration variables,
and the trajectory format are otherwise unchanged. The upstream CLI aliases
remain available. Existing upstream issue links and historical references are
retained where they explain inherited behavior.

The documentation site in `docs/` remains inherited upstream reference material;
it has not yet been rewritten as a Lean workflow guide.

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
