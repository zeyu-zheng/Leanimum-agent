import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from leanimum import package_dir
from leanimum.environments.docker import DockerEnvironment
from leanimum.models.test_models import DeterministicModel, make_output
from leanimum.run.benchmarks.reuf2f import (
    filter_instances,
    get_reuf2f_environment,
    main,
    remove_from_preds_file,
    update_preds_file,
)
from leanimum.run.benchmarks.utils.reuf2f import prepare_environment

CONFIG = str(package_dir / "config" / "benchmarks" / "reuf2f.yaml")
INSTANCE = {
    "instance_id": "first",
    "declaration": "first.target",
    "problem_statement": "In first.lean, prove either first.target or refute it by proving its logical negation first.target_neg.",
    "challenge": "theorem first.target : True := by sorry\ntheorem first.target_neg : Not True := by sorry\n",
    "image": "zeyuzhenghub/lean4:v4.34.0",
}

OUTPUTS = [
    make_output("Prove", [{"command": "sed -i 's/True := by sorry/True := by trivial/' first.lean"}], cost=0),
    make_output("Patch", [{"command": "git add first.lean && git diff --cached > patch.txt"}], cost=0),
    make_output("Submit", [{"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"}], cost=0),
]


@pytest.fixture
def dataset(tmp_path):
    path = tmp_path / "test.jsonl"
    path.write_text(json.dumps(INSTANCE) + "\n")
    return path


@pytest.mark.slow
@pytest.mark.parametrize("workers", [1, 2])
def test_reuf2f_end_to_end(dataset, tmp_path, workers, container_executable):
    """Test the complete ReuF2F flow on one instance with a deterministic model"""
    with patch("leanimum.run.benchmarks.reuf2f.get_model") as mock_get_model:
        # Use side_effect to create a new model instance for each worker
        mock_get_model.side_effect = lambda **kwargs: DeterministicModel(outputs=OUTPUTS, cost_per_call=0)

        main(
            subset=str(dataset),
            slice_spec="0:1",
            output=str(tmp_path),
            workers=workers,
            filter_spec="first",
            config_spec=[CONFIG],
            environment_class="docker",
        )

    instance_id = "first"
    with open(tmp_path / "preds.json") as f:
        actual_result = json.load(f)

    assert actual_result[instance_id]["model_name_or_path"] == "deterministic"
    assert "+theorem first.target : True := by trivial" in actual_result[instance_id]["model_patch"]

    traj_output_file = tmp_path / instance_id / f"{instance_id}.traj.json"
    trajectory = json.loads(traj_output_file.read_text())
    assert trajectory["info"]["exit_status"] == "Submitted"
    assert INSTANCE["problem_statement"] in trajectory["messages"][1]["content"]


@pytest.mark.slow
def test_prepare_environment_commits_the_challenge(container_executable):
    """The shared image's project roots the task and commits it, as a per-instance image would."""
    env = DockerEnvironment(image=INSTANCE["image"], cwd="/testbed", executable=container_executable, timeout=1200)
    prepare_environment(env, INSTANCE)
    assert env.execute({"command": "cat first.lean"})["output"] == INSTANCE["challenge"]
    assert 'roots = ["first"]' in env.execute({"command": "cat lakefile.toml"})["output"]
    assert env.execute({"command": "git status --porcelain"})["output"] == ""
    assert env.execute({"command": "git rev-list --count HEAD"})["output"].strip() == "1"


def test_get_reuf2f_environment_does_not_mutate_shared_config():
    """The config dict is shared across worker threads, so resolving the per-instance image must not mutate it."""
    config = {"environment": {"environment_class": "docker"}}
    with (
        patch("leanimum.run.benchmarks.reuf2f.get_environment", return_value=MagicMock()) as mock_get_environment,
        patch("leanimum.run.benchmarks.reuf2f.prepare_environment"),
    ):
        get_reuf2f_environment(config, INSTANCE)

    assert mock_get_environment.call_args.args[0]["image"] == INSTANCE["image"]
    assert "image" not in config["environment"]


def test_get_reuf2f_environment_runs_startup_command_as_dict():
    """startup_command must be passed to env.execute() as a dict, not a bare string."""
    fake_env = MagicMock()
    fake_env.execute.return_value = {"returncode": 0, "output": ""}
    config = {"run": {"env_startup_command": "echo {{instance_id}}"}}

    with (
        patch("leanimum.run.benchmarks.reuf2f.get_environment", return_value=fake_env),
        patch("leanimum.run.benchmarks.reuf2f.prepare_environment"),
    ):
        get_reuf2f_environment(config, INSTANCE)

    fake_env.execute.assert_called_once_with({"command": "echo first"})


