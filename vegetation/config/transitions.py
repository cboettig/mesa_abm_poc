JOTR_JUVENILE_AGE = 8
JOTR_ADULT_AGE = 15
JOTR_REPRODUCTIVE_AGE = 30
JOTR_SEED_DISPERSAL_DISTANCE = 30

# TODO: Refactor to be more like a config
# This is a temporary solution to get the transition rates to be
# valid for the JOTR model, but this doesn't scale well - we need this
# to probably be more abstract and use a config for at least our initial


def get_jotr_emergence_rate(aridity):
    rate = 0.8 - (aridity / 10000)
    return rate


def get_jotr_survival_rate(life_stage, aridity, nurse_indicator):
    if life_stage == "seedling":
        rate = 0.55
    if life_stage == "juvenile":
        rate = 0.8
    if life_stage == "adult":
        rate = 0.7
    if life_stage == "breeding":
        rate = 0.65

    rate = rate - (aridity / 10000)
    if nurse_indicator:
        rate = rate + 0.2

    return rate
