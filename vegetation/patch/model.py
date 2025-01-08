import mesa
import mesa_geo as mg
import numpy as np
from shapely.geometry import Point
import random
import json
from scipy.stats import poisson
from pyproj import Transformer

from config.stages import LifeStage
from patch.space import StudyArea
from config.transitions import (
    JOTR_JUVENILE_AGE,
    JOTR_REPRODUCTIVE_AGE,
    JOTR_ADULT_AGE,
    JOTR_SEED_DISPERSAL_DISTANCE,
    get_jotr_emergence_rate,
    get_jotr_survival_rate,
    get_jotr_breeding_poisson_lambda,
)
from config.paths import INITIAL_AGENTS_PATH

JOTR_UTM_PROJ = "+proj=utm +zone=11 +ellps=WGS84 +datum=WGS84 +units=m +no_defs +north"
STD_INDENT = "    "

class JoshuaTreeAgent(mg.GeoAgent):
    def __init__(self, model, geometry, crs, age=None, parent_id=None):
        super().__init__(
            model=model,
            geometry=geometry,
            crs=crs,
        )

        self.age = age
        self.parent_id = parent_id
        self.life_stage = None

        # TODO: When we create the agent, we need to know its own indices relative
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/6
        # to the rasterlayer. This seems like very foundational mesa / mesa-geo stuff,
        # which should be handled by the GeoAgent or GeoBase, but the examples are
        # inconsistent. For now, invert the affine transformation to get the indices,
        # converting from geographic (lat, lon) to raster (col, row) coordinates

        self.float_indices = ~self.model.space.raster_layer._transform * (
            np.float64(geometry.x),
            np.float64(geometry.y),
        )

        # According to wang-boyu, mesa-geo maintainer:
        # pos = (x, y), with an origin at the lower left corner of the raster grid
        # indices = (row, col) format with an origin at the upper left corner of the raster grid
        # See https://github.com/projectmesa/mesa-geo/issues/267

        # pos = (np.float64(geometry.x), np.float64(geometry.y))
        # self._pos = pos

        self.indices = (int(self.float_indices[0]), int(self.float_indices[1]))
        self._pos = (
            self.indices[0],
            self.model.space.raster_layer.height - self.indices[1],
        )

        # TODO: Figure out how to set the life stage on init
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/3
        # Seems natural to set the life stage on init, but in
        # see lines 181-190 in mesa_geo/geoagent.py, the agents are instantiated before the
        # GeoAgent gets the attributes within the geojson, so we need to call _update_life_stage
        # after init when the age is known to the agent

        # self._update_life_stage()

    def step(self):

        # Save initial life stage for logging
        initial_life_stage = self.life_stage

        # Check if agent is dead - if yes, skip
        if self.life_stage == LifeStage.DEAD:
            return

        # Find the underlying cell - it must exist, else raise an error
        intersecting_cell_filter = self.model.space.raster_layer.iter_neighbors(
            self.indices, moore=False, include_center=True, radius=0
        )
        intersecting_cell = next(intersecting_cell_filter)
        if not intersecting_cell:
            raise ValueError("No intersecting cell found")

        # If seed, get emergence rate, if not, get survival rate
        if self.life_stage == LifeStage.SEED:
            survival_rate = get_jotr_emergence_rate(intersecting_cell.aridity)
        else:
            survival_rate = get_jotr_survival_rate(
                self.life_stage,
                intersecting_cell.aridity,
                0,  # Assume no nurse plants for now
            )

        # Roll the dice to see if the agent survives
        dice_roll_zero_to_one = random.random()

        # Check survival, comparing dice roll to survival rate
        if dice_roll_zero_to_one < survival_rate:
            print(
                f"{STD_INDENT*1}💪 Agent {self.unique_id} ({self.life_stage.name}, age {self.age}) survived! (dice roll {dice_roll_zero_to_one:.2f} w/ survival prob {survival_rate:.2f})"
            )

        else:
            print(
                f"{STD_INDENT*1}💀 Agent {self.unique_id} ({self.life_stage.name}, age {self.age}) died! (dice roll {dice_roll_zero_to_one:.2f} w/ survival prob {survival_rate:.2f})"
            )
            self.life_stage = LifeStage.DEAD


        # Increment age
        self.age += 1
        life_stage_promotion = self._update_life_stage()

        if life_stage_promotion:
            print(
                f"{STD_INDENT*2}🔄 Agent {self.unique_id} ({initial_life_stage.name}) promoted to {self.life_stage.name}!"
            )

        # Update underlying patch
        intersecting_cell.update_occupancy(self)

        # Disperse
        if self.life_stage == LifeStage.BREEDING:
            jotr_breeding_poisson_lambda = get_jotr_breeding_poisson_lambda(
                intersecting_cell.aridity
            )
            n_seeds = poisson.rvs(jotr_breeding_poisson_lambda)

            self.disperse_seeds(n_seeds)

    def _update_life_stage(self):

        initial_life_stage = self.life_stage

        if self.life_stage == LifeStage.DEAD:
            return

        age = self.age if self.age else 0
        if age == 0:
            life_stage = LifeStage.SEED
        elif age > 0 and age <= JOTR_JUVENILE_AGE:
            life_stage = LifeStage.SEEDLING
        elif age >= JOTR_JUVENILE_AGE and age <= JOTR_ADULT_AGE:
            life_stage = LifeStage.JUVENILE
        elif age > JOTR_ADULT_AGE and age < JOTR_REPRODUCTIVE_AGE:
            life_stage = LifeStage.ADULT
        else:
            life_stage = LifeStage.BREEDING
        self.life_stage = life_stage

        if initial_life_stage != self.life_stage:
            return True
        else:
            return False

    def disperse_seeds(
        self, n_seeds, max_dispersal_distance=JOTR_SEED_DISPERSAL_DISTANCE
    ):

        if self.life_stage != LifeStage.BREEDING:
            raise ValueError(
                f"Agent {self.unique_id} is not breeding and cannot disperse seeds"
            )

        print(f"{STD_INDENT*2}🌰 Agent {self.unique_id} ({self.life_stage.name}) is dispersing {n_seeds} seeds...")

        # TODO: Use the best projection for valid seed dispersal
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/12
        # For now this uses UTM zone 11N, cuz it's in meters and
        # works, but it may not be best for accurate linear distance?

        # Create transformers to disperse seeds accurately in meters
        wgs84_to_utm = Transformer.from_crs("EPSG:4326", JOTR_UTM_PROJ, always_xy=True)
        utm_to_wgs84 = Transformer.from_crs(JOTR_UTM_PROJ, "EPSG:4326", always_xy=True)

        # Transform parent location to UTM
        x_utm, y_utm = wgs84_to_utm.transform(self.geometry.x, self.geometry.y)

        for __seed_idx in np.arange(0, n_seeds):
            # Random direction in radians
            angle = random.uniform(0, 2 * np.pi)

            # Random distance in meters, up to dispersal distance
            dispersal_distance = random.uniform(0, max_dispersal_distance)

            # Calculate new seed location in UTM
            seed_x_utm = x_utm + dispersal_distance * np.cos(angle)
            seed_y_utm = y_utm + dispersal_distance * np.sin(angle)

            # Transform back to WGS84
            seed_x_wgs84, seed_y_wgs84 = utm_to_wgs84.transform(seed_x_utm, seed_y_utm)

            # Create new seed agent
            seed_agent = JoshuaTreeAgent(
                model=self.model,
                geometry=Point(seed_x_wgs84, seed_y_wgs84),
                crs=self.crs,
                age=0,
                parent_id=self.unique_id,
            )
            seed_agent._update_life_stage()

            # Add the seed agent to the model
            self.model.space.add_agents(seed_agent)
            delta_x_index = self.indices[0] - seed_agent.indices[0]
            delta_y_index = self.indices[1] - seed_agent.indices[1]

            print(
                f"{STD_INDENT*3}➕ Seed ({seed_agent.unique_id}, lifestage {seed_agent.life_stage}) to {seed_agent._pos} (🔺index: {delta_x_index}, {delta_y_index})"
            )


