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

        # TODO: It seems weird that we have duplicate time dimension, it seems like
        # stackstac should automatically ignore the `id` dimension which is just
        # is contains the cog name, which doesn't really matter to us. This check
        # ensures that there aren't overlap issues where we introduce some kind of
        # bias, but this seems like a code smell to me
        n_not_nan = np.unique(elevation.count(dim='time'))
        if not n_not_nan == [1]:
            raise ValueError(f"Some cells have no, or duplicate, elevation data. Unique number of non-nan values: {n_not_nan}")

        # Collapse along time dimension, ignoring COG source
        elevation = elevation.median(dim='time')

        __elevation_bands, elevation_height, elevation_width = elevation.shape

        self.raster_layer = mg.RasterLayer(
            model=self.model,
            height=elevation_height,
            width=elevation_width,
            # cell_cls=VegCell,
            total_bounds=self.bounds,
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

    @raster_layer.setter
    def raster_layer(self, value):
        if self.layers:
            self.layers[0] = value
        else:
            self.layers.append(value)

    def is_at_boundary(self, row_idx, col_idx):
        return (
            row_idx == 0
            or row_idx == self.raster_layer.height
            or col_idx == 0
            or col_idx == self.raster_layer.width
        )