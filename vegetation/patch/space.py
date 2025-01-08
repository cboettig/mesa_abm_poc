from __future__ import annotations

import mesa
import mesa_geo as mg
import numpy as np
import stackstac
from pystac_client import Client as PystacClient
import planetary_computer
import random
import os
import hashlib
import logging
import time

# from patch.model import JoshuaTreeAgent
# import rioxarray as rxr

DEM_STAC_PATH = "https://planetarycomputer.microsoft.com/api/stac/v1/"
LOCAL_STAC_CACHE_FSTRING = "/local_dev_data/{band_name}_{bounds_md5}.tif"
SAVE_LOCAL_STAC_CACHE = True


class VegCell(mg.Cell):
    elevation: int | None
    aridity: int | None
    refugia: bool = False

    def __init__(
        self,
        model,
        pos: mesa.space.Coordinate | None = None,
        indices: mesa.space.Coordinate | None = None,
    ):
        super().__init__(model, pos, indices)
        self.elevation = None
        self.aridity = None

        # TODO: Improve patch level tracking of JOTR agents
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/1
        # For now, this is somewhat of a hack to track which agents are present within a patch cell
        # This is something I suspect is an offshoot of my question posed to the mesa-geo team
        # (https://github.com/projectmesa/mesa-geo/issues/267), where the cell does not have a geometry
        # and thus I can't use the various geometry based intersection methods to find agents. My guess
        # is that this will either not work or be very slow, but itll get us started
        self.jotr_agents = []

    def step(self):
        pass

    def update_occupancy(self, jotr_agent):
        if jotr_agent.life_stage and jotr_agent not in self.jotr_agents:
            self.jotr_agents.append(jotr_agent)


class StudyArea(mg.GeoSpace):
    def __init__(self, bounds, epsg, model):
        super().__init__(crs=f"epsg:{epsg}")
        self.bounds = bounds
        self.model = model
        self.epsg = epsg

        # For local development, we want to cache the STAC data so we don't
        # have to download it every time. This hash is used to uniquely identify
        # the bounds of the study area, so that we can grab if we already have it
        self.bounds_md5 = hashlib.md5(str(bounds).encode()).hexdigest()

        self.pystac_client = None
        if not LOCAL_STAC_CACHE_FSTRING:
            self.pystac_client = PystacClient.open(
                DEM_STAC_PATH, modifier=planetary_computer.sign_inplace
            )

    def get_elevation(self):

        local_elevation_path = LOCAL_STAC_CACHE_FSTRING.format(
            band_name="elevation",
            bounds_md5=self.bounds_md5,
        )

        if os.path.exists(local_elevation_path):

            print(f"Loading elevation from local cache: {local_elevation_path}")

            try:
                elevation_layer = mg.RasterLayer.from_file(
                    raster_file=local_elevation_path,
                    model=self.model,
                    cell_cls=VegCell,
                    attr_name="elevation",
                )
            except Exception as e:
                logging.warning(
                    f"Failed to load elevation from local cache ({local_elevation_path}): {e}"
                )
                raise e

        else:

            print("No local cache found, downloading elevation from STAC")
            time_at_start = time.time()

            elevation = self.get_elevation_from_stac()

            __elevation_bands, elevation_height, elevation_width = elevation.shape

            elevation_layer = mg.RasterLayer(
                model=self.model,
                height=elevation_height,
                width=elevation_width,
                # cell_cls=VegCell,
                total_bounds=self.bounds,
                # crs=f"epsg:{self.epsg}",
                crs=self.crs,
            )

            elevation_layer.apply_raster(
                data=elevation,
                attr_name="elevation",
            )

            if SAVE_LOCAL_STAC_CACHE:
                print(f"Saving elevation to local cache: {local_elevation_path}")
                elevation_layer.to_file(local_elevation_path)

            print(f"Downloaded elevation in {time.time() - time_at_start} seconds")

        super().add_layer(elevation_layer)

    def get_aridity(self):

        # TODO: Use something axtually real, but for now, assume this is an
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/8
        # positive relationship with elevation, with a little noise. This is
        # smelly because it relies on elevation being set first, but it's
        # a placeholder for now
        elevation_array = self.raster_layer.get_raster("elevation")
        inverse_elevation = np.array(elevation_array + random.uniform(-300, 300))

        self.raster_layer.apply_raster(
            data=inverse_elevation,
            attr_name="aridity",
        )
        super().add_layer(self.raster_layer)

    def get_refugia_status(self):
        elevation_array = self.raster_layer.get_raster("elevation")
        ninetyfive_percentile = np.percentile(elevation_array, 95)
        refugia = elevation_array > ninetyfive_percentile

        self.raster_layer.apply_raster(
            data=refugia,
            attr_name="refugia",
        )
        super().add_layer(self.raster_layer)

    def get_elevation_from_stac(self):

        print("Collecting STAC Items")
        items_generator = self.pystac_client.search(
            collections=["cop-dem-glo-30"],
            bbox=self.bounds,
        ).items()

        items = [item for item in items_generator]
        print(f"Found {len(items)} items")

        print("Stacking STAC Items")
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

        print("Checking for duplicate elevation data")
        n_not_nan = np.unique(elevation.count(dim="time"))
        if not n_not_nan == [1]:
            raise ValueError(
                f"Some cells have no, or duplicate, elevation data. Unique number of non-nan values: {n_not_nan}"
            )

        # Collapse along time dimension, ignoring COG source
        print("Collapsing time dimension")
        elevation = elevation.median(dim="time")

        return elevation

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
