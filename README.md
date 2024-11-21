## Dev setup

### Using devcontainer

If going the dev container route, you will need the following:

- Docker (cli, but optionally the desktop app)
- VSCode, and the `Dev Containers` extension
- `ssh` installed on the host machine, to access git from within

After cloning the repo, you will need to open it in VSCode and run the following command:

- `Cmd + Shift + P -> Dev Containers: Reopen in Container`

## Simulations

The demo simulation here is derived from `mesa-geo`'s [Rainfall Model](https://github.com/projectmesa/mesa-examples/tree/main/gis/rainfall).

## Running the Solara server

To run Solara, it's recommended to use the included VSCode launch config (which will be detected automatically by VSCode within the debug panel). Simply fire it up and click the localhost link to use the Solara dashboard.

Alternatively, the simulation can be run the same way (without debugging) via the following command within the `rainfall` folder:

```bash
solara run app.py
```
