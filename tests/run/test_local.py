from unittest.mock import patch

from leanimum.run.mini import DEFAULT_CONFIG_FILE, main
from tests.conftest import assert_observations_match


def test_local_end_to_end(local_test_data, local_model, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LEANA_CONFIGURED", "true")
    with patch("leanimum.models.litellm_model.LitellmModel", return_value=local_model):
        agent = main(
            model_name="tardis",
            config_spec=[str(DEFAULT_CONFIG_FILE)],
            yolo=True,
            task="Run the local fixture",
            output=None,
            cost_limit=10,
            model_class=None,
            agent_class=None,
            environment_class=None,
            exit_immediately=True,
        )

    assert len(agent.messages) == 2 + 2 * len(local_test_data["model_responses"])
    assert_observations_match(local_test_data["expected_observations"], agent.messages)
    assert agent.n_calls == len(local_test_data["model_responses"])
    assert agent.messages[-1]["extra"]["exit_status"] == "Submitted"
