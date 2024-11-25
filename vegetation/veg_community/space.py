from __future__ import annotations

import gzip

import mesa
import mesa_geo as mg
import numpy as np
import stackstac
import rioxarray as rxr

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
    def __init__(self, bounds, crs, model):
        super().__init__(crs=crs)
        self.bounds = bounds
        self.model = model
        self.crs = crs

    def get_elevation(self, crs):
        self.raster_layer = mg.RasterLayer(
            model=self.model,
            height=self.height,
            width=self.width,
            cell_cls=VegCell,
            crs=crs,
        )
        raster_layer.crs = crs

        elevation = stackstac.stack(
            urls=['https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-30'],
            assets=['elevation'],
            bounds=self.bounds,
            resolution=30,
            epsg=crs,
        )

        raster_layer.apply_raster(
            data=elevation,
            attr_name="elevation",
        )
        super().add_layer(raster_layer)

    def get_aridity(self, crs):
        raster_layer = mg.RasterLayer(
            model=self.model,
            height=self.raster_layer.height,
            width=self.raster_layer.width,
            cell_cls=VegCell,
            crs=crs,
        )

        # 
        inverse_elevation = np.array(
            (10000 - self.raster_layer.data["elevation"]) / 10000
        )

        raster_layer.apply_raster(
            data=inverse_elevation,
            attr_name="water_level",
        )


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