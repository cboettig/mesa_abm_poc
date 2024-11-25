from __future__ import annotations

import gzip

import mesa
import mesa_geo as mg
import numpy as np


class VegCell(mg.Cell):
    elevation: int | None
    water_level: int | None
    water_level_normalized: float | None

    def __init__(
        self,
        model,
        pos: mesa.space.Coordinate | None = None,
        indices: mesa.space.Coordinate | None = None,
    ):
        super().__init__(model, pos, indices)
        self.elevation = None
        self.water_level = None

    def step(self):
        pass


class StudyArea(mg.GeoSpace):
    def __init__(self, crs, water_height, model):
        super().__init__(crs=crs)
        self.model = model
        self.water_height = water_height
        self.outflow = 0

    def set_elevation_layer(self, elevation_gzip_file, crs):
        raster_layer = mg.RasterLayer.from_file(
            elevation_gzip_file,
            model=self.model,
            cell_cls=VegCell,
            attr_name="elevation",
            rio_opener=gzip.open,
        )
        raster_layer.crs = crs
        raster_layer.apply_raster(
            data=np.zeros(shape=(1, raster_layer.height, raster_layer.width)),
            attr_name="water_level",
        )
        super().add_layer(raster_layer)

    def set_water_level(self, water_level_bounds, crs):
        raster_layer = mg.RasterLayer(
            model=self.model,
            height=self.raster_layer.height,
            width=self.raster_layer.width,
            cell_cls=VegCell,
            crs=crs,
        )

        random_init = np.random.uniform(
            low=water_level_bounds[0], high=water_level_bounds[1],
            size=(raster_layer.height, raster_layer.width),
        )

        raster_layer.apply_raster(
            data=random_init,
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