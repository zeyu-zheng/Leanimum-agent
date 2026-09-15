import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
from jinja2 import StrictUndefined, Template
from leanimum.agents.default import AgentConfig
from leanimum.config import builtin_config_dir, get_config_from_spec
from leanimum.models.utils.actions_text import parse_regex_actions


@dataclass
class MockOutput:
    """Mock output object for testing the template"""

    returncode: int
    output: str
    exception_info: str = ""


def test_observation_template_short_output():
    """Test that short output (< 10000 chars) is displayed in full"""
    # Load the text-based Lean config
    config_path = Path(__file__).parent.parent.parent / "src" / "leanimum" / "config" / "mini_textbased.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Create mock output with short content
    output = MockOutput(returncode=0, output="Success! Operation completed.\nWarning: minor issue")

    # Render the template
    result = template.render(output=output)

    # Verify the result contains all parts and no truncation
    assert "<returncode>" in result
    assert "0" in result
    assert "<output>" in result
    assert "Success! Operation completed." in result
    assert "Warning: minor issue" in result

    # Should not contain truncation elements for short output
    assert "<output_head>" not in result
    assert "<elided_chars>" not in result
    assert "<output_tail>" not in result
    assert "<warning>" not in result


def test_observation_template_long_output():
    """Test that long output (> 10000 chars) is truncated with head/tail format"""
    # Load the text-based Lean config
    config_path = Path(__file__).parent.parent.parent / "src" / "leanimum" / "config" / "mini_textbased.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Create mock output with long content
    long_output = "A" * 8000 + "B" * 3000  # 11000 characters total
    # Total will be > 10000 chars

    output = MockOutput(returncode=1, output=long_output)

    # Render the template
    result = template.render(output=output)

    # Should contain truncation elements for long output
    assert "<warning>" in result
    assert "The output of your last command was too long" in result
    assert "<output_head>" in result
    assert "<elided_chars>" in result
    assert "characters elided" in result
    assert "<output_tail>" in result

    # Should still contain the basic structure
    assert "<returncode>" in result
    assert "1" in result

    # Verify the head contains first part of output
    head_start = result.find("<output_head>")
    head_end = result.find("</output_head>")
    head_content = result[head_start:head_end]
    assert "AAAA" in head_content  # Should contain start of output

    # Verify the tail contains last part of output
    tail_start = result.find("<output_tail>")
    tail_end = result.find("</output_tail>")
    tail_content = result[tail_start:tail_end]
    assert "BBBB" in tail_content  # Should contain end of output


def test_observation_template_edge_case_exactly_10000_chars():
    """Test the boundary case where output is around 10000 characters"""
    # Load the text-based Lean config
    config_path = Path(__file__).parent.parent.parent / "src" / "leanimum" / "config" / "mini_textbased.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Use a large amount of data that will definitely exceed 10000 chars when rendered
    output = MockOutput(returncode=0, output="X" * 10000)

    # Render the template
    result = template.render(output=output)

    # Should use truncated format for large output
    assert "<output_head>" in result
    assert "<elided_chars>" in result
    assert "<output_tail>" in result
    assert "<warning>" in result
    # The X's should still be present in head or tail
    assert "XXXX" in result


def test_observation_template_just_under_10000_chars():
    """Test that smaller output shows full output without truncation"""
    # Load the text-based Lean config
    config_path = Path(__file__).parent.parent.parent / "src" / "leanimum" / "config" / "mini_textbased.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Use a reasonably sized output that should be well under 10000 chars when rendered
    output = MockOutput(returncode=0, output="Y" * 8000)

    # Render the template
    result = template.render(output=output)

    # Should show full output without truncation
    assert "<output_head>" not in result
    assert "<elided_chars>" not in result
    assert "<output_tail>" not in result
    assert "<warning>" not in result
    assert "Y" * 8000 in result


def test_agent_config_requires_templates():
    """Test that AgentConfig now requires all template fields (no defaults in code)"""
    import pytest
    from pydantic import ValidationError

    # AgentConfig should require all template fields now (Pydantic raises ValidationError)
    with pytest.raises(ValidationError, match="validation error"):
        AgentConfig()


@pytest.mark.parametrize(
    ("name", "text_based"),
    [("mini", False), ("mini_textbased", True), ("default", True), ("reuf2f", False)],
)
def test_all_prompts_are_lean_and_match_action_protocol(name, text_based):
    config = get_config_from_spec(name)
    prompt = Template(config["agent"]["instance_template"], undefined=StrictUndefined).render(
        task="Prove Nat.add_zero without sorry",
        system="Linux",
        release="test",
        version="test",
        machine="x86_64",
    )
    assert "Lean" in config["agent"]["system_template"] + prompt
    for text in (
        "Nat.add_zero",
        "Mathlib",
        "Comparator",
        "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
    ):
        assert text in prompt
    for text in ("Please solve this issue", "reproduce the issue", "newfile.py", "SWE-bench", "ProgramBench"):
        assert text not in prompt
    assert config["environment"]["timeout"] == (1200 if name == "reuf2f" else 600)
    if text_based:
        assert config["model"]["model_class"] == "litellm_textbased"
        assert "exactly ONE bash code block" in config["agent"]["system_template"]
        assert parse_regex_actions(
            "```mswea_bash_command\nlake env lean Target.lean\n```",
            action_regex=r"```mswea_bash_command\s*\n(.*?)\n```",
            format_error_template=config["model"]["format_error_template"],
        ) == [{"command": "lake env lean Target.lean"}]
    else:
        assert "bash tool call" in prompt