def test_filter_instances_no_filters():
    """Test filter_instances with no filtering applied"""
    instances = [{"instance_id": "repo1__test1"}, {"instance_id": "repo2__test2"}, {"instance_id": "repo3__test3"}]
    result = filter_instances(instances, filter_spec="", slice_spec="")
    assert result == instances


def test_filter_instances_regex_filter():
    """Test filter_instances with regex filtering"""
    instances = [
        {"instance_id": "django__test1"},
        {"instance_id": "flask__test2"},
        {"instance_id": "django__test3"},
        {"instance_id": "requests__test4"},
    ]
    result = filter_instances(instances, filter_spec=r"django__.*", slice_spec="")
    expected = [{"instance_id": "django__test1"}, {"instance_id": "django__test3"}]
    assert result == expected


def test_filter_instances_slice_only():
    """Test filter_instances with slice specification"""
    instances = [{"instance_id": f"repo{i}__test{i}"} for i in range(10)]
    result = filter_instances(instances, filter_spec="", slice_spec="2:5")
    expected = [{"instance_id": "repo2__test2"}, {"instance_id": "repo3__test3"}, {"instance_id": "repo4__test4"}]
    assert result == expected


def test_filter_instances_slice_start_only():
    """Test filter_instances with slice start only"""
    instances = [{"instance_id": f"repo{i}__test{i}"} for i in range(5)]
    result = filter_instances(instances, filter_spec="", slice_spec="3:")
    expected = [{"instance_id": "repo3__test3"}, {"instance_id": "repo4__test4"}]
    assert result == expected


def test_filter_instances_slice_end_only():
    """Test filter_instances with slice end only"""
    instances = [{"instance_id": f"repo{i}__test{i}"} for i in range(5)]
    result = filter_instances(instances, filter_spec="", slice_spec=":2")
    expected = [{"instance_id": "repo0__test0"}, {"instance_id": "repo1__test1"}]
    assert result == expected


def test_filter_instances_filter_and_slice():
    """Test filter_instances with both filtering and slicing"""
    instances = [
        {"instance_id": "django__test1"},
        {"instance_id": "flask__test2"},
        {"instance_id": "django__test3"},
        {"instance_id": "django__test4"},
        {"instance_id": "requests__test5"},
    ]
    result = filter_instances(instances, filter_spec=r"django__.*", slice_spec="1:3")
    expected = [{"instance_id": "django__test3"}, {"instance_id": "django__test4"}]
    assert result == expected


def test_filter_instances_shuffle():
    """Test filter_instances with shuffle enabled produces deterministic results"""
    instances = [{"instance_id": f"repo{i:02d}__test{i}"} for i in range(10)]
    # Test that shuffle produces same result with same seed
    result1 = filter_instances(instances.copy(), filter_spec="", slice_spec="", shuffle=True)
    result2 = filter_instances(instances.copy(), filter_spec="", slice_spec="", shuffle=True)
    assert result1 == result2
    # Test that shuffled result is different from original order
    result_no_shuffle = filter_instances(instances.copy(), filter_spec="", slice_spec="", shuffle=False)
    assert result1 != result_no_shuffle


def test_filter_instances_empty_list():
    """Test filter_instances with empty input list"""
    result = filter_instances([], filter_spec=r".*", slice_spec="0:5", shuffle=True)
    assert result == []


def test_filter_instances_no_matches():
    """Test filter_instances when regex matches nothing"""
    instances = [{"instance_id": "django__test1"}, {"instance_id": "flask__test2"}]
    result = filter_instances(instances, filter_spec=r"nonexistent__.*", slice_spec="")
    assert result == []


def test_update_preds_file_new_file(tmp_path):
    """Test update_preds_file when output file doesn't exist"""
    output_path = tmp_path / "preds.json"
    update_preds_file(output_path, "test__instance__1", "test_model", "test_result")

    assert output_path.exists()
    result = json.loads(output_path.read_text())
    expected = {
        "test__instance__1": {
            "model_name_or_path": "test_model",
            "instance_id": "test__instance__1",
            "model_patch": "test_result",
        }
    }
    assert result == expected


