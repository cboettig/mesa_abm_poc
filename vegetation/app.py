import cProfile
import pstats
from typing import Tuple

from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from patch.model import Vegetation, JoshuaTreeAgent
from patch.space import VegCell
from config.stages import LIFE_STAGE_RGB_VIZ_MAP

# Very big bounds for western JOTR
# TST_JOTR_BOUNDS = [-116.380920, 33.933106, -116.163940, 34.042419]

# Medium bounds for testing
# TST_JOTR_BOUNDS = [-116.367188, 33.939942, -116.201019, 34.061193]

# Small-ish bounds
TST_JOTR_BOUNDS = [-116.326332, 33.975823, -116.289768, 34.004147]

# Very small bounds for testing
# TST_JOTR_BOUNDS = [-116.380920, 33.933106, -116.360920, 33.935106]

# TODO: Add conda lock file to prevent version issues
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/11

# TODO: Push working build to artifact registry, or dockerhub, or something, while
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/10
# we wait on mesa-geo PR


model_params = {
    "num_steps": Slider("total number of steps", 20, 1, 100, 1),
    "export_data": False,
    "bounds": TST_JOTR_BOUNDS,
}


def cell_portrayal(agent):

    if isinstance(agent, VegCell):

        # This is very primitive, but essentially we color based on the furthest
        # life stage of any Joshua Tree agent in the cell. If there are no agents,
        # we color based on elevation.

        patch_life_stages = [agent.life_stage for agent in agent.jotr_agents]

        if len(patch_life_stages) > 0:

            max_stage = max(patch_life_stages)
            rgba = LIFE_STAGE_RGB_VIZ_MAP[max_stage]


        else:
            if not agent.refugia_status:
                debug_normalized_elevation = int((agent.elevation / 5000) * 255)
                rgba = (
                    debug_normalized_elevation,
                    debug_normalized_elevation,
                    debug_normalized_elevation,
                    .25,
                )
            else:
                rgba = (0, 255, 0, 1)
        return rgba

    if isinstance(agent, JoshuaTreeAgent):

        portrayal = {}
        portrayal["shape"] = "circle"
        portrayal["color"] = "red"
        portrayal["opacity"] = 0.0
        portrayal["fillOpacity"] = 0.0
        portrayal["stroke"] = False
        portrayal["radius"] = 0

        portrayal["description"] = f"Agent ID: {agent.unique_id}"

        return portrayal


model = Vegetation(bounds=TST_JOTR_BOUNDS)


page = SolaraViz(
    model,
    name="Veg Model",
    components=[
        make_geospace_component(cell_portrayal, zoom=14),
        make_plot_component(
            [
                "Mean Age",
                "N Agents",
                "N Seeds",
                "N Seedlings",
                "N Juveniles",
                "N Adults",
                "N Breeding",
            ],
        ),
        make_plot_component(
            ["% Refugia Cells Occupied"],
        ),
    ],
    model_params=model_params,
)

if __name__ == "__main__":
    # Run your Solara app
    page  # noqa
