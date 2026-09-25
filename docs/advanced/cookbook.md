# Cookbook

!!! abstract "Remixing & extending Leanimum-agent"

    * Compose model, agent and environment classes to build a custom workflow.
    * Start with the [default agent control flow](control_flow.md).

!!! note "Development setup"

    Make sure to follow the dev setup instructions in [quickstart.md](../quickstart.md).

## Mix & match

Choose an [agent](../reference/agents/default.md),
[model](../reference/models/overview.md) and [environment](environments.md), then
combine them in a run script. Start with the configured example in
[Python bindings](../usage/python_bindings.md); subclasses still need the agent's
prompt templates and matching model configuration.

## Customizing execution

Handle a custom command with a Python function, leaving other commands unchanged.
This example treats `python_function` arguments as words, not shell expressions.
Each result includes the fields needed by the observation template.

=== "Subclassing the agent"

    ```python
    import shlex

    from leanimum.agents.default import DefaultAgent

    def python_function(*args: str) -> dict:
        return {"output": " ".join(args) + "\n", "returncode": 0, "exception_info": ""}

    class AgentWithPythonFunctions(DefaultAgent):
        def execute_actions(self, message: dict) -> list[dict]:
            outputs = []
            for action in message.get("extra", {}).get("actions", []):
                command = action.get("command", "")
                if command.split(maxsplit=1)[:1] == ["python_function"]:
                    outputs.append(python_function(*shlex.split(command)[1:]))
                else:
                    outputs.append(self.env.execute(action))
            return self.add_messages(*self.model.format_observation_messages(
                message, outputs, self.get_template_vars()
            ))
    ```

=== "Subclassing the environment"

    ```python
    import shlex

    from leanimum.environments.local import LocalEnvironment

    def python_function(*args: str) -> dict:
        return {"output": " ".join(args) + "\n", "returncode": 0, "exception_info": ""}

    class EnvironmentWithPythonFunctions(LocalEnvironment):
        def execute(self, action: dict, cwd: str = "") -> dict:
            command = action.get("command", "")
            if command.split(maxsplit=1)[:1] == ["python_function"]:
                return python_function(*shlex.split(command)[1:])
            return super().execute(action, cwd)
    ```

## Custom completion command

Exit when `submit` is issued as a standalone action:

=== "Subclassing the agent"

    ```python
    from leanimum.agents.default import DefaultAgent
    from leanimum.exceptions import Submitted

    class AgentQuitsOnSubmit(DefaultAgent):
        def execute_actions(self, message: dict) -> list[dict]:
            if [a.get("command", "") for a in message.get("extra", {}).get("actions", [])] == ["submit"]:
                raise Submitted({
                    "role": "exit",
                    "content": "The agent has finished its task.",
                    "extra": {"exit_status": "Submitted", "submission": ""},
                })
            return super().execute_actions(message)
    ```

=== "Subclassing the environment"

    ```python
    from leanimum.environments.local import LocalEnvironment
    from leanimum.exceptions import Submitted

    class EnvironmentQuitsOnSubmit(LocalEnvironment):
        def execute(self, action: dict, cwd: str = "") -> dict:
            if action.get("command", "") == "submit":
                raise Submitted({
                    "role": "exit",
                    "content": "The agent has finished its task.",
                    "extra": {"exit_status": "Submitted", "submission": ""},
                })
            return super().execute(action, cwd)
    ```

## Validate actions

Extend the configuration with patterns to reject before execution.
These checks illustrate subclassing; regex matching is not a security sandbox.

=== "Subclassing the agent"

    ```python
    import re
    from leanimum.agents.default import DefaultAgent, AgentConfig
    from leanimum.exceptions import FormatError

    class ValidatingAgentConfig(AgentConfig):
        forbidden_patterns: list[str] = [
            r"rm -rf /",
            r"sudo.*passwd",
            r"mkfs\.",
        ]

    class ValidatingAgent(DefaultAgent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, config_class=ValidatingAgentConfig)

        def execute_actions(self, message: dict) -> list[dict]:
            for action in message.get("extra", {}).get("actions", []):
                command = action.get("command", "")
                for pattern in self.config.forbidden_patterns:
                    if re.search(pattern, command, re.IGNORECASE):
                        raise FormatError(self.model.format_message(
                            role="user", content="Action blocked: forbidden pattern detected"
                        ))
            return super().execute_actions(message)
    ```

=== "Subclassing the environment"

    ```python
    import re
    from leanimum.environments.local import LocalEnvironment, LocalEnvironmentConfig

    class EnvironmentWithForbiddenPatternsConfig(LocalEnvironmentConfig):
        forbidden_patterns: list[str] = [
            r"rm -rf /",
            r"sudo.*passwd",
            r"mkfs\.",
        ]

    class EnvironmentWithForbiddenPatterns(LocalEnvironment):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, config_class=EnvironmentWithForbiddenPatternsConfig)

        def execute(self, action: dict, cwd: str = "") -> dict:
            command = action.get("command", "")
            for pattern in self.config.forbidden_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return {
                        "output": "Action blocked: forbidden pattern detected",
                        "returncode": 1,
                        "exception_info": "",
                    }
            return super().execute(action, cwd)
    ```

{% include-markdown "../_footer.md" %}
