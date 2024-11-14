## Dev setup

### Using devcontainer

If going the dev container route, you will need the following:

- Docker (cli, but optionally the desktop app)
- VSCode, and the `Dev Containers` extension
- `ssh` installed on the host machine, to access git from within

After cloning the repo, you will need to open it in VSCode and run the following command:

- `Cmd + Shift + P -> Dev Containers: Reopen in Container`

### Using local setup

If foregoing the dev container, you will need the following:

- Conda (to create and manage the python environment and its dependencies)
- NetLogo (version 6.1.0)
- OpenJDK 8 (for NetLogo)

After netlogo installation, you will need to set:

- `NETLOGO_HOME` environment variable to the path of the NetLogo installation directory.
- `JAVA_HOME` environment variable to the path of the OpenJDK 8 installation directory.
- `NETLOGO_VERSION` environment variable to the version of NetLogo installed, to the major version and minor (e.g. 6.1).

VSCode is recommended for development, but not required. If using VSCode, the following extensions are recommended:

- debugpy, for debugging python code and using the included `launch.json` configuration
- `python` and `flake8` for linting and code formatting

#### Using Ubuntu 20.04 LTS

If using Ubuntu 20.04 LTS, you can install the required dependencies with the following included workflow (assuming you already have conda):

- `.devcontainer/scripts/install_git_and_ssh.sh` will install git and ssh
- `.devcontainer/scripts/install_netlogo.sh` will install NetLogo and its Java dependency, as well as instantiate the relevant env vars
- `conda install .devcontainer/python_environment.yml` will install the python dependencies. Remember to `conda init` and `conda activate netlogo` to activate the environment.

#### Using Windows or MacOS

If using Windows or MacOS, you will need to install the dependencies manually. The included scripts are written for Ubuntu, and will not work on Windows or MacOS. In this case, it is highly recommended to use the devcontainer, as it will handle the installation of the dependencies for you.

## User Environment

This repo uses a `.env` file in the root of the repo (which can be copied and modified from `.devcontainer.env`). This file is read into the simulation itself in order to set user-specific environment vars - in this case, its a toy variable with no real meaning (the name of the results csv):

```
VERY_SPECIAL_NAME_FOR_MY_RESULTS_CSV = my_special_name
```

Note that this must be done manually regardless of whether you use the dev container workflow or install locally. `.env` is ignored by git, so everyone working on the repo can have their own user environment vars that do not conflict with one another.

## Simulations

This toy repo relies on:

- NetLogo
- pynetlogo

The example analysis (within main.py) is pulled directly from the pynetlogo documentation, with some minor modifications for simplicity.

To run the simulation, you can use the following command (from a terminal with the `netlogo` environment activated):

```bash
python simulation/main.py
```

Or, optionally, you can use the included `launch.json` configuration to debug the simulation using VSCode's debug panel - which essentially does the exact same thing, unless you add a breakpoint, which will stop the simulation at that point. This can be very helpful both for understanding the simulation code and for debugging.
