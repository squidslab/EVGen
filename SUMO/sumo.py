import os
import shutil
import pandas as pd
import subprocess
import sys

from arguments import args
from external_requests import downloadElevation

from pathlib import Path
from custom_types import GPSPoint, CustomVehicle, SUMOTrip, SUMOVehicleExtraData

from SUMO.sumo_paths import configPath, customPath
from SUMO.sumo_network import loadSUMONetwork
from SUMO.sumo_xml import setupSUMOConfig, setupDuarouterConfig, setupVehicleTypes, generateSUMOTrips, addExtraToSUMOVehicles, finalizeRandomSUMOVehicles, readSUMOBatteryOut, getSUMOSimulationStats

# Generates a 3D SUMO net using osmGet, osmBuild and netconvert based on the bounding box specified by given GPSPoints
def generateSUMO3DNet(minGPSPoint: GPSPoint, maxGPSPoint: GPSPoint):
    scenarioName = args.scenario_name

    # Set SUMO_HOME path
    sumoHomePath = os.getenv("SUMO_HOME_PATH")

    if not sumoHomePath:
        raise RuntimeError("SUMO_HOME_PATH is not set in the environment")

    sumoHome = Path(sumoHomePath)

    # Scenario directory path
    scenarioPath = configPath / scenarioName

    # Remove scenario-specific config directory if it exists
    if scenarioPath.exists():
        shutil.rmtree(scenarioPath)

    # Create scenario-specific config directory
    scenarioPath.mkdir(parents=True)

    # Config files paths
    elevationFile = scenarioPath / f"{scenarioName}_elevation.tif"
    osmFile = scenarioPath / f"{scenarioName}_bbox.osm.xml"
    sumoNetFile = scenarioPath / f"{scenarioName}.net.xml"
    sumo3DNetFile = scenarioPath / f"{scenarioName}_3D.net.xml"

    try:
        # 1. Download elevation data
        downloadElevation(minGPSPoint, maxGPSPoint, elevationFile)

        if not elevationFile.exists():
            raise RuntimeError("Elevation file was not generated")

        # 2. Download OSM data
        subprocess.run(
            [
                sys.executable,
                str(sumoHome / "tools" / "osmGet.py"),
                (
                    f"--bbox="
                    f"{minGPSPoint.longitude},"
                    f"{minGPSPoint.latitude},"
                    f"{maxGPSPoint.longitude},"
                    f"{maxGPSPoint.latitude}"
                ),
                "--prefix",
                scenarioName
            ],
            cwd=scenarioPath,
            check=True
        )

        if not osmFile.exists():
            raise RuntimeError("OSM file was not generated")

        # 3. Build SUMO network from OSM
        subprocess.run(
            [
                sys.executable,
                str(sumoHome / "tools" / "osmBuild.py"),
                "--osm-file",
                osmFile.name,
                "--prefix",
                scenarioName
            ],
            cwd=scenarioPath,
            check=True
        )

        if not sumoNetFile.exists():
            raise RuntimeError("SUMO network was not generated")

        # Prepare environment for netconvert
        env = os.environ.copy()
        env["PATH"] = str(sumoHome / "bin") + os.pathsep + env["PATH"]

        # 4. Add elevation data to SUMO network
        subprocess.run(
            [
                str(sumoHome / "bin" / "netconvert.exe"),
                "--sumo-net-file",
                sumoNetFile.name,
                "--heightmap.geotiff",
                elevationFile.name,
                "--output-file",
                sumo3DNetFile.name
            ],
            cwd=scenarioPath,
            env=env,
            check=True
        )

        if not sumo3DNetFile.exists():
            raise RuntimeError("3D SUMO network was not generated")

        # Log successful 3D net generation
        print(f"SUMO 3D network generated: {sumo3DNetFile.name}")

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"SUMO command failed with exit code {error.returncode}"
        ) from error

