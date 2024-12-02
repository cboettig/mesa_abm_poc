JOTR_JUVENILE_AGE = 8
JOTR_ADULT_AGE = 15
JOTR_REPRODUCTIVE_AGE = 30
JOTR_SEED_DISPERSAL_DISTANCE = 30


def get_jotr_emergence_rate(aridity):
    rate = 0.3 - (aridity / 1000)
    return rate


def get_jotr_survival_rate(life_stage, aridity, nurse_indicator):
    if life_stage == 'seedling':
        rate = 0.4
    if life_stage == 'juvenile':
        rate = 0.8
    if life_stage == 'adult':
        rate = 0.7

    rate = rate - (aridity / 1000)
    if nurse_indicator:
        rate = rate + 0.2

    return rate