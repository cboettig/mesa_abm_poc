from typing import Tuple

from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_leaflet
from vegetation.model import Vegetation
from vegetation.space import VegCell

model_params = {
    "num_steps": Slider("total number of steps", 20, 1, 100, 1),
    "export_data": False,
}


def cell_portrayal(cell: VegCell) -> Tuple[float, float, float, float]:
    return cell.elevation, cell.elevation, cell.elevation, 1


model = Vegetation()
page = SolaraViz(
    model,
    [
        make_geospace_leaflet(cell_portrayal, zoom=11),
        make_plot_component(
            ["Total Biomass"]
        ),
    ],
    name="Veg Model",
    model_params=model_params,
)

page  # noqa
