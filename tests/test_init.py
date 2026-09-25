"""Tests for leanimum.__init__."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_startup_banner_survives_non_utf8_stdout(tmp_path):
    """Importing the package must not crash when stdout can't encode the startup banner (e.g. Windows cp1252)."""
    env = {
        **os.environ,
        "PYTHONIOENCODING": "cp1252",
        "LEANA_SILENT_STARTUP": "",
        "LEANA_GLOBAL_CONFIG_DIR": str(tmp_path),
    }
    result = subprocess.run([sys.executable, "-c", "import leanimum"], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(("override", "label"), [(False, "default"), (True, "custom")])
def test_global_config_directory(tmp_path, override, label):
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "LEANA_SILENT_STARTUP": "1",
    }
    env.pop("LEANA_GLOBAL_CONFIG_DIR", None)
    if override:
        env["LEANA_GLOBAL_CONFIG_DIR"] = str(tmp_path / label)
    code = """
import json
from platformdirs import user_config_dir
from leanimum import global_config_dir, global_config_file
print(json.dumps([str(global_config_dir), str(global_config_file), user_config_dir("leanimum-agent")]))
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=True)
    directory, config_file, default = json.loads(result.stdout)
    assert directory == (str(tmp_path / label) if override else default)
    assert config_file == str(Path(directory) / ".env")
