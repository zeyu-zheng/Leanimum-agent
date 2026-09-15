"""Prepare isolated task copies for Docker or explicit local execution; no grading."""

import base64
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from leanimum.environments.docker import DockerEnvironment
from leanimum.environments.local import LocalEnvironment

CONFIG_FILES = {"lean-toolchain", "lakefile.toml", "lake-manifest.json", ".gitignore"}


def git(cwd: Path, *args: str, **kwargs) -> bytes:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.autocrlf=false",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        timeout=60,
        **kwargs,
    ).stdout


def load_instances(tasks: Path) -> list[dict]:
    tasks = tasks.expanduser().resolve()
    records = {}
    fields = {
        "instance_id",
        "base_commit",
        "source_revision",
        "problem_statement",
        "source_file",
    }
    for line in (tasks / "tasks.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (
            not isinstance(row, dict)
            or set(row) != fields
            or any(not isinstance(v, str) or not v for v in row.values())
        ):
            raise ValueError("Invalid prepared task record")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", row["instance_id"]) or any(
            not re.fullmatch(r"[0-9a-f]{40}", row[k]) for k in ("base_commit", "source_revision")
        ):
            raise ValueError("Invalid prepared task identity")
        if row["instance_id"] in records:
            raise ValueError("Duplicate task instance_id")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\.lean", row["source_file"]) or row["source_file"] in {
            "lakefile.lean",
            "Mathlib.lean",
            "Helpers.lean",
            "Challenge.lean",
            "Solution.lean",
        }:
            raise ValueError("Invalid task source_file")
        records[row["instance_id"]] = {
            **row,
            "workspace": str(tasks / "tasks" / row["instance_id"] / "workspace"),
        }
    if not records:
        raise ValueError("Empty task release")
    return list(records.values())


def workspace_files(instance: dict) -> dict[str, bytes]:
    """Read the release commit, never its mutable working tree or agent Git state."""
    workspace, commit = Path(instance["workspace"]), instance["base_commit"]
    expected = CONFIG_FILES | {instance["source_file"]}
    files = {}
    for entry in filter(None, git(workspace, "ls-tree", "-rz", commit).split(b"\0")):
        info, name = entry.decode().split("\t", 1)
        if not info.startswith("100644 blob ") or name not in expected:
            raise ValueError("Unexpected file in prepared task baseline")
        files[name] = git(workspace, "show", f"{commit}:{name}")
    if files.keys() != expected:
        raise ValueError("Incomplete prepared task baseline")
    return files