def test_update_preds_file_existing_file(tmp_path):
    """Test update_preds_file when output file already exists"""
    output_path = tmp_path / "preds.json"

    # Create initial file with one instance
    initial_data = {
        "existing__instance": {
            "model_name_or_path": "old_model",
            "instance_id": "existing__instance",
            "model_patch": "old_result",
        }
    }
    output_path.write_text(json.dumps(initial_data))

    # Add new instance
    update_preds_file(output_path, "new__instance", "new_model", "new_result")

    result = json.loads(output_path.read_text())
    expected = {
        "existing__instance": {
            "model_name_or_path": "old_model",
            "instance_id": "existing__instance",
            "model_patch": "old_result",
        },
        "new__instance": {
            "model_name_or_path": "new_model",
            "instance_id": "new__instance",
            "model_patch": "new_result",
        },
    }
    assert result == expected


def test_update_preds_file_overwrite_existing(tmp_path):
    """Test update_preds_file overwrites existing instance"""
    output_path = tmp_path / "preds.json"

    # Create initial file
    initial_data = {
        "test__instance": {
            "model_name_or_path": "old_model",
            "instance_id": "test__instance",
            "model_patch": "old_result",
        }
    }
    output_path.write_text(json.dumps(initial_data))

    # Update existing instance
    update_preds_file(output_path, "test__instance", "new_model", "new_result")

    result = json.loads(output_path.read_text())
    expected = {
        "test__instance": {
            "model_name_or_path": "new_model",
            "instance_id": "test__instance",
            "model_patch": "new_result",
        }
    }
    assert result == expected


def test_remove_from_preds_file_existing(tmp_path):
    """Test remove_from_preds_file removes existing instance"""
    output_path = tmp_path / "preds.json"

    # Create file with multiple instances
    initial_data = {
        "instance1": {"model_name_or_path": "model1", "instance_id": "instance1", "model_patch": "result1"},
        "instance2": {"model_name_or_path": "model2", "instance_id": "instance2", "model_patch": "result2"},
    }
    output_path.write_text(json.dumps(initial_data))

    # Remove one instance
    remove_from_preds_file(output_path, "instance1")

    result = json.loads(output_path.read_text())
    expected = {"instance2": {"model_name_or_path": "model2", "instance_id": "instance2", "model_patch": "result2"}}
    assert result == expected


def test_remove_from_preds_file_nonexistent_instance(tmp_path):
    """Test remove_from_preds_file with nonexistent instance"""
    output_path = tmp_path / "preds.json"

    initial_data = {"instance1": {"model_name_or_path": "model1", "instance_id": "instance1", "model_patch": "result1"}}
    output_path.write_text(json.dumps(initial_data))

    # Try to remove nonexistent instance
    remove_from_preds_file(output_path, "nonexistent")

    # File should be unchanged
    result = json.loads(output_path.read_text())
    assert result == initial_data


def test_remove_from_preds_file_no_file(tmp_path):
    """Test remove_from_preds_file when file doesn't exist"""
    output_path = tmp_path / "preds.json"

    # Should not raise an error
    remove_from_preds_file(output_path, "any_instance")

    # File should still not exist
    assert not output_path.exists()


@pytest.mark.slow
def test_redo_existing_false_skips_existing(dataset, tmp_path):
    """Test that redo_existing=False skips instances that already have results"""
    # Create existing preds.json with one instance
    preds_file = tmp_path / "preds.json"
    existing_data = {
        "first": {
            "model_name_or_path": "previous_model",
            "instance_id": "first",
            "model_patch": "previous_result",
        }
    }
    preds_file.write_text(json.dumps(existing_data))

    with patch("leanimum.run.benchmarks.reuf2f.get_model") as mock_get_model:
        mock_get_model.side_effect = lambda **kwargs: DeterministicModel(outputs=[], cost_per_call=0)

        main(
            subset=str(dataset),
            slice_spec="0:1",
            output=str(tmp_path),
            workers=1,
            filter_spec="first",
            redo_existing=False,
            config_spec=[CONFIG],
        )

    # Should still have the original result
    result = json.loads(preds_file.read_text())
    assert result == existing_data


@pytest.mark.slow
def test_redo_existing_true_overwrites_existing(dataset, tmp_path, container_executable):
    """Test that redo_existing=True processes instances even if they already have results"""
    # Create existing preds.json with one instance
    preds_file = tmp_path / "preds.json"
    existing_data = {
        "first": {
            "model_name_or_path": "previous_model",
            "instance_id": "first",
            "model_patch": "previous_result",
        }
    }
    preds_file.write_text(json.dumps(existing_data))

    with patch("leanimum.run.benchmarks.reuf2f.get_model") as mock_get_model:
        mock_get_model.side_effect = lambda **kwargs: DeterministicModel(outputs=OUTPUTS, cost_per_call=0.1)

        main(
            subset=str(dataset),
            slice_spec="0:1",
            output=str(tmp_path),
            workers=1,
            filter_spec="first",
            redo_existing=True,
            config_spec=[CONFIG],
            environment_class="docker",
        )

    # Should have new result from deterministic model
    result = json.loads(preds_file.read_text())
    assert "+theorem first.target : True := by trivial" in result["first"]["model_patch"]
    assert result["first"]["model_name_or_path"] == "deterministic"


