import cProfile
import pstats
from typing import Tuple

from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_leaflet
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

model_params = {
    "num_steps": Slider("total number of steps", 20, 1, 100, 1),
    "export_data": False,
    "bounds": TST_JOTR_BOUNDS,
}


def cell_portrayal(agent):
    if isinstance(agent, VegCell):
        if agent.jotr_occupancy > 0:
            rgba = 0, 255, 0, 1
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

        # For now, we don't want to show individual agents on the map
        portrayal = {}
        # portrayal["shape"] = "circle"
        # portrayal["r"] = 2
        # portrayal["color"] = "green"
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
