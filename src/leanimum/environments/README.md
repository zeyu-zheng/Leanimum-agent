# Environments

* `local.py` - Execute code with `subprocess.run`
* `docker.py` - Execute code in a Docker or Podman container
* `singularity.py` - Execute code in a Singularity or Apptainer container

## Extras

* `extra/swerex_docker.py` - Execute environments with docker via [swerex](https://github.com/swe-agent/swe-rex)
* `extra/swerex_modal.py` - Execute environments with [Modal](https://modal.com) via [swerex](https://github.com/swe-agent/swe-rex)
* `extra/bubblewrap.py` - Execute environments with [bubblewrap](https://github.com/containers/bubblewrap)
* `extra/contree.py` - Execute commands in ConTree sandboxes

The [ReuF2F runner](../../../docs/usage/reuf2f.md) supports Docker/Podman and local
execution. The generic CLI can select the other backends above.
