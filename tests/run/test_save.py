"""Trajectory serialization and JSON persistence."""

import json

import pytest

from leanimum import __version__
from leanimum.agents.default import DefaultAgent
from leanimum.config import get_config_from_spec
from leanimum.environments.local import LocalEnvironment
from leanimum.models.test_models import DeterministicModel


@pytest.fixture
def agent(tmp_path):
    agent = DefaultAgent(
        DeterministicModel(outputs=[]),
        LocalEnvironment(cwd=str(tmp_path)),
        **get_config_from_spec("default")["agent"],
    )
    agent.add_messages(
        {"role": "system", "content": "test system message"},
        {"role": "user", "content": "test user message"},
    )
    return agent


def test_agent_serialize(agent):
    agent.cost, agent.n_calls = 0.25, 2
    data = agent.serialize()
    assert data == {
        "info": {
            "model_stats": {"instance_cost": 0.25, "api_calls": 2},
            "config": {
                "agent": agent.config.model_dump(mode="json"),
                "agent_type": "leanimum.agents.default.DefaultAgent",
                "model": agent.model.config.model_dump(mode="json"),
                "model_type": "leanimum.models.test_models.DeterministicModel",
                "environment": agent.env.config.model_dump(mode="json"),
                "environment_type": "leanimum.environments.local.LocalEnvironment",
            },
            "mini_version": __version__,
            "exit_status": "",
            "submission": "",
        },
        "messages": agent.messages,
        "trajectory_format": "leanimum-agent-1.1",
    }
    assert json.loads(json.dumps(data)) == data


def test_agent_save_round_trips_and_merges_metadata(agent, tmp_path):
    path = tmp_path / "nested/run.traj.json"
    extra = {"info": {"exit_status": "Submitted", "submission": "test result"}}
    saved = agent.save(path, extra, {"instance_id": "one"})
    assert json.loads(path.read_text()) == saved
    assert saved == agent.serialize(extra, {"instance_id": "one"})
    assert saved["info"]["exit_status"] == "Submitted"
    assert saved["info"]["submission"] == "test result"
    assert saved["info"]["config"]["agent_type"] == "leanimum.agents.default.DefaultAgent"
    assert saved["messages"] == agent.messages
    assert saved["instance_id"] == "one"
    assert agent.serialize()["info"]["exit_status"] == ""
