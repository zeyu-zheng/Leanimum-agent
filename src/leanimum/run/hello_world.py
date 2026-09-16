"""This is the simplest possible example of how to use Leanimum-agent with python bindings.
For a more complete example, see mini.py
"""

import logging
import os
from pathlib import Path

import typer
import yaml

from leanimum import package_dir
from leanimum.agents.default import DefaultAgent
from leanimum.environments.local import LocalEnvironment
from leanimum.models.litellm_textbased_model import LitellmTextbasedModel

app = typer.Typer()


@app.command()
def main(
    task: str = typer.Option(..., "-t", "--task", help="Task/problem statement", show_default=False, prompt=True),
    model_name: str = typer.Option(
        os.getenv("LEANA_MODEL_NAME"),
        "-m",
        "--model",
        help="Model name (defaults to LEANA_MODEL_NAME env var)",
        prompt="What model do you want to use?",
    ),
) -> DefaultAgent:
    logging.basicConfig(level=logging.DEBUG)
    agent = DefaultAgent(
        LitellmTextbasedModel(model_name=model_name),
        LocalEnvironment(timeout=600),
        **yaml.safe_load(Path(package_dir / "config" / "default.yaml").read_text())["agent"],
    )
    agent.run(task)
    return agent


if __name__ == "__main__":
    app()
