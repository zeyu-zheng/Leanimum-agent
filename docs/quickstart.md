# Quick start

Install this checkout with Python 3.10 or newer:

```bash
git clone https://github.com/zeyu-zheng/Leanimum-agent.git
cd Leanimum-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
leani-extra config setup
```

Run in a prepared Lean project:

```bash
leani -c mini.yaml -c environment.cwd=/absolute/path/to/project \
  -t "Complete the proof of Example.target in Example.lean and check it."
```

`mini.yaml` uses bash tool calls; `mini_textbased.yaml` uses one
`mswea_bash_command` code block. Both contain Lean and native Comparator guidance.
If you pass `-c`, include a full configuration before your overrides.

The main CLI confirms commands by default. `--yolo` disables confirmation, not
filesystem restrictions. Local execution has no sandbox. Read the chosen backend's
requirements before allowing an agent to install tools or execute unfamiliar code.

To work on the only built-in benchmark:

```bash
leani-extra reuf2f --subset /tmp/reuf2f-tasks --slice 0:1 \
  -m YOUR_MODEL -o /tmp/reuf2f-run
```

Export the release with ReuF2F's `prepare-tasks` first. The runner uses the shared
`zeyuzhenghub/lean4:v4.33.1` image on `linux/amd64` by default. See
[ReuF2F](usage/reuf2f.md) for the default Docker batch flow and independent Comparator scoring.
The commands above install from source; no published distribution is assumed.
