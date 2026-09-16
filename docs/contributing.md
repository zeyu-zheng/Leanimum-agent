# ❤️ Contributing

We happily accept contributions!

## Areas of help

- Documentation, examples, tutorials, etc. In particular, we're looking for
    - examples of how this library is used in the wild
    - additional examples for the [cookbook](advanced/cookbook.md)
- Support for more models (anything where `litellm` doesn't work out of the box)
- Support for more environments & deployments (e.g., run it as a github action, etc.)
- Take a look at the [issues](https://github.com/zeyu-zheng/Leanimum-agent/issues) and look for issues marked `good-first-issue` or `help-wanted` (please read the guidelines below first)

## Design & Architecture

- Leanimum-agent aims to stay minimalistic, hackable, and of high quality code.
- To extend features, we prefer to add a new version of one of the four components (see [cookbook](advanced/cookbook.md)), rather than making the existing components more complex.
- Components should be relatively self-contained, but if there are utilities that might be shared, add a `utils` folder (like [this one](https://github.com/zeyu-zheng/Leanimum-agent/tree/main/src/leanimum/models/utils)). But keep it simple!
- If your component is a bit more specific, add it into an `extra` folder (like [this one](https://github.com/zeyu-zheng/Leanimum-agent/tree/main/src/leanimum/models/extra))
- Our target audience is anyone who doesn't shy away from modifying a bit of code (especially a run script) to get what they want.
- Therefore, not everything needs to be configurable with the config files, but it should be easy to create a run script that makes use of it.
- Many LMs write very verbose code -- please clean it up! Same goes for the tests. They should still be concise and readable.
- Run `pre-commit` before committing to check formatting and lint rules.

## Development setup

Start with the source checkout and virtual environment from the
[quickstart](quickstart.md). Install the full dependencies to include the optional
model and environment adapters imported by the test suite:

```bash
pip install -e '.[full]'
pre-commit install
pytest -n auto --ignore=tests/test_fire.py
```

`-n auto` runs tests across available CPU cores. `.[dev]` is sufficient for the
core development tools and documentation, but does not include every backend
needed to collect the full suite.

Container tests need their runtimes and may skip when unavailable. A skipped
integration test does not validate deployment. Real-model tests are separate;
they require `--run-fire`, provider credentials and may incur charges.

Build the documentation locally:

```bash
mkdocs build --strict
```

{% include-markdown "_footer.md" %}
