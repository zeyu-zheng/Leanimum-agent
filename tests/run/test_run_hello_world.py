from unittest.mock import patch

from leanimum.run.hello_world import main
from tests.conftest import assert_observations_match


def test_run_hello_world_end_to_end(local_test_data, local_model, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("leanimum.run.hello_world.LitellmTextbasedModel", return_value=local_model) as model_class:
        agent = main(task="Run the local fixture", model_name="tardis")

    model_class.assert_called_once_with(model_name="tardis")
    assert len(agent.messages) == 2 + 2 * len(local_test_data["model_responses"])
    assert_observations_match(local_test_data["expected_observations"], agent.messages)
    assert agent.n_calls == len(local_test_data["model_responses"])
    assert agent.messages[-1]["extra"]["exit_status"] == "Submitted"
