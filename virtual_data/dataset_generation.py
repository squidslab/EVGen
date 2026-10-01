import re
import math
import json
import xml.etree.ElementTree as ET
import pandas as pd

from paths import OUTPUT, VIRTUAL_DATASETS
from datetime import datetime
from dataclasses import asdict

def generateVirtualDatasetId(source: str):
    # Get current date in YYYYMMDD format
    date = datetime.now().strftime("%Y%m%d")

    # Search for existing datasets generated today
    pattern = re.compile(rf"{date}_{source}_(\d{{3}})\.csv")

    simulationNumbers = []
    for dataset in VIRTUAL_DATASETS.glob(f"{date}_{source}_*.csv"):
        match = pattern.match(dataset.name)

        if match:
            simulationNumbers.append(int(match.group(1)))

    # Generate the next progressive number
    nextNumber = max(simulationNumbers, default=0) + 1

    return f"{date}_{source}_{nextNumber:03d}"

# Generates a virtual dataset using simulation results
def generateVirtualDataset(sourceScenario: str, trajectories: pd.DataFrame | None = None, keepEnergySteps: bool = False):
    if keepEnergySteps:
        virtualDataset = generateStepDataset(
            sourceScenario,
            trajectories
        )
    else:
        virtualDataset = generateTrajectoryDataset(
            sourceScenario,
            trajectories
        )

    # Save virtual dataset as CSV
    virtualDataset.to_csv(
        VIRTUAL_DATASETS / f"{generateVirtualDatasetId(sourceScenario)}.csv",
        index=False
    )

    return virtualDataset

# Generates a virtual dataset containing one record for each trajectory
def generateTrajectoryDataset(sourceScenario: str, trajectories: pd.DataFrame | None = None):
    # Parse SUMO tripinfos.xml at given path
    tripInfosFile = ET.parse(OUTPUT / sourceScenario / "tripinfos.xml")
    tripInfos = tripInfosFile.getroot()

    # Create trajectory metadata dictionary if original trajectories are available
    trajectoryMetadata = (
        {
            trajectory['trajectoryId']: trajectory
            for trajectory in trajectories.to_dict(orient="records")
        }
        if trajectories is not None
        else None
    )

    # Records to generate for virtual database
    virtualTrajectories = []

    # Extract data for each virtual trajectory
    for tripInfo in tripInfos.findall("tripinfo"):
        trajectoryId = tripInfo.get("id")

        # Retrieve original trajectory metadata if available
        trajectory = (
            trajectoryMetadata.get(trajectoryId)
            if trajectoryMetadata is not None
            else None
        )

        # Skip virtual trajectories for which the original trajectory metadata cannot be found
        if trajectories is not None and trajectory is None:
            continue

        # Retrieve trip info data
        vehicleType = tripInfo.get("vType")
        tripDuration = float(tripInfo.get("duration", 0.0))
        tripDistance = float(tripInfo.get("routeLength", 0.0))
        tripAvgSpeed = (
            math.ceil(tripDistance / tripDuration * 100) / 100
            if tripDuration > 0
            else 0.0
        )
        battery = tripInfo.find("battery")

        # Skip virtual trajectories without battery information
        if battery is None:
            continue

        # Create virtual trajectory record
        virtualTrajectory = {
            "trajectoryId": trajectoryId,
            "vehicleType": vehicleType,

            "tripDuration (s)": tripDuration,
            "tripDistance (m)": tripDistance,
            "tripAvgSpeed (m/s)": tripAvgSpeed,

            "batteryCapacity (Wh)": float(battery.get("actualBatteryCapacity", 0.0)),
            "totalEnergyConsumed (Wh)": float(battery.get("totalEnergyConsumed", 0.0)),
            "totalEnergyRegenerated (Wh)": float(battery.get("totalEnergyRegenerated", 0.0)),
        }

        # Add trajectory metadata when available
        if trajectory is not None:
            virtualTrajectory.update(
                {
                    "startpoint (lat, lon)": json.dumps(asdict(trajectory["startpoint"])),
                    "endpoint (lat, lon)": json.dumps(asdict(trajectory["endpoint"])),
                    "waypoints [(lat, lon)]": json.dumps([
                        asdict(waypoint)
                        for waypoint in trajectory["waypoints"]
                    ]),
                }
            )

        # Save generated virtual record
        virtualTrajectories.append(virtualTrajectory)

    # Create and return virtual dataset
    return pd.DataFrame(virtualTrajectories)

