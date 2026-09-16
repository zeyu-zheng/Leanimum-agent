"""Real subprocess/replay tests: no mocked transport or model calls."""

import concurrent.futures
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from leanimum.config import get_config_from_spec
from leanimum.environments.docker import DockerEnvironment
from leanimum.environments.local import LocalEnvironment
from leanimum.models.test_models import make_output
from leanimum.run.benchmarks import reuf2f as runner
from leanimum.run.benchmarks.reuf2f import (
    filter_instances,
    process_instance,
    update_preds_file,
)
from leanimum.run.benchmarks.utils.batch_progress import RunBatchProgressManager
from leanimum.run.benchmarks.utils.reuf2f import (
    git,
    load_instances,
    prepare_environment,
    workspace_files,
)
from leanimum.utils.serialize import recursive_merge

PROJECT_CONFIG = 'name = "project"\ndefaultTargets = ["Project"]\n\n[[lean_lib]]\nname = "Project"\nroots = ["Main"]\n'
EMPTY_MANIFEST = json.dumps({"version": "1.2.0", "name": "project", "packagesDir": ".lake/packages", "packages": []})


def prepare_project(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "lean-toolchain").write_text("leanprover/lean4:v4.33.0\n")
    (path / "lakefile.toml").write_text(PROJECT_CONFIG)
    (path / "lake-manifest.json").write_text(EMPTY_MANIFEST)


@pytest.fixture
def release(tmp_path):
    root = tmp_path / "prepared tasks"
    records = []
    for name in ("first", "second"):
        workspace = root / "tasks" / name / "workspace"
        workspace.mkdir(parents=True)
        files = {
            f"{name}.lean": f"theorem {name}.target : True := by sorry\n"
            f"theorem {name}.target_neg : Not True := by sorry\n",
            "lean-toolchain": "leanprover/lean4:v4.33.0\n",
            "lakefile.toml": PROJECT_CONFIG.replace('["Main"]', f'["{name}"]'),
            "lake-manifest.json": json.dumps(
                {
                    "version": "1.2.0",
                    "name": "project",
                    "packagesDir": ".lake/packages",
                    "packages": [],
                }
            ),
            ".gitignore": ".lake/\n",
        }
        for path, text in files.items():
            (workspace / path).write_text(text)
        git(workspace, "init", "--quiet", "--initial-branch=main", "--template=")
        git(workspace, "add", ".")
        git(
            workspace,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "Baseline",
        )
        records.append(
            {
                "instance_id": name,
                "source_revision": "a" * 40,
                "base_commit": git(workspace, "rev-parse", "HEAD").decode().strip(),
                "source_file": f"{name}.lean",
                "problem_statement": f"In {name}.lean, prove {name}.target or {name}.target_neg. The unchosen theorem may remain sorry.",
            }
        )
    (root / "tasks.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
    return root


@pytest.fixture(params=["local", "docker"])
def backend_settings(request, tmp_path):
    if request.param == "docker":
        return {"environment": {"executable": request.getfixturevalue("container_executable")}}
    if not shutil.which("lake"):
        pytest.skip("Lean/Lake is required for local task preflight")
    prepared = tmp_path / "prepared environment"
    prepare_project(prepared)
    (prepared / "keep.txt").write_text("Do not modify the prepared project.\n")
    return {"environment": {"environment_class": "local", "cwd": str(prepared)}}


@pytest.fixture
def task_env(backend_settings):
    env = runner.get_reuf2f_environment(recursive_merge(get_config_from_spec("reuf2f"), backend_settings))
    try:
        yield env
    finally:
        if isinstance(env, DockerEnvironment):
            env.cleanup()
            env.container_id = None


def execute(env, command):
    result = env.execute({"command": command})
    assert result["returncode"] == 0, result
    return result["output"]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "leanimum.run.benchmarks.reuf2f", *args],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "LEANA_SILENT_STARTUP": "1"},
    )


