N_SIMULATIONS_PER_EXPERIMENT = 10

EXPERIMENT_PARAMS = {
    "num_vars": 6,
    "names": [
        "random-seed",
        "grass-regrowth-time",
        "sheep-gain-from-food",
        "wolf-gain-from-food",
        "sheep-reproduce",
        "wolf-reproduce",
    ],
    "bounds": [
        [1, 100000],
        [20.0, 40.0],
        [2.0, 8.0],
        [16.0, 32.0],
        [2.0, 8.0],
        [2.0, 8.0],
    ],
}
