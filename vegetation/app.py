import cProfile
import pstats
from typing import Tuple

from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization.components.geospace_leaflet import make_geospace_leaflet
from patch.model import Vegetation, JoshuaTreeAgent
from patch.space import VegCell

# Very big bounds for western JOTR
# TST_JOTR_BOUNDS = [-116.380920, 33.933106, -116.163940, 34.042419]

# Medium bounds for testing
# TST_JOTR_BOUNDS = [-116.367188, 33.939942, -116.201019, 34.061193]

# Small-ish bounds
TST_JOTR_BOUNDS = [-116.326332, 33.975823, -116.289768, 34.004147]

# Very small bounds for testing
# TST_JOTR_BOUNDS = [-116.380920, 33.933106, -116.360920, 33.935106]

# TODO: Add conda lock file to prevent version issues

# TODO: Push working build to artifact registry, or dockerhub, or something, while
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

        if len(agent.jotr_agents) > 0:
            only_dead = all([a.life_stage == "dead" for a in agent.jotr_agents])
            if only_dead:
                return 100, 0, 0, 1

            has_breeders = any([a.life_stage == "breeding" for a in agent.jotr_agents])
            if has_breeders:
                return 0, 255, 0, 1

            has_adults = any([a.life_stage == "adult" for a in agent.jotr_agents])
            if has_adults:
                return 0, 200, 0, 1

            has_juveniles = any([a.life_stage == "juvenile" for a in agent.jotr_agents])
            if has_juveniles:
                return 0, 150, 0, 1

            has_seedlings = any([a.life_stage == "seedling" for a in agent.jotr_agents])
            if has_seedlings:
                return 0, 100, 0, 1

            has_seeds = any([a.life_stage == "seed" for a in agent.jotr_agents])
            if has_seeds:
                return 0, 50, 0, 1

        else:

            debug_normalized_elevation = int((agent.elevation / 5000) * 255)
            rgba = (
                debug_normalized_elevation,
                debug_normalized_elevation,
                debug_normalized_elevation,
                1,
            )
        return rgba

    if isinstance(agent, JoshuaTreeAgent):

        # For now, we don't want to show individual agents on the map,
        # but we get an error if we don't return something

        portrayal = {}
        portrayal["shape"] = "circle"
        portrayal["r"] = 2
        portrayal["color"] = "green"
        portrayal["opacity"] = 0.0

        return portrayal


model = Vegetation(bounds=TST_JOTR_BOUNDS)


page = SolaraViz(
    model,
    name="Veg Model",
    components=[
        make_geospace_leaflet(cell_portrayal, zoom=14),
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
    ],
    model_params=model_params,
)

if __name__ == "__main__":
    # Run your Solara app
    page  # noqa