def agent_config(outputs, **agent_overrides):
    return recursive_merge(
        get_config_from_spec("reuf2f"),
        {
            "agent": {"cost_limit": 0, **agent_overrides},
            "model": {
                "model_class": "deterministic",
                "model_name": "deterministic",
                "outputs": outputs,
            },
        },
    )


def finish():
    return make_output(
        "Finish",
        [{"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"}],
        cost=0,
    )


def make_patch():
    return make_output(
        "Create patch for the modified source files",
        [{"command": "git diff -- first.lean Helpers.lean Helpers/ > patch.txt"}],
        cost=0,
    )


def test_default_image_platform_and_no_host_mounts():
    from pydantic import ValidationError

    from leanimum.agents.default import AgentConfig

    config = get_config_from_spec("reuf2f")["environment"]
    assert config["image"] == "zeyuzhenghub/lean4:v4.33.0"
    assert config["environment_class"] == "docker" and config["cwd"] == "/testbed"
    assert config["run_args"] == ["--rm", "--platform", "linux/amd64"]
    assert config["timeout"] == 1200 and config["container_timeout"] == "3h"
    assert AgentConfig(**get_config_from_spec("reuf2f")["agent"]).wall_time_limit_seconds == 0
    # Keep required-image validation here with its owning configuration contract.
    with pytest.raises(ValidationError, match="image"):
        runner.get_reuf2f_environment({"environment": {"environment_class": "docker"}})


def test_docker_launch_uses_config_without_runner_defaults(tmp_path, caplog):
    caplog.set_level(logging.DEBUG, logger="leanimum.environment")
    config = recursive_merge(
        get_config_from_spec("reuf2f"),
        {
            "environment": {
                "image": "example/custom-lean:fixed",
                "cwd": "/custom",
                "run_args": ["--rm", "--platform", "linux/arm64"],
                "executable": str(tmp_path / "missing-docker"),
            },
        },
    )
    with pytest.raises(FileNotFoundError):
        runner.get_reuf2f_environment(config)
    assert "example/custom-lean:fixed" in caplog.text
    assert "-w /custom" in caplog.text and "--platform linux/arm64" in caplog.text
    assert "zeyuzhenghub/lean4" not in caplog.text and "linux/amd64" not in caplog.text


def test_release_selection_and_committed_inputs(release):
    instances = load_instances(release)
    assert filter_instances(instances, filter_spec="^sec", slice_spec="0:1") == instances[1:]
    original = workspace_files(instances[0])
    Path(instances[0]["workspace"], "first.lean").write_text("changed checkout")
    assert workspace_files(instances[0]) == original
    assert set(original) == {
        "first.lean",
        ".gitignore",
        "lean-toolchain",
        "lakefile.toml",
        "lake-manifest.json",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("instance_id", "../../outside"),
        ("base_commit", "HEAD"),
        ("source_revision", "not-a-hash"),
        ("problem_statement", ""),
        ("source_file", "../../outside.lean"),
        ("source_file", "lakefile.lean"),
        ("source_file", "Helpers.lean"),
        ("source_file", "task;echo bad.lean"),
    ],
)
def test_invalid_release_records(release, field, value):
    path = release / "tasks.jsonl"
    row = json.loads(path.read_text().splitlines()[0])
    path.write_text(json.dumps({**row, field: value}) + "\n")
    with pytest.raises(ValueError, match="Invalid"):
        load_instances(release)