def test_only_reuf2f_benchmark_config_is_shipped():
    assert sorted(p.name for p in (builtin_config_dir / "benchmarks").glob("*.yaml")) == ["reuf2f.yaml"]
    prompt = get_config_from_spec("reuf2f")["agent"]["instance_template"]
    assert "original theorem" in prompt and "_neg" in prompt
    assert "ReuF2FEval" not in prompt and "Main.lean" not in prompt
    assert "The unchosen theorem may remain `sorry`" in prompt
    assert "DO NOT MODIFY: Target statements" in prompt
    assert "TASK.md" not in prompt and "#reuf2f_solution" not in prompt
    assert "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt" in prompt
    assert "git diff -- path/to/file1 path/to/file2 > patch.txt" in prompt
    assert "Do NOT commit your changes." in prompt and "git add -N" in prompt
    assert "base_commit" not in prompt
    assert "[[lean_lib]]" in prompt and "import the needed modules in the task file" in prompt
    assert "library layout in `lakefile.toml`" in prompt
    assert "Helpers/" not in prompt


def test_reuf2f_library_guidance_is_environment_detail_not_workflow():
    prompt = get_config_from_spec("reuf2f")["agent"]["instance_template"]
    boundaries = prompt.split("## Important Boundaries\n", 1)[1].split("## Recommended Workflow", 1)[0]
    workflow = prompt.split("## Recommended Workflow\n", 1)[1].split("## Command Execution Rules", 1)[0]
    environment = prompt.split("## Environment Details\n", 1)[1].split("## Submission", 1)[0]
    submission = prompt.split("## Submission\n", 1)[1]
    assert "the Project root" in boundaries and "do not introduce `lakefile.lean`" in boundaries
    assert "4. Check your changes with `lake build`" in workflow
    assert "Aux" not in workflow and "[[lean_lib]]" not in workflow
    assert "Register new helper libraries with `[[lean_lib]]` entries in `lakefile.toml`" in environment
    assert "import the needed modules in the task file" in environment
    assert "rg 'PATTERN' .lake/packages/mathlib/Mathlib" in environment
    assert "--hidden" not in environment and "--no-ignore" not in environment
    assert "Aux/Lemmas.lean" not in environment
    assert "Step 1: Create the patch file" in submission
    assert "modified Lean sources and lakefile.toml" in submission
    assert "Do NOT commit your changes." in submission
    assert "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt" in submission


@pytest.mark.parametrize(
    ("name", "baseline_name"),
    [("mini", "mini"), ("mini_textbased", "mini_textbased"), ("default", "default"), ("reuf2f", "swebench")],
)
def test_prompts_preserve_upstream_shape_and_shared_blocks(name, baseline_name):
    baseline = json.loads((Path(__file__).parents[1] / "test_data/prompt_baseline.json").read_text())["prompts"][
        baseline_name
    ]
    config = get_config_from_spec(name)
    system = config["agent"]["system_template"]
    instance = config["agent"]["instance_template"]
    if name == "reuf2f":
        system = system.replace("solve Lean tasks", "solve programming tasks")
    assert system == baseline["system_template"]
    text = system + instance
    upper_ratio = 1.2 if name == "reuf2f" else 1.1
    assert 0.9 * baseline["words"] <= len(text.split()) <= upper_ratio * baseline["words"]
    # The Lean prompt adds boundary and library-usage bullets, not new control flow.
    line_tolerance = 6 if name == "reuf2f" else 4
    assert abs(len(text.splitlines()) - baseline["lines"]) <= line_tolerance
    assert [line for line in instance.splitlines() if line.startswith("#")] == baseline["headings"]
    for key in ("observation_template", "format_error_template"):
        assert hashlib.sha256(config["model"][key].encode()).hexdigest() == baseline[key + "_sha256"]
    start = instance.index(baseline["rules_start"])
    end = instance.index(baseline["rules_end"], start)
    assert hashlib.sha256(instance[start:end].encode()).hexdigest() == baseline["rules_sha256"]


def test_generic_lean_prompts_share_workflow_and_examples():
    mini, text, default = [get_config_from_spec(name)["agent"] for name in ("mini", "mini_textbased", "default")]
    assert text == {**default, "cost_limit": 3.0, "mode": "confirm"}
    for agent in (text, default):
        assert (
            mini["instance_template"].split("## Command Execution Rules")[0]
            == agent["instance_template"].split("## Important Rules")[0]
        )
        assert mini["instance_template"].split("## Useful command examples")[1] == agent["instance_template"].split(
            "## Useful command examples"
        )[1].replace("```mswea_bash_command", "```bash")


@pytest.mark.parametrize(("name", "system"), [("mini", "Darwin"), ("mini_textbased", "Darwin"), ("default", "Linux")])
def test_shell_examples_render_for_each_platform(name, system):
    prompt = Template(get_config_from_spec(name)["agent"]["instance_template"], undefined=StrictUndefined).render(
        task="Check Target.lean", system=system, release="test", version="test", machine="test"
    )
    assert ("sed -i ''" in prompt) == (system == "Darwin")
    assert "newfile.lean" in prompt and "example (n : Nat) : n + 0 = n := by" in prompt
    assert "rg -n --hidden --no-ignore" in prompt
