import json
import re

import pytest
from jinja2 import StrictUndefined, Template
from pydantic import ValidationError

from leanimum.agents.default import AgentConfig
from leanimum.config import get_config_from_spec
from leanimum.exceptions import FormatError
from leanimum.models.litellm_textbased_model import LitellmTextbasedModelConfig
from leanimum.models.utils.actions_text import parse_regex_actions
from leanimum.models.utils.actions_toolcall import parse_toolcall_actions


@pytest.mark.parametrize(
    ("name", "json_output"), [("mini", True), ("mini_textbased", False), ("default", False), ("reuf2f", False)]
)
@pytest.mark.parametrize(("size", "truncated"), [(80, False), (9999, False), (10000, True), (11000, True)])
def test_observation_output_boundary(name, json_output, size, truncated):
    template = Template(get_config_from_spec(name)["model"]["observation_template"], undefined=StrictUndefined)
    output = ('"\n\\' * ((size + 2) // 3))[:size]
    rendered = template.render(output={"returncode": 3, "output": output, "exception_info": "fixture error"})
    if json_output:
        result = json.loads(rendered)
        assert result["returncode"] == 3 and result["exception_info"] == "fixture error"
        assert ("warning" in result) == truncated
        if truncated:
            assert result["output_head"] == output[:5000]
            assert result["output_tail"] == output[-5000:]
            assert result["elided_chars"] == size - 10000
        else:
            assert result["output"] == output
    else:
        assert "<returncode>3</returncode>" in rendered
        assert "<exception>fixture error</exception>" in rendered
        assert ("<warning>" in rendered) == truncated
        if truncated:
            assert output[:5000] in rendered and output[-5000:] in rendered
            assert f"{size - 10000} characters elided" in rendered
        else:
            assert output in rendered and "<output_head>" not in rendered


@pytest.mark.parametrize(
    ("name", "text_based"), [("mini", False), ("mini_textbased", True), ("default", True), ("reuf2f", False)]
)
def test_all_prompts_are_lean_and_match_action_protocol(name, text_based):
    config = get_config_from_spec(name)
    prompt = Template(config["agent"]["instance_template"], undefined=StrictUndefined).render(
        task="Prove Nat.add_zero without sorry", system="Linux", release="test", version="test", machine="x86_64"
    )
    assert "Lean" in config["agent"]["system_template"] + prompt
    for text in ("Nat.add_zero", "Mathlib", "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"):
        assert text in prompt
    # The ReuF2F prompt follows mini-swe-agent's SWE-bench prompt, which names no grader.
    assert ("Comparator" in prompt) == (name != "reuf2f")
    assert config["environment"]["timeout"] == (1200 if name == "reuf2f" else 600)
    if text_based:
        assert config["model"]["model_class"] == "litellm_textbased"
        model = LitellmTextbasedModelConfig(model_name="fixture", **config["model"])
        example = re.search(r"```leana_bash_command\n.*?\n```", config["agent"]["system_template"], re.DOTALL)
        assert example is not None
        assert parse_regex_actions(
            example[0], action_regex=model.action_regex, format_error_template=model.format_error_template
        ) == [{"command": "your_command_here"}]
    else:
        assert "bash tool call" in prompt


def test_agent_config_requires_templates():
    with pytest.raises(ValidationError, match="validation error"):
        AgentConfig()


def test_reuf2f_prompt_states_the_submission_contract():
    prompt = get_config_from_spec("reuf2f")["agent"]["instance_template"]
    for required in (
        "original theorem",
        "_neg",
        "DO NOT MODIFY: Target statements",
        "lakefile.toml library layout may change",
        "Register new helper libraries with `[[lean_lib]]`",
        "import the needed modules in the task file",
        "rg 'PATTERN' .lake/packages/mathlib/Mathlib",
        "Do NOT commit your changes.",
        "git add path/to/file1 path/to/file2 && git diff --cached > patch.txt",
        "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt",
    ):
        assert required in prompt


@pytest.mark.parametrize(
    ("name", "text_based"), [("mini", False), ("mini_textbased", True), ("default", True), ("reuf2f", False)]
)
@pytest.mark.parametrize(("reason",), [("stop",), ("length",), ("tool_calls",)])  # noqa: PT006
def test_configured_format_error_renders(name, text_based, reason):
    config = get_config_from_spec(name)["model"]
    if text_based:
        model = LitellmTextbasedModelConfig(model_name="fixture", **config)
        with pytest.raises(FormatError) as error:
            parse_regex_actions(
                "Missing command",
                action_regex=model.action_regex,
                format_error_template=model.format_error_template,
                template_kwargs={"finish_reason": reason},
            )
    else:
        with pytest.raises(FormatError) as error:
            parse_toolcall_actions(
                [],
                format_error_template=config["format_error_template"],
                template_kwargs={"finish_reason": reason},
            )
    message = error.value.messages[0]
    assert message["role"] == "user" and message["extra"]["interrupt_type"] == "FormatError"
    assert ("output token limit" in message["content"]) == (reason != "stop")
    if reason == "stop":
        assert ("leana_bash_command" if text_based else "bash") in message["content"]


@pytest.mark.parametrize(("name", "system"), [("mini", "Darwin"), ("mini_textbased", "Darwin"), ("default", "Linux")])
def test_shell_examples_render_for_each_platform(name, system):
    prompt = Template(get_config_from_spec(name)["agent"]["instance_template"], undefined=StrictUndefined).render(
        task="Check Target.lean", system=system, release="test", version="test", machine="test"
    )
    assert ("sed -i ''" in prompt) == (system == "Darwin")
    assert "newfile.lean" in prompt and "example (n : Nat) : n + 0 = n := by" in prompt
    assert "rg -n --hidden --no-ignore" in prompt