@pytest.mark.parametrize(("instance_id",), [("first",), ("second",)])  # noqa: PT006
def test_real_bootstrap_minimal_workspace_and_local_commit(release, task_env, tmp_path, instance_id):
    instance = filter_instances(load_instances(release), filter_spec=f"^{instance_id}$")[0]
    baseline = workspace_files(instance)
    prepared = Path(task_env.config.cwd) if isinstance(task_env, LocalEnvironment) else None
    template = (prepared / "lakefile.toml").read_bytes() if prepared else None
    assert prepare_environment(task_env, instance, tmp_path / "run" / instance_id) is None
    if prepared is not None:
        assert (prepared / "keep.txt").read_text() == "Do not modify the prepared project.\n"
        assert {p.name for p in prepared.iterdir()} == {
            "lean-toolchain",
            "lakefile.toml",
            "lake-manifest.json",
            "keep.txt",
        }
        assert Path(task_env.config.cwd).is_relative_to(tmp_path / "run" / instance_id)
        assert (Path(task_env.config.cwd) / "lakefile.toml").read_bytes() == template.replace(
            b'["Main"]', f'["{instance_id}"]'.encode()
        )
    assert execute(task_env, "git rev-parse HEAD").strip() != instance["base_commit"]
    assert execute(task_env, "git rev-list --count HEAD").strip() == "1"
    for name, data in baseline.items():
        assert execute(task_env, f"cat {name}") == execute(task_env, f"git show HEAD:{name}") == data.decode()
    assert execute(task_env, "git status --porcelain") == ""
    assert set(execute(task_env, "ls -A").splitlines()) == set(baseline) | {
        ".git",
        ".lake",
    }
    execute(task_env, "lake build")


