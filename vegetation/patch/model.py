import mesa
import mesa_geo as mg
import numpy as np
from shapely.geometry import Point
import random
import json

from patch.space import StudyArea
from config.transitions import (
    JOTR_JUVENILE_AGE,
    JOTR_REPRODUCTIVE_AGE,
    JOTR_ADULT_AGE,
    JOTR_SEED_DISPERSAL_DISTANCE,
    get_jotr_emergence_rate,
    get_jotr_survival_rate
)
from config.paths import INITIAL_AGENTS_PATH


class JoshuaTreeAgent(mg.GeoAgent):
    def __init__(self, model, geometry, crs, age=None):
        super().__init__(
            model=model,
            geometry=geometry,
            crs=crs,
        )

        self.age = age

        pos = (np.float64(geometry.x), np.float64(geometry.y))
        self._pos = pos

        # TODO: When we create the agent, we need to know its own indices relative
        # to the rasterlayer. This seems like very foundational mesa / mesa-geo stuff,
        # which should be handled by the GeoAgent or GeoBase, but the examples are 
        # inconsistent. For now, invert the affine transformation to get the indices,
        # converting from geographic (lat, lon) to raster (col, row) coordinates

        self.float_indices = ~self.model.space.raster_layer._transform * \
            (np.float64(geometry.x), np.float64(geometry.y))

        self.indices = (int(self.float_indices[0]), int(self.float_indices[1]))

        # TODO: Figure out how to set the life stage on init
        # Seems natural to set the life stage on init, but in 
        # see lines 181-190 in mesa_geo/geoagent.py, the agents are instantiated before the
        # GeoAgent gets the attributes within the geojson, so we need to call _update_life_stage
        # after init when the age is known to the agent

        # self._update_life_stage()

    def step(self):

        intersecting_cell_filter = self.model.space.raster_layer.iter_neighbors(
            self.indices,
            moore=False,
            include_center=True,
            radius=0
        )

        intersecting_cell = next(intersecting_cell_filter)
        if not intersecting_cell:
            raise ValueError('No intersecting cell found')

        if self.life_stage == 'seed':
            survival_rate = get_jotr_emergence_rate(
                intersecting_cell.aridity
            )
        else:
            survival_rate = get_jotr_survival_rate(
                self.life_stage,
                intersecting_cell.aridity,
                0  # Assume no nurse plants for now
            )

        print(f"Agent life stage {self.life_stage}, survival rate: {survival_rate}")

        # Check survival
        if random.random() < survival_rate:
            print('Survived!')
            self.age += 1
        else:
            print('Died!')
            if self.life_stage in ['juvenile', 'adult', 'breeding']:
                self.life_stage = 'dead'  # Keep as a potential nurse plant
            else:
                self.remove()  # If seed or seedling, remove from model

        # Increment age
        self.age += 1
        self._update_life_stage()

        # Disperse
        if self.life_stage == 'breeding':
            self.disperse_seeds()

    def _update_life_stage(self):
        age = self.age if self.age else 0
        if age == 0:
            life_stage = 'seed'
        elif age > 1 and age <= JOTR_JUVENILE_AGE:
            life_stage = 'seedling'
        elif age >= JOTR_JUVENILE_AGE and age <= JOTR_ADULT_AGE:
            life_stage = 'juvenile'
        elif age > JOTR_ADULT_AGE and age < JOTR_REPRODUCTIVE_AGE:
            life_stage = 'adult'
        else:
            life_stage = 'breeding'
        self.life_stage = life_stage

    def disperse_seeds(self, dispersal_distance=JOTR_SEED_DISPERSAL_DISTANCE):
        pass

class Vegetation(mesa.Model):
    def __init__(self, bounds, export_data=False, num_steps=20, epsg=4326):
        super().__init__()
        self.bounds = bounds
        self.export_data = export_data
        self.num_steps = num_steps

        self.space = StudyArea(bounds, epsg=epsg, model=self)

        self.space.get_elevation()
        self.space.get_aridity()

        with open(INITIAL_AGENTS_PATH, 'r') as f:
            initial_agents_geojson = json.loads(f.read())

        agents = mg.AgentCreator(
            JoshuaTreeAgent,
            model=self
        ).from_GeoJSON(initial_agents_geojson)

        # TODO: Since .from_GeoJSON() sets attributes after init, we need to call
        # _update_life_stage after init, but before we add to the grid
        self.agents.select(agent_type=JoshuaTreeAgent).do('_update_life_stage')

        self.space.add_agents(agents)

        self.datacollector = mesa.DataCollector(
            {
                "Mean Age": self.mean_age,
                "N Agents": self.n_agents,
                "N Seeds": self.n_seeds,
                "N Seedlings": self.n_seedlings,
                "N Juveniles": self.n_juveniles,
                "N Adults": self.n_adults,
                "N Breeding": self.n_breeding
            }
        )

    @property
    def mean_age(self):
        return self.agents.select(agent_type=JoshuaTreeAgent) \
            .agg('age', np.mean)

    @property
    def n_agents(self):
        return len(self.agents.select(agent_type=JoshuaTreeAgent))

    @property
    def n_seeds(self):
        count_dict = self.agents.select(agent_type=JoshuaTreeAgent) \
            .groupby('life_stage').count()
        return count_dict['seed'] if 'seed' in count_dict else 0

    @property
    def n_seedlings(self):
        count_dict = self.agents.select(agent_type=JoshuaTreeAgent) \
            .groupby('life_stage').count()
        return count_dict['seedling'] if 'seedling' in count_dict else 0

    @property
    def n_juveniles(self):
        count_dict = self.agents.select(agent_type=JoshuaTreeAgent) \
            .groupby('life_stage').count()
        return count_dict['juvenile'] if 'juvenile' in count_dict else 0

    @property
    def n_adults(self):
        count_dict = self.agents.select(agent_type=JoshuaTreeAgent) \
            .groupby('life_stage').count()
        return count_dict['adult'] if 'adult' in count_dict else 0

    @property
    def n_breeding(self):
        count_dict = self.agents.select(agent_type=JoshuaTreeAgent) \
            .groupby('life_stage').count()
        return count_dict['breeding'] if 'breeding' in count_dict else 0

    def step(self):
        self.agents.shuffle_do("step")