class ExceptionModelConfig(BaseModel):
    model_name: str = "exception_model"


class ExceptionModel:
    """Test model that raises exceptions during processing."""

    def __init__(self, exception_type: type[Exception] = RuntimeError, exception_message: str = "Test exception"):
        self.exception_type = exception_type
        self.exception_message = exception_message
        self.cost = 0.0
        self.n_calls = 0
        self.config = ExceptionModelConfig()

    def query(self, *args, **kwargs):
        self.n_calls += 1
        raise self.exception_type(self.exception_message)

    def format_message(self, **kwargs) -> dict:
        return dict(**kwargs)

    def format_observation_messages(
        self, message: dict, outputs: list[dict], template_vars: dict | None = None
    ) -> list[dict]:
        return [self.format_message(role="user", content=str(o)) for o in outputs]

    def get_template_vars(self, **kwargs) -> dict:
        return self.config.model_dump() | {"n_model_calls": self.n_calls, "model_cost": self.cost}

    def serialize(self) -> dict:
        return {
            "info": {
                "model_stats": {
                    "instance_cost": self.cost,
                    "api_calls": self.n_calls,
                },
                "config": {
                    "model": self.config.model_dump(mode="json"),
                    "model_type": f"{self.__class__.__module__}.{self.__class__.__name__}",
                },
            }
        }


@pytest.mark.slow
@pytest.mark.parametrize("workers", [1, 2])
def test_exception_handling_in_agent_run(dataset, tmp_path, workers, container_executable):
    """Test that exceptions during agent.run() are properly handled and recorded"""
    with patch("leanimum.run.benchmarks.reuf2f.get_model") as mock_get_model:
        mock_get_model.return_value = ExceptionModel(RuntimeError, "Agent processing failed")

        with patch("leanimum.run.benchmarks.reuf2f.RunBatchProgressManager") as mock_progress_class:
            mock_progress_manager = mock_progress_class.return_value
            mock_progress_manager.render_group = None  # For Live context manager

            main(
                subset=str(dataset),
                slice_spec="0:1",
                output=str(tmp_path),
                workers=workers,
                filter_spec="first",
                config_spec=[CONFIG],
                environment_class="docker",
            )

    # Check that prediction file contains exception information
    preds_file = tmp_path / "preds.json"
    assert preds_file.exists()

    result = json.loads(preds_file.read_text())
    instance_id = "first"
    assert instance_id in result
    assert result[instance_id]["model_patch"] == ""
    assert result[instance_id]["model_name_or_path"] == "exception_model"

    # Check that trajectory file contains exception information
    traj_file = tmp_path / instance_id / f"{instance_id}.traj.json"
    assert traj_file.exists()

    traj_data = json.loads(traj_file.read_text())
    assert traj_data["instance_id"] == instance_id
    assert traj_data["info"]["exit_status"] == "RuntimeError"
    assert traj_data["info"]["submission"] == ""
    assert traj_data["info"]["exception_str"] == "Agent processing failed"


@pytest.mark.slow
def test_exception_handling_with_progress_manager(dataset, tmp_path, container_executable):
    """Test that progress manager receives exception notifications in multithreaded mode"""
    with patch("leanimum.run.benchmarks.reuf2f.get_model") as mock_get_model:
        mock_get_model.return_value = ExceptionModel(ConnectionError, "Network timeout")

        with patch("leanimum.run.benchmarks.reuf2f.RunBatchProgressManager") as mock_progress_class:
            mock_progress_manager = mock_progress_class.return_value
            mock_progress_manager.render_group = None  # For Live context manager

            main(
                subset=str(dataset),
                slice_spec="0:1",
                output=str(tmp_path),
                workers=2,
                filter_spec="first",
                config_spec=[CONFIG],
                environment_class="docker",
            )

            # Verify progress manager methods were called
            mock_progress_manager.on_instance_start.assert_called_once_with("first")
            mock_progress_manager.on_instance_end.assert_called_once_with("first", "ConnectionError")

            # on_uncaught_exception should not be called since exceptions are handled properly
            mock_progress_manager.on_uncaught_exception.assert_not_called()