def test_missing_dependency_fails_before_model(release, task_env, tmp_path):
    instance = load_instances(release)[0]
    baseline = workspace_files(instance)
    manifest = json.loads(baseline["lake-manifest.json"])
    manifest["packages"] = [{"name": "missing", "type": "git", "rev": "a" * 40}]
    workspace = Path(instance["workspace"])
    (workspace / "lake-manifest.json").write_text(json.dumps(manifest))
    git(workspace, "add", "lake-manifest.json")
    git(
        workspace,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Missing dependency",
    )
    instance["base_commit"] = git(workspace, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(RuntimeError, match="Missing prepared dependency|Prepared dependency lock"):
        prepare_environment(task_env, instance, tmp_path / "run")
    execute(task_env, "test ! -e .git")


def test_large_task_input_does_not_use_shell_argument_payload(release, task_env, tmp_path):
    instance = load_instances(release)[0]
    workspace = Path(instance["workspace"])
    source = workspace / "first.lean"
    source.write_text(source.read_text() + "/-" + "x" * 200_000 + "-/\n")
    git(workspace, "add", "first.lean")
    git(
        workspace,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Large input",
    )
    instance["base_commit"] = git(workspace, "rev-parse", "HEAD").decode().strip()
    baseline = workspace_files(instance)
    prepare_environment(task_env, instance, tmp_path / "run")
    assert execute(task_env, "git rev-parse HEAD").strip() != instance["base_commit"]
    for name, data in baseline.items():
        assert execute(task_env, f"cat {name}") == execute(task_env, f"git show HEAD:{name}") == data.decode()


def test_failed_rerun_does_not_reuse_patch_or_trajectory(release, tmp_path, backend_settings):
    instance = load_instances(release)[0]
    output = tmp_path / "run"
    edit = make_output("Edit", [{"command": "printf '\n-- candidate\n' >> first.lean"}], cost=0)
    config = recursive_merge(agent_config([edit, make_patch(), finish()]), backend_settings)
    process_instance(instance, output, config, RunBatchProgressManager(1))
    assert (output / "first/first.traj.json").is_file()
    assert "+-- candidate" in json.loads((output / "preds.json").read_text())["first"]["model_patch"]
    config["run"] = {"env_startup_command": "exit 7"}
    process_instance(instance, output, config, RunBatchProgressManager(1))
    assert json.loads((output / "preds.json").read_text())["first"]["model_patch"] == ""
    assert not (output / "first/first.traj.json").exists()


def test_real_agent_flow_submits_ordinary_git_diff(release, tmp_path, backend_settings):
    instance = load_instances(release)[0]
    config = agent_config(
        [
            make_output(
                "Write candidate",
                [
                    {
                        "command": "printf 'theorem first.target : True := by trivial\ntheorem first.target_neg : Not True := by sorry\n' > first.lean; "
                        "mkdir -p Helpers; printf '%s\n' '-- untracked helper' > Helpers/New.lean; git add -N Helpers/New.lean"
                    }
                ],
                cost=0,
            ),
            make_patch(),
            finish(),
        ]
    )
    output = tmp_path / "run"
    progress = RunBatchProgressManager(1)
    process_instance(instance, output, recursive_merge(config, backend_settings), progress)
    result = json.loads((output / "preds.json").read_text())["first"]
    assert set(result) == {"instance_id", "model_name_or_path", "model_patch"}
    assert "+theorem first.target : True := by trivial" in result["model_patch"]
    assert "+-- untracked helper" in result["model_patch"]
    trajectory = json.loads((output / "first/first.traj.json").read_text())
    assert trajectory["info"]["exit_status"] == "Submitted" and progress.n_completed == 1
    assert trajectory["info"]["submission"] == result["model_patch"]
    assert trajectory["base_commit"] == instance["base_commit"]  # release identity, not container HEAD
    assert instance["base_commit"] not in trajectory["messages"][1]["content"]
    assert "In first.lean, prove first.target or first.target_neg" in trajectory["messages"][1]["content"]
    assert "git diff -- path/to/file1 path/to/file2 > patch.txt" in trajectory["messages"][1]["content"]
    assert "Main.lean" not in trajectory["messages"][1]["content"]
    assert trajectory["source_revision"] == instance["source_revision"]
    replay = tmp_path / "replay"
    replay.mkdir()
    for name, content in workspace_files(instance).items():
        (replay / name).write_bytes(content)
    git(replay, "init", "--quiet", "--template=")
    git(replay, "apply", "--check", "-", input=result["model_patch"].encode())
    git(replay, "apply", "-", input=result["model_patch"].encode())
    assert (replay / "Helpers/New.lean").read_text() == "-- untracked helper\n"
    assert "by trivial" in (replay / "first.lean").read_text()


@pytest.mark.parametrize(("operation",), [("stage",), ("commit",)])  # noqa: PT006
def test_agent_git_mistakes_are_not_recovered(release, tmp_path, backend_settings, operation):
    command = "printf '\n-- omitted edit\n' >> first.lean; git add first.lean"
    if operation == "commit":
        command += "; git -c user.name=Agent -c user.email=test@example.invalid commit -qm candidate"
    output = tmp_path / "run"
    process_instance(
        load_instances(release)[0],
        output,
        recursive_merge(
            agent_config(
                [
                    make_output("Stage or commit despite prompt", [{"command": command}], cost=0),
                    make_patch(),
                    finish(),
                ]
            ),
            backend_settings,
        ),
        RunBatchProgressManager(1),
    )
    prediction = json.loads((output / "preds.json").read_text())["first"]
    assert prediction["model_patch"] == ""
    trajectory = json.loads((output / "first/first.traj.json").read_text())
    assert trajectory["info"]["exit_status"] == "Submitted"
    cwd = Path(trajectory["info"]["config"]["environment"]["cwd"])
    if backend_settings["environment"].get("environment_class") == "local":
        assert cwd.is_relative_to(output / "first")
        assert "-- omitted edit" in (cwd / "first.lean").read_text()
    else:
        assert str(cwd) == "/testbed"


@pytest.mark.parametrize(
    ("case", "status"),
    [("error", "IndexError"), ("budget", "LimitsExceeded"), ("missing", "Submitted")],
)
def test_errors_and_budget_do_not_invent_a_patch(release, tmp_path, backend_settings, case, status):
    instance = load_instances(release)[0]
    edit = make_output(
        "Edit without submission",
        [{"command": "printf '\n-- unsent change\n' >> first.lean"}],
        cost=0,
    )
    outputs = [edit]
    if case == "missing":
        outputs = [
            make_output("Remove", [{"command": "rm first.lean"}], cost=0),
            make_patch(),
            finish(),
        ]
    output = tmp_path / "run"
    progress = RunBatchProgressManager(1)
    process_instance(
        instance,
        output,
        recursive_merge(
            agent_config(outputs, step_limit=1 if case == "budget" else 5),
            backend_settings,
        ),
        progress,
    )
    trajectory = json.loads((output / "first/first.traj.json").read_text())
    assert trajectory["info"]["exit_status"] == status
    assert progress._instances_by_exit_status[status] == ["first"]
    patch = json.loads((output / "preds.json").read_text())["first"]["model_patch"]
    assert "deleted file" in patch if case == "missing" else patch == ""


def test_submitted_text_is_not_treated_as_a_verdict(release, tmp_path, backend_settings):
    output = tmp_path / "run"
    config = agent_config(
        [
            make_output(
                "Claim success",
                [{"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT; echo accepted"}],
                cost=0,
            )
        ]
    )
    process_instance(
        load_instances(release)[0],
        output,
        recursive_merge(config, backend_settings),
        RunBatchProgressManager(1),
    )
    prediction = json.loads((output / "preds.json").read_text())["first"]
    assert prediction["model_patch"] == "accepted\n"
    assert set(prediction) == {"instance_id", "model_name_or_path", "model_patch"}


def test_missing_patch_file_does_not_submit(release, tmp_path, backend_settings):
    output = tmp_path / "run"
    process_instance(
        load_instances(release)[0],
        output,
        recursive_merge(agent_config([finish()], step_limit=1), backend_settings),
        RunBatchProgressManager(1),
    )
    assert json.loads((output / "preds.json").read_text())["first"]["model_patch"] == ""
    trajectory = json.loads((output / "first/first.traj.json").read_text())
    assert trajectory["info"]["exit_status"] == "LimitsExceeded"


def test_missing_docker_never_falls_back(release, tmp_path):
    output = tmp_path / "run"
    config = recursive_merge(
        agent_config([]),
        {"environment": {"executable": str(tmp_path / "missing-docker")}},
    )
    progress = RunBatchProgressManager(1)
    process_instance(load_instances(release)[0], output, config, progress)
    assert json.loads((output / "preds.json").read_text())["first"]["model_patch"] == ""
    assert progress._instances_by_exit_status["FileNotFoundError"] == ["first"]
    assert not list(output.glob("*/workspace-*"))
    assert not (output / "first/first.traj.json").exists()


@pytest.mark.parametrize(
    ("environment_class",),  # noqa: PT006
    [
        ("singularity",),
        ("swerex_modal",),
        ("contree",),
        ("swerex_docker",),
        ("bubblewrap",),
    ],
)  # noqa: PT006
def test_unconnected_backend_is_rejected(release, tmp_path, environment_class):
    output = tmp_path / "run"
    config = recursive_merge(agent_config([]), {"environment": {"environment_class": environment_class}})
    with pytest.raises(ValueError, match="support only docker and local"):
        runner.get_reuf2f_environment(config)
    progress = RunBatchProgressManager(1)
    process_instance(load_instances(release)[0], output, config, progress)
    assert progress._instances_by_exit_status["ValueError"] == ["first"]
    assert json.loads((output / "preds.json").read_text())["first"]["model_patch"] == ""
    assert not list(output.glob("*/*.traj.json"))


def test_predictions_thread_safe(tmp_path):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda i: update_preds_file(tmp_path / "preds.json", str(i), "model", "patch"),
                range(20),
            )
        )
    assert len(json.loads((tmp_path / "preds.json").read_text())) == 20


