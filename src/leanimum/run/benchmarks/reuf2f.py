#!/usr/bin/env python3

"""Run Leanimum-agent on ReuF2F instances using the upstream SWE-bench batch flow."""

# Adapted from mini-SWE-agent 04d809ceab9df28f9adaed044884180159172930,
# src/minisweagent/run/benchmarks/swebench.py (MIT; repository LICENSE).

import concurrent.futures
import json
import random
import re
import threading
import time
import traceback
from pathlib import Path

import typer
from jinja2 import StrictUndefined, Template
from rich.live import Live

from leanimum.config import builtin_config_dir, get_config_from_spec
from leanimum.environments import get_environment
from leanimum.environments.docker import DockerEnvironment
from leanimum.environments.local import LocalEnvironment
from leanimum.models import get_model
from leanimum.run.benchmarks.utils.batch_progress import RunBatchProgressManager
from leanimum.run.benchmarks.utils.common import ProgressTrackingAgent
from leanimum.run.benchmarks.utils.reuf2f import load_instances, prepare_environment
from leanimum.utils.log import add_file_handler, logger
from leanimum.utils.serialize import UNSET, recursive_merge

_HELP_TEXT = """Run Leanimum-agent on ReuF2F instances with Docker or explicit local execution.

Supply a prepared task release with --subset. Docker uses the shared Lean image;
local uses a prepared Lean project at environment.cwd and provides no isolation.
Candidate generation and independent Comparator grading are separate.
"""

_CONFIG_SPEC_HELP_TEXT = """Path to config files, filenames, or key-value pairs.

[bold red]IMPORTANT:[/bold red] If you set this option, include [bold green]-c reuf2f.yaml[/bold green].
Multiple configs will be recursively merged, for example:
[bold green]-c reuf2f.yaml -c agent.step_limit=100[/bold green]
"""

DEFAULT_CONFIG_FILE = builtin_config_dir / "benchmarks" / "reuf2f.yaml"
app = typer.Typer(rich_markup_mode="rich", add_completion=False)
_OUTPUT_FILE_LOCK = threading.Lock()


def get_reuf2f_environment(config: dict) -> DockerEnvironment | LocalEnvironment:
    env_config = {**config.get("environment", {})}
    env_config["environment_class"] = env_config.get("environment_class", "docker")
    if env_config["environment_class"] not in ("docker", "local"):
        raise ValueError("ReuF2F tasks support only docker and local")
    if env_config["environment_class"] == "local":
        logger.warning("Local execution has no task isolation; use a disposable no-secret environment")
    return get_environment(env_config)


def update_preds_file(output_path: Path, instance_id: str, model_name: str, result: str):
    """Update the output JSON file with results from a single instance."""
    with _OUTPUT_FILE_LOCK:
        output_data = {}
        if output_path.exists():
            output_data = json.loads(output_path.read_text())
        output_data[instance_id] = {
            "model_name_or_path": model_name,
            "instance_id": instance_id,
            "model_patch": result,
        }
        output_path.write_text(json.dumps(output_data, indent=2))


def remove_from_preds_file(output_path: Path, instance_id: str):
    """Remove an instance from the predictions file."""
    if not output_path.exists():
        return
    with _OUTPUT_FILE_LOCK:
        output_data = json.loads(output_path.read_text())
        if instance_id in output_data:
            del output_data[instance_id]
            output_path.write_text(json.dumps(output_data, indent=2))


def process_instance(
    instance: dict,
    output_dir: Path,
    config: dict,
    progress_manager: RunBatchProgressManager,
) -> None:
    """Upstream run/save flow with shared-image preparation and explicit cleanup."""
    instance_id = instance["instance_id"]
    instance_dir = output_dir / instance_id
    instance_dir.mkdir(parents=True, exist_ok=True)
    remove_from_preds_file(output_dir / "preds.json", instance_id)
    (instance_dir / f"{instance_id}.traj.json").unlink(missing_ok=True)
    model = get_model(config=config.get("model", {}))
    task = instance["problem_statement"]

    progress_manager.on_instance_start(instance_id)
    progress_manager.update_instance_status(instance_id, "Pulling/starting environment")

    env = None
    agent = None
    exit_status = None
    result = None
    extra_info = {}

    try:
        env = get_reuf2f_environment(config)
        if startup_command := config.get("run", {}).get("env_startup_command"):
            startup_command = Template(startup_command, undefined=StrictUndefined).render(**instance)
            out = env.execute({"command": startup_command})
            if out["returncode"] != 0:
                raise RuntimeError(f"Error executing startup command: {out}")
        prepare_environment(env, instance, instance_dir)
        agent = ProgressTrackingAgent(
            model,
            env,
            progress_manager=progress_manager,
            instance_id=instance_id,
            **config.get("agent", {}),
        )
        info = agent.run(task)
        exit_status = info.get("exit_status")
        result = info.get("submission")
    except Exception as e:
        logger.error(f"Error processing instance {instance_id}: {e}", exc_info=True)
        exit_status, result = type(e).__name__, ""
        extra_info = {"traceback": traceback.format_exc(), "exception_str": str(e)}
    finally:
        try:
            if agent is not None:
                traj_path = instance_dir / f"{instance_id}.traj.json"
                agent.save(
                    traj_path,
                    {
                        "info": {
                            "exit_status": exit_status,
                            "submission": result,
                            **extra_info,
                        },
                        "instance_id": instance_id,
                        "source_revision": instance["source_revision"],
                        "base_commit": instance["base_commit"],
                    },
                )
                logger.info(f"Saved trajectory to '{traj_path}'")
            update_preds_file(output_dir / "preds.json", instance_id, model.config.model_name, result)
            progress_manager.on_instance_end(instance_id, exit_status)
        finally:
            if isinstance(env, DockerEnvironment):
                env.cleanup()
                env.container_id = None