# Runs before the model starts. Transport source, not replacement project configs.
_BOOTSTRAP = r"""
import base64, hashlib, json, os, pathlib, re, shutil, subprocess, sys
input_path = pathlib.Path(sys.argv[1])
payload = json.loads(input_path.read_text())
input_path.unlink()
root = pathlib.Path.cwd()
prepared = pathlib.Path(payload["prepared"]) if payload["local"] else root
if not payload["local"] and root != pathlib.Path("/testbed"):
    raise RuntimeError("Shared-image workspace must be /testbed")
source_file = payload["source_file"]
expected = payload["toolchain"]
if (prepared / "lean-toolchain").read_text().strip() != expected:
    raise RuntimeError("Prepared toolchain does not match the task release")
if (prepared / "lakefile.lean").exists():
    raise RuntimeError("Expected image lakefile.toml, not lakefile.lean")
text = (prepared / "lakefile.toml").read_text()
pattern = r'(?m)^(roots\s*=\s*\[\s*)"Main"(\s*\]\s*(?:#.*)?)$'
text, count = re.subn(pattern, lambda m: m[1] + json.dumps(source_file[:-5]) + m[2], text)
if count != 1 or hashlib.sha256(text.encode()).hexdigest() != payload["lakefile_sha256"]:
    raise RuntimeError("Prepared lakefile.toml does not match the released image recipe")
manifest_bytes = (prepared / "lake-manifest.json").read_bytes()
manifest = json.loads(manifest_bytes)
if manifest["packagesDir"] != ".lake/packages":
    raise RuntimeError("Unexpected dependency directory")
if sorted(manifest["packages"], key=lambda p: p["name"]) != payload["packages"]:
    raise RuntimeError("Prepared dependency lock does not match the task release")
if payload["local"]:
    if any(root.iterdir()):
        raise RuntimeError("Local task workspace must be fresh")
    (root / "lean-toolchain").write_bytes((prepared / "lean-toolchain").read_bytes())
    (root / "lake-manifest.json").write_bytes(manifest_bytes)
    if (prepared / ".lake/packages").is_dir():
        (root / ".lake").mkdir()
        (root / ".lake/packages").symlink_to((prepared / ".lake/packages").resolve(), target_is_directory=True)
else:
    for p in root.iterdir():
        if p.name not in {".lake", "lakefile.toml", "lake-manifest.json", "lean-toolchain"}:
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            else:
                p.unlink()
(root / "lakefile.toml").write_text(text)
(root / source_file).write_bytes(base64.b64decode(payload["source"]))
(root / ".gitignore").write_bytes(base64.b64decode(payload["gitignore"]))
initial = {name: (root / name).read_bytes() for name in (source_file, "lakefile.toml", "lake-manifest.json", "lean-toolchain", ".gitignore")}
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
def git(*args, cwd=root):
    return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null",
        "-c", "core.autocrlf=false", *args], cwd=cwd, env=env)
for p in manifest["packages"]:
    if p["type"] != "git" or pathlib.Path(p["name"]).name != p["name"]:
        raise RuntimeError("Expected locked git dependency")
    directory = root / manifest["packagesDir"] / p["name"]
    if not directory.is_dir():
        raise RuntimeError("Missing prepared dependency: " + p["name"])
    if git("rev-parse", "HEAD", cwd=directory).decode().strip() != p["rev"]:
        raise RuntimeError("Dependency revision mismatch: " + p["name"])
    if git("status", "--porcelain", "--untracked-files=no", cwd=directory).strip():
        raise RuntimeError("Modified dependency: " + p["name"])
version = subprocess.check_output(["lean", "--version"], text=True)
if not re.search(r"version " + re.escape(expected.rsplit(":v", 1)[1]) + r"(?:,|\s)", version):
    raise RuntimeError("Running Lean does not match release toolchain: " + version)
subprocess.run(["lake", "build", source_file[:-5]], check=True)
for name, content in initial.items():
    if (root / name).read_bytes() != content:
        raise RuntimeError("Preflight changed task files: " + name)
git("init", "--quiet", "--initial-branch=main", "--object-format=sha1", "--template=")
git("add", "--", *sorted(initial))
git("-c", "user.name=Leanimum", "-c", "user.email=agent@leanimum.invalid",
    "-c", "commit.gpgsign=false", "commit", "--quiet", "--no-verify", "-m", "Initial task")
"""


def prepare_environment(
    env: DockerEnvironment | LocalEnvironment,
    instance: dict,
    instance_dir: Path,
) -> None:
    files = workspace_files(instance)
    payload = {
        "source": base64.b64encode(files[instance["source_file"]]).decode(),
        "gitignore": base64.b64encode(files[".gitignore"]).decode(),
        "lakefile_sha256": hashlib.sha256(files["lakefile.toml"]).hexdigest(),
        "toolchain": files["lean-toolchain"].decode().strip(),
        "packages": sorted(json.loads(files["lake-manifest.json"])["packages"], key=lambda p: p["name"]),
        "source_file": instance["source_file"],
        "local": isinstance(env, LocalEnvironment),
    }
    if isinstance(env, LocalEnvironment):
        prepared = Path(env.config.cwd or ".").expanduser().resolve()
        if (prepared / "lean-toolchain").read_bytes() != files["lean-toolchain"]:
            raise ValueError("Local environment.cwd toolchain does not match the task release")
        payload["prepared"] = str(prepared)
        instance_dir.mkdir(parents=True, exist_ok=True)
        env.config.cwd = tempfile.mkdtemp(prefix="workspace-", dir=instance_dir.resolve())
    elif not isinstance(env, DockerEnvironment):
        raise ValueError("ReuF2F task transport supports only docker and local")
    # Source statements can exceed Linux's per-argument limit. Copy the input
    # file, not a giant shell argument; bootstrap removes it before agent launch.
    with tempfile.TemporaryDirectory(prefix="leanimum-input-") as temporary:
        input_path = Path(temporary) / "input.json"
        input_path.write_text(json.dumps(payload))
        target = str(input_path)
        interpreter = sys.executable
        if isinstance(env, DockerEnvironment):
            target = f"/tmp/{Path(temporary).name}.json"
            interpreter = "python3"
            subprocess.run(
                [
                    env.config.executable,
                    "cp",
                    str(input_path),
                    f"{env.container_id}:{target}",
                ],
                check=True,
                capture_output=True,
                timeout=env.config.timeout,
            )
        out = env.execute({"command": shlex.join([interpreter, "-c", _BOOTSTRAP, target])})

    if out["returncode"] != 0:
        raise RuntimeError(f"Error preparing ReuF2F environment: {out}")