def test_cli_output_cannot_overwrite_release(release):
    assert run_cli("--subset", str(release), "-o", str(release / "bad")).returncode != 0


def test_cli_has_only_current_options():
    from typer.main import get_command

    assert {param.name for param in get_command(runner.app).params} == {
        "subset",
        "slice_spec",
        "filter_spec",
        "shuffle",
        "output",
        "workers",
        "model",
        "model_class",
        "redo_existing",
        "config_spec",
        "environment_class",
    }


def test_cli_filter_slice_use_selection_without_launch(release, tmp_path):
    # All selected IDs are already recorded, so no model or environment is created.
    output = tmp_path / "existing"
    output.mkdir()
    predictions = {"second": {"instance_id": "second", "model_name_or_path": "fixture", "model_patch": ""}}
    (output / "preds.json").write_text(json.dumps(predictions))
    result = run_cli("--subset", str(release), "--filter", "^second$", "--slice", "0:1", "-o", str(output))
    assert result.returncode == 0, result.stderr
    assert json.loads((output / "preds.json").read_text()) == predictions
    assert not list(output.glob("*/*.traj.json"))
    assert "Running on 0 instances" in (output / "leanimum.log").read_text()


def test_cli_accepts_image_override_through_config(release, tmp_path, caplog):
    output = tmp_path / "run"
    caplog.set_level(logging.DEBUG, logger="leanimum.environment")
    runner.app(
        [
            "--subset",
            str(release),
            "--slice",
            "0:1",
            "-o",
            str(output),
            "-c",
            "reuf2f.yaml",
            "-c",
            "environment.image=example/override:fixed",
            "-c",
            f"environment.executable={tmp_path / 'missing-docker'}",
            "-c",
            "model.outputs=[]",
            "--model-class",
            "deterministic",
            "-m",
            "deterministic",
        ],
        standalone_mode=False,
    )
    assert "example/override:fixed" in caplog.text
    assert "--platform linux/amd64" in caplog.text and "-w /testbed" in caplog.text
    assert set(json.loads((output / "preds.json").read_text())) == {"first"}


