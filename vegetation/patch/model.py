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
    def __init__(self, model, geometry, crs, age=0):
        super().__init__(
            model=model,
            geometry=geometry,
            crs=crs,
        )

        # TODO: Shouldn't GeoAgent have some more native pos abstraction? I am
        # passing geometry after all...
        pos = (int(geometry.x), int(geometry.y))
        self._pos = pos
        self.age = age

        if age == 0:
            self.life_stage = 'seed'
        elif age > 1 and age <= JOTR_JUVENILE_AGE:
            self.life_stage = 'seedling'
        elif age >= JOTR_JUVENILE_AGE and age <= JOTR_ADULT_AGE:
            self.life_stage = 'juvenile'
        elif age > JOTR_ADULT_AGE and age < JOTR_REPRODUCTIVE_AGE:
            self.life_stage = 'adult'
        else:
            self.life_stage = 'breeding'

    @property
    def pos(self):
        return self._pos

    @property
    def indices(self):
        return self._indices

    @pos.setter
    def pos(self, pos):
        self._pos = pos
        if pos is not None:
            x, y = self.pos
            row_idx = self.model.space.raster_layer.height - y - 1
            col_idx = x
            self._indices = row_idx, col_idx
            self.geometry = Point(
                self.model.space.raster_layer.transform * self.indices
            )
        else:
            self.geometry = None

    def step(self):
        survival_rate = get_jotr_survival_rate(
            self.life_stage,
            self.model.space.raster_layer.get_raster("aridity")[self.indices],
            0  # Assume no nurse plants for now
        )

        # Check survival
        if random.random() < survival_rate:
            self.age += 1
        else:
            if self.life_stage in ['juvenile', 'adult', 'breeding']:
                self.life_stage = 'dead' # Keep as a potential nurse plant
            else:
                self.remove()  # If seed or seedling, remove from model entirely

        # Increment age
        self.age += 1

        # Disperse
        if self.life_stage == 'breeding':
            self.disperse_seeds()

    def disperse_seeds(self, dispersal_distance = JOTR_SEED_DISPERSAL_DISTANCE):
        pass

class Vegetation(mesa.Model):
    def __init__(self, bounds, export_data=False, num_steps=20, epsg=4326):
        super().__init__()
        self.bounds = bounds
        self.export_data = export_data
        self.num_steps = num_steps

        self.schedule = mesa.time.RandomActivationByType(self)
        self.space = StudyArea(bounds, epsg=epsg, model=self)

        with open(INITIAL_AGENTS_PATH, 'r') as f:
            initial_agents_geojson = json.loads(f.read())

        agents = mg.AgentCreator(
            JoshuaTreeAgent,
            model=self
        ).from_GeoJSON(initial_agents_geojson)
        self.space.add_agents(agents)

        for agent in agents:
            self.schedule.add(agent)

        self.datacollector = mesa.DataCollector(
            {
                "Mean Age": "mean_age",
                "N Agents": "n_agents", 
                "N Seeds": "n_seeds",
                "N Seedlings": "n_seedlings",
                "N Juveniles": "n_juveniles",
                "N Adults": "n_adults",
                "N Breeding": "n_breeding"
            }
        )

        self.space.get_elevation()
        self.space.get_aridity()

    @property
    def mean_age(self):
        return np.mean([agent.age for agent in self.agents])

    @property
    def n_agents(self):
        return len(self.agents)

    @property
    def n_seeds(self):
        return len([agent for agent in self.agents if agent.life_stage == 'seed'])

    @property
    def n_seedlings(self):
        return len([agent for agent in self.agents if agent.life_stage == 'seedling'])

    @property
    def n_juveniles(self):
        return len([agent for agent in self.agents if agent.life_stage == 'juvenile'])

    @property
    def n_adults(self):
        return len([agent for agent in self.agents if agent.life_stage == 'adult'])

    @property
    def n_breeding(self):
        return len([agent for agent in self.agents if agent.life_stage == 'breeding'])

    def step(self):
        self.schedule.step()