# Generates a virtual dataset containing one record for each simulation step of each trajectory
def generateStepDataset(sourceScenario: str, trajectories: pd.DataFrame | None = None):
    # Parse SUMO tripinfos.xml at given path
    tripInfosFile = ET.parse(OUTPUT / sourceScenario / "tripinfos.xml")
    tripInfos = tripInfosFile.getroot()

    # Parse SUMO battery.out.xml at given path
    batteryOutputFile = ET.parse(OUTPUT / sourceScenario / "battery.out.xml")
    batteryExport = batteryOutputFile.getroot()

    # Create tripinfo dictionary indexed by trajectory id
    tripInfosData = {
        tripInfo.get("id"): tripInfo
        for tripInfo in tripInfos.findall("tripinfo")
    }

    # Create trajectory metadata dictionary if original trajectories are available
    trajectoryMetadata = (
        {
            trajectory['trajectoryId']: trajectory
            for trajectory in trajectories.to_dict(orient="records")
        }
        if trajectories is not None
        else None
    )

    # Group simulation steps by trajectory id
    trajectorySteps = {}

    for timestep in batteryExport.findall("timestep"):
        timestamp = float(timestep.get("time", 0.0))

        for vehicle in timestep.findall("vehicle"):
            trajectoryId = vehicle.get("id")

            if trajectoryId not in trajectorySteps:
                trajectorySteps[trajectoryId] = []

            trajectorySteps[trajectoryId].append(
                (timestamp, vehicle)
            )

    # Records to generate for virtual dataset
    virtualSteps = []

    # Extract data for each virtual step
    for trajectoryId, steps in trajectorySteps.items():
        # Retrieve trip info for current virtual trajectory
        tripInfo = tripInfosData.get(trajectoryId)

        # Skip virtual steps without trip info
        if tripInfo is None:
            continue

        # Retrieve original trajectory metadata if available
        trajectory = (
            trajectoryMetadata.get(trajectoryId)
            if trajectoryMetadata is not None
            else None
        )

        # Skip virtual steps for which the original trajectory metadata cannot be found
        if trajectories is not None and trajectory is None:
            continue

        # Retrieve trip info data
        vehicleType = tripInfo.get("vType")
        tripDuration = float(tripInfo.get("duration", 0.0))
        tripDistance = float(tripInfo.get("routeLength", 0.0))
        tripAvgSpeed = (
            math.ceil(tripDistance / tripDuration * 100) / 100
            if tripDuration > 0
            else 0.0
        )

        # Sort virtual trajectory simulation steps by timestamp
        steps.sort(key=lambda step: step[0])

        # Generate one record for each simulation step of current virtual trajectory
        for timestamp, vehicle in steps:
            virtualStep = {
                "timestamp": timestamp,
                "trajectoryId": trajectoryId,
                "vehicleType": vehicleType,

                "speed (m/s)": float(vehicle.get("speed", 0.0)),
                "acceleration (m/s²)": float(vehicle.get("acceleration", 0.0)),

                "tripDuration (s)": tripDuration,
                "tripDistance (m)": tripDistance,
                "tripAvgSpeed (m/s)": tripAvgSpeed,

                "batteryCapacity (Wh)": float(vehicle.get("actualBatteryCapacity", 0.0)),
                "energyConsumed (Wh)": float(vehicle.get("energyConsumed", 0.0)),
                "totalEnergyConsumed (Wh)": float(vehicle.get("totalEnergyConsumed", 0.0)),
                "totalEnergyRegenerated (Wh)": float(vehicle.get("totalEnergyRegenerated", 0.0)),
            }

            # Add trajectory metadata when available
            if trajectory is not None:
                virtualStep.update(
                    {
                        "startpoint (lat, lon)": json.dumps(asdict(trajectory["startpoint"])),
                        "endpoint (lat, lon)": json.dumps(asdict(trajectory["endpoint"])),
                        "waypoints [(lat, lon)]": json.dumps([
                            asdict(waypoint)
                            for waypoint in trajectory["waypoints"]
                        ]),
                    }
                )

            # Save generated virtual record
            virtualSteps.append(virtualStep)

    # Create and return virtual dataset
    return pd.DataFrame(virtualSteps)