def test_cli_resume_and_redo(release, tmp_path, backend_settings):
    config = tmp_path / "deterministic.yaml"
    config.write_text(
        yaml.safe_dump(
            recursive_merge(
                agent_config(
                    [
                        make_output(
                            "Create empty patch",
                            [{"command": "git diff -- '*.lean' > patch.txt"}],
                            cost=0,
                        ),
                        finish(),
                    ]
                ),
                backend_settings,
            )
        )
    )
    output = tmp_path / "batch"
    args = ["--subset", str(release), "-c", str(config), "-w", "2", "-o", str(output)]
    result = run_cli(*args)
    assert result.returncode == 0, result.stderr
    assert len(json.loads((output / "preds.json").read_text())) == 2
    before = {p: p.read_bytes() for p in output.glob("*/*.traj.json")}
    assert len(before) == 2
    assert run_cli(*args).returncode == 0
    assert before == {p: p.read_bytes() for p in before}
    assert run_cli(*args, "--redo-existing").returncode == 0
    assert len(list(output.glob("*/*.traj.json"))) == 2
    if backend_settings["environment"].get("environment_class") == "local":
        assert len(list(output.glob("*/workspace-*"))) == 4
    else:
        assert not list(output.glob("*/workspace-*"))


@pytest.mark.parametrize(("backend",), [("local",), ("docker",)])  # noqa: PT006
def test_cli_can_select_backend_with_no_selected_tasks(release, tmp_path, backend):
    output = tmp_path / backend
    result = run_cli("--subset", str(release), "--slice", "0:0", "-o", str(output), "--environment-class", backend)
    assert result.returncode == 0, result.stderr
    assert not list(output.glob("*/*.traj.json"))
    assert not (output / "preds.json").exists()


def test_local_backend_factory_uses_existing_class(tmp_path):
    config = recursive_merge(
        get_config_from_spec("reuf2f"),
        {
            "environment": {"environment_class": "local", "cwd": str(tmp_path)},
        },
    )
    env = runner.get_reuf2f_environment(config)
    assert isinstance(env, LocalEnvironment)
    assert env.config.cwd == str(tmp_path)
    assert execute(env, "pwd").strip() == str(tmp_path.resolve())


