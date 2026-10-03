import re

from dataclasses import asdict
from custom_types import SUMOSimStats

# Prints simulation statistics
def printSimulationStats(SUMOSimStats: SUMOSimStats):
    print("\nSimulation statistics")
    print("---------------------")

    for name, value in asdict(SUMOSimStats).items():
        statName = re.sub(r"(?<!^)(?=[A-Z])", " ", name).title()
        print(f"{statName:<25} {value}")

    print()

# Prints validation error metrics
def printValidationErrors(MAE: float, RMSE: float, MAPE: float | None = None, SMAPE: float | None = None):
    print("\nValidation Error Metrics")
    print("------------------------")

    print("MAE:", MAE)

    print("RMSE:", RMSE)

    if MAPE is not None:
        print("MAPE:", MAPE, "%")

    if SMAPE is not None:
        print("SMAPE:", SMAPE, "%")
