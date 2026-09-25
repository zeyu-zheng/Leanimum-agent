"""CLI dispatch and configuration using real agents with deterministic responses."""

import json
import re
import subprocess
import sys
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from leanimum.config import get_config_from_spec
from leanimum.models.test_models import make_output
from leanimum.run.mini import app


def strip_ansi_codes(text: str) -> str:
    return re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)


@pytest.fixture
def cli_config(tmp_path, monkeypatch, reset_global_stats):
    monkeypatch.setenv("LEANA_CONFIGURED", "true")
    config = get_config_from_spec("mini")
    config["agent"].update(step_limit=1, cost_limit=2.5, whitelist_actions=[".*"])
    config["environment"]["cwd"] = str(tmp_path)
    config["model"] = {
        "model_class": "deterministic",
        "model_name": "configured-model",
        "cost_per_call": 0,
        "outputs": [
            make_output(
                "Check workspace",
                [{"command": "printf 'checked\\n' > result.txt; printf 'fixture output\\n'"}],
                cost=0,
            )
        ],
    }
    path = tmp_path / "agent.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


@pytest.mark.parametrize(
    ("arguments", "mode", "confirm_exit", "cost_limit", "model_name"),
    [
        ([], "confirm", True, 2.5, "configured-model"),
        (["--yolo"], "yolo", True, 2.5, "configured-model"),
        (["--exit-immediately"], "confirm", False, 2.5, "configured-model"),
        (["--cost-limit", "0"], "confirm", True, 0, "configured-model"),
        (["--model", "cli-model"], "confirm", True, 2.5, "cli-model"),
    ],
)
def test_cli_options_reach_real_components(cli_config, tmp_path, arguments, mode, confirm_exit, cost_limit, model_name):
    output = tmp_path / "run.traj.json"
    result = CliRunner().invoke(app, ["-c", str(cli_config), "-t", "Check the task", "-o", str(output), *arguments])
    assert result.exit_code == 0, result.output
    trajectory = json.loads(output.read_text())
    config = trajectory["info"]["config"]
    assert config["agent_type"] == "leanimum.agents.interactive.InteractiveAgent"
    assert config["agent"]["mode"] == mode
    assert config["agent"]["confirm_exit"] is confirm_exit
    assert config["agent"]["cost_limit"] == cost_limit
    assert config["model_type"] == "leanimum.models.test_models.DeterministicModel"
    assert config["model"]["model_name"] == model_name
    assert config["environment_type"] == "leanimum.environments.local.LocalEnvironment"
    assert config["environment"]["cwd"] == str(tmp_path)
    assert trajectory["info"]["exit_status"] == "LimitsExceeded"
    assert trajectory["info"]["model_stats"]["api_calls"] == 1
    assert "Check the task" in trajectory["messages"][1]["content"]
    assert (tmp_path / "result.txt").read_text() == "checked\n"


def test_configure_if_first_time_called(cli_config, tmp_path):
    with patch("leanimum.run.mini.configure_if_first_time") as configure:
        result = CliRunner().invoke(app, ["-c", str(cli_config), "-t", "Check", "-o", str(tmp_path / "run.json")])
    assert result.exit_code == 0, result.output
    configure.assert_called_once_with()


def test_cli_prompts_when_task_is_omitted(cli_config, tmp_path):
    output = tmp_path / "run.traj.json"
    with patch("leanimum.run.mini._multiline_prompt", return_value="User provided task") as prompt:
        result = CliRunner().invoke(app, ["-c", str(cli_config), "-o", str(output)])
    assert result.exit_code == 0, result.output
    prompt.assert_called_once_with()
    assert "User provided task" in json.loads(output.read_text())["messages"][1]["content"]


def test_output_file_records_submission(cli_config, tmp_path):
    config = yaml.safe_load(cli_config.read_text())
    config["agent"].update(step_limit=2, output_path=str(tmp_path / "unused.traj.json"))
    config["model"]["outputs"].append(
        make_output(
            "Submit", [{"command": "printf 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\\nfixture patch\\n'"}], cost=0
        )
    )
    cli_config.write_text(yaml.safe_dump(config))
    output = tmp_path / "results/task.traj.json"
    result = CliRunner().invoke(
        app, ["-c", str(cli_config), "-t", "Check", "-o", str(output), "--yolo", "--exit-immediately"]
    )
    assert result.exit_code == 0, result.output
    trajectory = json.loads(output.read_text())
    assert trajectory["info"]["exit_status"] == "Submitted"
    assert trajectory["info"]["submission"] == "fixture patch\n"
    assert trajectory["messages"][-1]["role"] == "exit"
    assert trajectory["info"]["model_stats"]["api_calls"] == 2
    assert trajectory["trajectory_format"] == "leanimum-agent-1.1"
    assert (tmp_path / "result.txt").read_text() == "checked\n"
    assert not (tmp_path / "unused.traj.json").exists()


def test_python_module_help():
    result = subprocess.run([sys.executable, "-m", "leanimum", "--help"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    output = strip_ansi_codes(result.stdout)
    assert "Run Leanimum-agent in your local environment." in output
    for option in ("--config", "--model", "--task", "--yolo", "--output", "--help"):
        assert option in output


@pytest.mark.parametrize(
    ("command", "expected_text"),
    [
        ("leani", "Run Leanimum-agent in your local environment."),
        ("leanimum-agent", "Run Leanimum-agent in your local environment."),
        ("leani-extra", "central entry point for all extra commands"),
        ("leani-e", "central entry point for all extra commands"),
    ],
)
def test_renamed_command_help(command: str, expected_text: str):
    result = subprocess.run([command, "--help"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert expected_text in strip_ansi_codes(result.stdout)


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("config", "setup"),
        ("inspect", "--no-reasoning"),
        ("i", "--no-reasoning"),
        ("inspector", "--no-reasoning"),
        ("reuf2f", "--subset"),
    ],
)
def test_extra_subcommand_help(alias, expected):
    result = subprocess.run(["leani-extra", alias, "--help"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    output = strip_ansi_codes(result.stdout)
    assert expected in output and "--help" in output