def test_local_wrong_toolchain_does_not_change_host_project(release, tmp_path):
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "lean-toolchain").write_text("leanprover/lean4:v4.0.0\n")
    (prepared / "keep.txt").write_text("keep")
    env = LocalEnvironment(cwd=str(prepared))
    before = {p.name: p.read_bytes() for p in prepared.iterdir()}
    with pytest.raises(ValueError, match="toolchain does not match"):
        prepare_environment(env, load_instances(release)[0], tmp_path / "run")
    assert before == {p.name: p.read_bytes() for p in prepared.iterdir()}
    assert not (tmp_path / "run").exists()


def test_cli_local_override_uses_fresh_workspace(release, tmp_path):
    if not shutil.which("lake"):
        pytest.skip("Lean/Lake is required")
    prepared = tmp_path / "prepared"
    prepare_project(prepared)
    config = tmp_path / "model.yaml"
    config.write_text(yaml.safe_dump(agent_config([make_patch(), finish()])))
    output = tmp_path / "run"
    result = run_cli(
        "--subset",
        str(release),
        "--slice",
        "0:1",
        "--environment-class",
        "local",
        "-c",
        str(config),
        "-c",
        f"environment.cwd={prepared}",
        "-o",
        str(output),
    )
    assert result.returncode == 0, result.stderr
    trajectory = json.loads((output / "first/first.traj.json").read_text())
    assert trajectory["info"]["exit_status"] == "Submitted"
    assert Path(trajectory["info"]["config"]["environment"]["cwd"]).is_relative_to(output / "first")
    assert {p.name for p in prepared.iterdir()} == {"lean-toolchain", "lakefile.toml", "lake-manifest.json"}
    assert set(json.loads((output / "preds.json").read_text())) == {"first"}


def test_local_dependency_revisions_are_checked(release, tmp_path):
    prepared = tmp_path / "prepared"
    dependency = prepared / ".lake/packages/dependency"
    prepare_project(prepared)
    dependency.mkdir(parents=True)
    (dependency / "README").write_text("dependency fixture")
    git(dependency, "init", "--quiet", "--template=")
    git(dependency, "add", ".")
    git(
        dependency,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Initial",
    )
    original = git(dependency, "rev-parse", "HEAD")
    instance = load_instances(release)[0]
    workspace = Path(instance["workspace"])
    manifest = json.loads((workspace / "lake-manifest.json").read_text())
    manifest["packages"] = [{"name": "dependency", "type": "git", "rev": "0" * 40}]
    (workspace / "lake-manifest.json").write_text(json.dumps(manifest))
    git(workspace, "add", "lake-manifest.json")
    git(
        workspace,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Bad lock",
    )
    instance["base_commit"] = git(workspace, "rev-parse", "HEAD").decode().strip()
    (prepared / "lake-manifest.json").write_text(json.dumps(manifest))
    env = LocalEnvironment(cwd=str(prepared))
    with pytest.raises(RuntimeError, match="Dependency revision mismatch"):
        prepare_environment(env, instance, tmp_path / "run")
    assert git(dependency, "rev-parse", "HEAD") == original
    assert (Path(env.config.cwd) / ".lake/packages").resolve() == (prepared / ".lake/packages").resolve()
    assert not (Path(env.config.cwd) / ".git").exists()