# Generate SUMO routes using duarouter based on given trajectories
def generateRoutes(trajectories: pd.DataFrame, SUMOvehicleTypes: dict[float, str], departDelay: float = 0):
    sumoTrips: list[SUMOTrip] = []
    vehiclesExtra: dict[str, SUMOVehicleExtraData] = {}

    # Configure duarouter config file and vehicle types additional file if not in validation mode
    if not args.validation:
        setupDuarouterConfig()
        setupVehicleTypes()

    # Set current depart
    currentDepart: float = 0.00

    # Iterate over trajectories and for each generate SUMO trip data and SUMO vehicle extra data
    for trajectory in trajectories.to_dict(orient="records"):
        sumoVehicleId = trajectory["trajectoryId"]

        startpoint: GPSPoint = trajectory['startpoint']
        endpoint: GPSPoint = trajectory['endpoint']
        waypoints: list[GPSPoint] = trajectory["waypoints"]

        sumoTrips.append(SUMOTrip(
            id=sumoVehicleId,
            type=(SUMOvehicleTypes.get(sumoVehicleId, "ev_generic")),

            depart=currentDepart,

            fromLonLat=f"{startpoint.longitude},{startpoint.latitude}",
            toLonLat=f"{endpoint.longitude},{endpoint.latitude}",
            viaLonLat=" ".join(
                f"{waypoint.longitude},{waypoint.latitude}"
                for waypoint in waypoints
            ),

            startSpeed=trajectory["startSpeed"],
            endSpeed=trajectory["endSpeed"],
        ))

        currentDepart += departDelay

        vehiclesExtra[sumoVehicleId] = SUMOVehicleExtraData(
            startpoint=trajectory["startpoint"],
            endpoint=trajectory["endpoint"],
            stops=trajectory["stops"]
        )

    # Load correct SUMO Network
    loadSUMONetwork()

    # Generate custom.trips.xml containing SUMO trips
    generateSUMOTrips(sumoTrips)

    # Run duarouter to generate custom.rou.xml
    try:
        subprocess.run(
            [
                "duarouter",
                "--configuration-file",
                "custom.duarcfg",
                "--ignore-errors"
            ],
            cwd=customPath,
            check=True
        )
    except subprocess.CalledProcessError as duarError:
        print("DUAROUTER failed:", duarError)

    # Add some additional properties to SUMO vehicles into custom.rou.xml
    addExtraToSUMOVehicles(vehiclesExtra)

    # Log successful route generation
    print("SUMO routes generated")

# Generate random SUMO routes using randomTrips based on given number of trajectories
def generateRandomRoutes(numberofTrajectories: int = 5000, customVehicle: CustomVehicle | None = None, randomizeVehTypes: bool = False, departDelay: float = 0):
    scenarioName = args.scenario_name

    # Set SUMO_HOME path
    sumoHomePath = os.getenv("SUMO_HOME_PATH")

    if not sumoHomePath:
        raise RuntimeError("SUMO_HOME_PATH is not set in the environment")

    sumoHome = Path(sumoHomePath)

    # Configure vehicle types additional file if not in validation mode
    if not args.validation:
        setupVehicleTypes()

    # Config files paths
    scenarioPath = configPath / scenarioName
    sumo3DNetFile = scenarioPath / f"{scenarioName}_3D.net.xml"

    # Custom files paths
    scenarioCustomPath = customPath / scenarioName
    customRoutesFile = scenarioCustomPath / "custom.rou.xml"

    # Remove scenario-specific custom directory if it exists
    if scenarioCustomPath.exists():
        shutil.rmtree(scenarioCustomPath)

    # Create scenario-specific custom directory
    scenarioCustomPath.mkdir(parents=True)

    # Run randomTrips to randomly generate custom.rou.xml and produce requested number of trajectories
    try:
        subprocess.run(
            [
                sys.executable,
                str(sumoHome / "tools" / "randomTrips.py"),
                "-n", str(sumo3DNetFile),
                "-r", str(customRoutesFile),
                "--seed", "42",
                "--min-distance", "500",
                "--begin", "0",
                "--period", "1",
                "--end", str(numberofTrajectories),
            ],
            cwd=customPath,
            check=True
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"randomTrips.py failed with exit code {error.returncode}"
        ) from error

    # Add missing depart times and vehicle types to randomly generated SUMO vehicles into custom.rou.xml
    finalizeRandomSUMOVehicles(customVehicle, randomizeVehTypes, departDelay)

    # Log successful route generation
    print("Random SUMO routes generated")

# Run SUMO simulation
def runSimulation():
    # Configure SUMO config file based on validation or scenario mode
    if args.validation:
        configFileName = "osm.sumocfg"
    else:
        configFileName = "scenario.sumocfg"
        setupSUMOConfig()

    # Run SUMO
    try:
        subprocess.run(
            [
                "sumo",
                "-c",
                configFileName
            ],
            cwd=configPath,
            check=True
        )
    except subprocess.CalledProcessError as sumoError:
        print("SUMO failed:", sumoError)

    # Return battery data output by reading tripinfos.xml and other statistics about simulation
    return readSUMOBatteryOut(), getSUMOSimulationStats()
