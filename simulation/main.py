import os
import pandas as pd
import dotenv
import pyNetLogo
from SALib.sample import saltelli
from datetime import datetime
from config import N_SIMULATIONS_PER_EXPERIMENT, EXPERIMENT_PARAMS

# Global variables
NETLOGO_HOME = os.getenv("NETLOGO_HOME")
NETLOGO_VERSION = os.getenv("NETLOGO_VERSION")
NETLOGO_WOLF_SHEEP_PATH = NETLOGO_HOME + "/app/models/Sample Models/Biology/Wolf Sheep Predation.nlogo"

# Dotenv variables
dotenv.load_dotenv()
RESULTS_CSV_NAME = os.getenv("VERY_SPECIAL_NAME_FOR_MY_RESULTS_CSV")


def run_simulation(netlogo_link, experiment):
    """run a netlogo model

    Parameters
    ----------
    experiments : dict

    """

    # Set the input parameters
    for key, value in experiment.items():
        if key == "random-seed":
            # The NetLogo random seed requires a different syntax
            netlogo_link.command(f"random-seed {value}")
        else:
            # Otherwise, assume the input parameters are global variables
            netlogo_link.command(f"set {key} {value}")

    netlogo_link.command("setup")

    # Run for 100 ticks and return the number of sheep and
    # wolf agents at each time step
    counts = netlogo_link.repeat_report(["count sheep", "count wolves"], 100)

    results = {
        "avg_sheep": counts["count sheep"].values.mean(),
        "avg_wolves": counts["count wolves"].values.mean(),
        "sd_sheep": counts["count sheep"].values.std(),
        "sd_wolves": counts["count wolves"].values.std()
    }

    return results


if __name__ == "__main__":
    netlogo_link = pyNetLogo.NetLogoLink(
        gui=False,
        netlogo_home=NETLOGO_HOME,
        netlogo_version=NETLOGO_VERSION
    )

    netlogo_link.load_model(NETLOGO_WOLF_SHEEP_PATH)

    param_values = saltelli.sample(
        problem=EXPERIMENT_PARAMS,
        N=N_SIMULATIONS_PER_EXPERIMENT,
        calc_second_order=True
    )

    experiments = pd.DataFrame(param_values, columns=EXPERIMENT_PARAMS["names"])

    results = []
    time_elapsed = datetime.now()
    n_experiments_completed = 0

    for experiment in experiments.to_dict("records"):

        print(f"""
            ---
            Running experiment {n_experiments_completed} (time elapsed: {datetime.now() - time_elapsed}):
              - random seed {experiment['random-seed']}
              - grass-regrowth-time {experiment['grass-regrowth-time']}
              - sheep-gain-from-food {experiment['sheep-gain-from-food']}
              - sheep-reproduce {experiment['sheep-reproduce']}
              - wolf-gain-from-food {experiment['wolf-gain-from-food']}
              - wolf-reproduce {experiment['wolf-reproduce']}
            ---
        """)

        result = run_simulation(netlogo_link, experiment)

        experiment.update(result)
        results.append(experiment)
        n_experiments_completed += 1

    results = pd.DataFrame(results)
    results.to_csv(f"{RESULTS_CSV_NAME}.csv")
