from enum import IntEnum


class LifeStage(IntEnum):
    DEAD = 0
    SEED = 1
    SEEDLING = 2
    JUVENILE = 3
    ADULT = 4
    BREEDING = 5


LIFE_STAGE_RGB_VIZ_MAP = {
    LifeStage.DEAD: (100, 0, 0, 1),
    LifeStage.BREEDING: (0, 255, 0, 1),
    LifeStage.ADULT: (0, 200, 0, 1),
    LifeStage.JUVENILE: (0, 150, 0, 1),
    LifeStage.SEEDLING: (0, 100, 0, 1),
    LifeStage.SEED: (0, 50, 0, 1),
}