class Vegetation(mesa.Model):
    def __init__(self, bounds, export_data=False, num_steps=20, epsg=4326):
        super().__init__()
        self.bounds = bounds
        self.export_data = export_data
        self.num_steps = num_steps

        self.space = StudyArea(bounds, epsg=epsg, model=self)

        self.space.get_elevation()
        self.space.get_aridity()

        with open(INITIAL_AGENTS_PATH, "r") as f:
            initial_agents_geojson = json.loads(f.read())

        agents = mg.AgentCreator(JoshuaTreeAgent, model=self).from_GeoJSON(
            initial_agents_geojson
        )

        # TODO: Find a way to update life stage on init
        # Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/9
        # Since .from_GeoJSON() sets attributes after init, we call
        # _update_life_stage after init, but before we add to the grid
        self.agents.select(agent_type=JoshuaTreeAgent).do("_update_life_stage")

        self.space.add_agents(agents)
        self.update_metrics()

        self.datacollector = mesa.DataCollector(
            {
                "Mean Age": "mean_age",
                "N Agents": "n_agents",
                "N Seeds": "n_seeds",
                "N Seedlings": "n_seedlings",
                "N Juveniles": "n_juveniles",
                "N Adults": "n_adults",
                "N Breeding": "n_breeding",
            }
        )

    # @property
    def update_metrics(self):
        # Mean age
        mean_age = self.agents.select(agent_type=JoshuaTreeAgent).agg("age", np.mean)
        self.mean_age = mean_age

        # Number of agents (JoshuaTreeAgent)
        n_agents = len(self.agents.select(agent_type=JoshuaTreeAgent))
        self.n_agents = n_agents

        # Number of agents by life stage
        count_dict = (
            self.agents.select(agent_type=JoshuaTreeAgent).groupby("life_stage").count()
        )
        self.n_seeds = count_dict.get(LifeStage.SEED, 0)
        self.n_seedlings = count_dict.get(LifeStage.SEEDLING, 0)
        self.n_juveniles = count_dict.get(LifeStage.JUVENILE, 0)
        self.n_adults = count_dict.get(LifeStage.ADULT, 0)
        self.n_breeding = count_dict.get(LifeStage.BREEDING, 0)

    def step(self):
        # Print timestep header
        timestep_str = f"# {STD_INDENT*0}🕰️ Time passes. It is the year {self.steps} #"
        nchar_timestep_str = len(timestep_str)
        print("#" * (nchar_timestep_str - 1))
        print(timestep_str)
        print("#" * (nchar_timestep_str - 1))
        print("\n")

        # Step agents
        self.agents.shuffle_do("step")
        self.update_metrics()

        # Print end of timestep summary (just padding)
        print("\n")

        # Collect data
        self.datacollector.collect(self)