def filter_instances(
    instances: list[dict],
    *,
    filter_spec: str,
    slice_spec: str = "",
    shuffle: bool = False,
) -> list[dict]:
    """Filter and slice a list of SWEBench instances."""
    if shuffle:
        instances = sorted(instances.copy(), key=lambda x: x["instance_id"])
        random.seed(42)
        random.shuffle(instances)
    before_filter = len(instances)
    instances = [instance for instance in instances if re.match(filter_spec, instance["instance_id"])]
    if (after_filter := len(instances)) != before_filter:
        logger.info(f"Instance filter: {before_filter} -> {after_filter} instances")
    if slice_spec:
        values = [int(x) if x else None for x in slice_spec.split(":")]
        instances = instances[slice(*values)]
        if (after_slice := len(instances)) != before_filter:
            logger.info(f"Instance slice: {before_filter} -> {after_slice} instances")
    return instances


# fmt: off
@app.command(help=_HELP_TEXT)
def main(
    subset: str = typer.Option(..., "--subset", help="Path to a prepared ReuF2F task release", rich_help_panel="Data selection"),
    slice_spec: str = typer.Option("", "--slice", help="Slice specification (e.g., '0:5')", rich_help_panel="Data selection"),
    filter_spec: str = typer.Option("", "--filter", help="Filter instance IDs by regex", rich_help_panel="Data selection"),
    shuffle: bool = typer.Option(False, "--shuffle", help="Shuffle instances", rich_help_panel="Data selection"),
    output: str = typer.Option("", "-o", "--output", help="Output directory", rich_help_panel="Basic"),
    workers: int = typer.Option(1, "-w", "--workers", min=1, help="Number of worker threads for parallel processing", rich_help_panel="Basic"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "--model-class", help="Model class to use", rich_help_panel="Advanced"),
    redo_existing: bool = typer.Option(False, "--redo-existing", help="Redo recorded instances", rich_help_panel="Data selection"),
    config_spec: list[str] = typer.Option([str(DEFAULT_CONFIG_FILE)], "-c", "--config", help=_CONFIG_SPEC_HELP_TEXT, rich_help_panel="Basic"),
    environment_class: str | None = typer.Option(None, "--environment-class", help="Execution backend: docker (default) or local", rich_help_panel="Advanced"),
) -> None:
    # fmt: on
    tasks = Path(subset).expanduser().resolve()
    instances = load_instances(tasks)
    instances = filter_instances(instances, filter_spec=filter_spec, slice_spec=slice_spec, shuffle=shuffle)
    output_path = Path(output).expanduser().resolve()
    if output_path.is_relative_to(tasks) or tasks.is_relative_to(output_path):
        raise typer.BadParameter("Keep output separate from the prepared task release")
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results will be saved to {output_path}")
    add_file_handler(output_path / "leanimum.log")
    if not redo_existing and (output_path / "preds.json").exists():
        existing_instances = list(json.loads((output_path / "preds.json").read_text()).keys())
        logger.info(f"Skipping {len(existing_instances)} existing instances")
        instances = [instance for instance in instances if instance["instance_id"] not in existing_instances]
    logger.info(f"Running on {len(instances)} instances...")

    logger.info(f"Building agent config from specs: {config_spec}")
    configs = [get_config_from_spec(spec) for spec in config_spec]
    configs.append({
        "environment": {"environment_class": environment_class or UNSET},
        "model": {"model_name": model or UNSET, "model_class": model_class or UNSET},
    })
    config = recursive_merge(*configs)
    progress_manager = RunBatchProgressManager(len(instances), output_path / f"exit_statuses_{time.time()}.yaml")

    def process_futures(futures: dict[concurrent.futures.Future, str]):
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except concurrent.futures.CancelledError:
                pass
            except Exception as e:
                instance_id = futures[future]
                logger.error(f"Error in future for instance {instance_id}: {e}", exc_info=True)
                progress_manager.on_uncaught_exception(instance_id, e)

    with Live(progress_manager.render_group, refresh_per_second=4):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_instance, instance, output_path, config, progress_manager): instance["instance_id"]
                for instance in instances
            }
            try:
                process_futures(futures)
            except KeyboardInterrupt:
                logger.info("Cancelling all pending jobs. Press ^C again to exit immediately.")
                for future in futures:
                    if not future.running() and not future.done():
                        future.cancel()
                process_futures(futures)


if __name__ == "__main__":
    app()
