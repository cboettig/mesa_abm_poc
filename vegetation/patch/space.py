from __future__ import annotations

import mesa
import mesa_geo as mg
import numpy as np
import stackstac
from pystac_client import Client as PystacClient
import planetary_computer
# import rioxarray as rxr

DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"

class VegCell(mg.Cell):
    elevation: int | None
    aridity: int | None

    def __init__(
        self,
        model,
        pos: mesa.space.Coordinate | None = None,
        indices: mesa.space.Coordinate | None = None,
    ):
        super().__init__(model, pos, indices)
        self.elevation = None
        self.aridity = None

    def step(self):
        pass


class StudyArea(mg.GeoSpace):
    def __init__(self, bounds, epsg, model):
        super().__init__(crs=f"epsg:{epsg}")
        self.bounds = bounds
        self.model = model
        self.epsg = epsg

        self.pystac_client = PystacClient.open(
            DEM_STAC_PATH, modifier=planetary_computer.sign_inplace
        )

    def get_elevation(self):

        items_generator = self.pystac_client.search(
            collections=["cop-dem-glo-30"],
            bbox=self.bounds,
        ).get_items()

        items = [item for item in items_generator]

        elevation = stackstac.stack(
            items=items,
            assets=["data"],
            bounds=self.bounds,
            epsg=self.epsg,
        )

        self.raster_layer = mg.RasterLayer(
            model=self.model,
            height=self.height,
            width=self.width,
            cell_cls=VegCell,
            crs=f"epsg:{self.epsg}",
        )

        self.raster_layer.apply_raster(
            data=elevation,
            attr_name="elevation",
        )
        super().add_layer(self.raster_layer)

    def get_aridity(self):
        self.raster_layer = mg.RasterLayer(
            model=self.model,
            height=self.raster_layer.height,
            width=self.raster_layer.width,
            cell_cls=VegCell,
            crs=f"epsg:{self.epsg}",
        )

        # TODO: Use something axtually real, but for now, assume this is an
        # inverse relationship with elevation, with a little noise
        inverse_elevation = np.array(
            (10000 - self.raster_layer.data["elevation"] + random.random_int(0,1000)) / 10000
        )

        self.raster_layer.apply_raster(
            data=inverse_elevation,
            attr_name="water_level",
        )
        super().add_layer(self.raster_layer)

    @property
    def raster_layer(self):
        return self.layers[0]

    def is_at_boundary(self, row_idx, col_idx):
        return (
            row_idx == 0
            or row_idx == self.raster_layer.height
            or col_idx == 0
            or col_idx == self.raster_layer.width
        )