def test_agent_can_add_own_library_and_submit_toml(release, tmp_path):
    if not shutil.which("lake"):
        pytest.skip("Lean/Lake required")
    prepared = tmp_path / "prepared"
    prepare_project(prepared)
    commands = [
        make_output(
            "Add auxiliary source",
            [
                {
                    "command": "mkdir -p Support; printf 'theorem support : True := by trivial\\n' > Support/Facts.lean; printf '\\n[[lean_lib]]\\nname = \"Support\"\\n' >> lakefile.toml; printf 'import Support.Facts\\ntheorem first.target : True := by exact support\\ntheorem first.target_neg : Not True := by sorry\\n' > first.lean; lake build"
                }
            ],
            cost=0,
        ),
        make_output(
            "Create patch",
            [
                {
                    "command": "git add -N Support/Facts.lean; git diff -- first.lean lakefile.toml Support/Facts.lean > patch.txt"
                }
            ],
            cost=0,
        ),
        finish(),
    ]
    config = recursive_merge(
        agent_config(commands), {"environment": {"environment_class": "local", "cwd": str(prepared)}}
    )
    output = tmp_path / "run"
    process_instance(load_instances(release)[0], output, config, RunBatchProgressManager(1))
    patch = json.loads((output / "preds.json").read_text())["first"]["model_patch"]
    assert "diff --git a/lakefile.toml b/lakefile.toml" in patch
    assert "Support/Facts.lean" in patch and "exact support" in patch
    trajectory = json.loads((output / "first/first.traj.json").read_text())
    assert trajectory["info"]["exit_status"] == "Submitted"
    assert (prepared / "lakefile.toml").read_text() == PROJECT_CONFIG


def test_prepared_template_mismatch_fails_without_replacing_configs(release, tmp_path):
    prepared = tmp_path / "prepared"
    prepare_project(prepared)
    (prepared / "lakefile.toml").write_text(PROJECT_CONFIG + '\n[[lean_lib]]\nname = "Unexpected"\n')
    before = {p.name: p.read_bytes() for p in prepared.iterdir()}
    env = LocalEnvironment(cwd=str(prepared))
    with pytest.raises(RuntimeError, match="does not match the released image recipe"):
        prepare_environment(env, load_instances(release)[0], tmp_path / "attempt")
    assert {p.name: p.read_bytes() for p in prepared.iterdir()} == before
    assert list(Path(env.config.cwd).iterdir()) == []


@pytest.mark.parametrize(("explicit",), [(False,), (True,)])  # noqa: PT006
def test_output_defaults_to_cwd_and_can_be_overridden(release, tmp_path, explicit):
    working = tmp_path / "invocation"
    working.mkdir()
    output = tmp_path / "chosen-output" if explicit else working
    args = ["--subset", str(release), "--slice", "0:0"]
    if explicit:
        args += ["-o", str(output)]
    result = subprocess.run(
        [sys.executable, "-m", "leanimum.run.benchmarks.reuf2f", *args],
        cwd=working,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "LEANA_SILENT_STARTUP": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert (output / "leanimum.log").is_file()
    if explicit:
        assert not (working / "leanimum.log").exists()


def test_model_initialization_failure_does_not_write_prediction(release, tmp_path):
    output = tmp_path / "run"
    instance = load_instances(release)[0]
    output.mkdir()
    update_preds_file(output / "preds.json", "other", "fixture", "patch")
    update_preds_file(output / "preds.json", "first", "fixture", "old patch")
    (output / "first").mkdir()
    (output / "first/first.traj.json").write_text("old trajectory")
    config = recursive_merge(agent_config([]), {"model": {"model_class": "missing_model_package.Unknown"}})
    with pytest.raises(ValueError, match="Unknown model class"):
        process_instance(instance, output, config, RunBatchProgressManager(1))
    assert set(json.loads((output / "preds.json").read_text())) == {"other"}
    assert not (output / "first/first.traj.json").exists()
    assert not list((output / "first").glob("workspace-*"))


def test_cli_retries_model_initialization_failure_without_redo(release, tmp_path):
    output = tmp_path / "run"
    args = [
        "--subset",
        str(release),
        "-w",
        "2",
        "-o",
        str(output),
        "--model-class",
        "missing_model_package.Unknown",
        "-m",
        "fixture",
    ]
    for _ in range(2):
        result = run_cli(*args)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Unknown model class" in result.stdout + result.stderr
        assert not (output / "preds.json").exists()
        assert not list(output.glob("*/*.traj.json"))
        statuses = yaml.safe_load(max(output.glob("exit_statuses_*.yaml")).read_text())
        assert sorted(statuses["instances_by_exit_status"]["Uncaught ValueError"]) == ["first", "second"]
