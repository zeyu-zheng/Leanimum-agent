"""Set up the shared image's project for one ReuF2F task; no grading."""

import subprocess
import tempfile
from pathlib import Path

from leanimum.environments.docker import DockerEnvironment

GITIGNORE = ".lake/\n*.olean\n*.ilean\n*.trace\n"

# The shared image's project roots `Main`; each task roots its own module instead.
_SETUP = """set -euo pipefail
sed -i 's/^roots = \\["Main"\\]$/roots = ["{module}"]/' lakefile.toml
grep -qx 'roots = \\["{module}"\\]' lakefile.toml
printf '%s' '{gitignore}' > .gitignore
lake build {module}
git init -q && git add . && git -c user.name=reuf2f -c user.email=reuf2f@invalid commit -qm baseline
"""


def prepare_environment(env: DockerEnvironment, instance: dict) -> None:
    """Commit the challenge in /testbed, as a per-instance image would contain it."""
    module = instance["instance_id"]
    # Challenges can exceed the kernel's per-argument limit, so copy a file instead.
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"{module}.lean"
        source.write_text(instance["challenge"])
        subprocess.run(
            [env.config.executable, "cp", str(source), f"{env.container_id}:{env.config.cwd}/{source.name}"],
            check=True,
            capture_output=True,
            timeout=env.config.timeout,
        )
    out = env.execute({"command": _SETUP.format(module=module, gitignore=GITIGNORE)})
    if out["returncode"] != 0:
        raise RuntimeError(f"Error preparing ReuF2F environment: {out}")
