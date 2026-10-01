from arguments import args
from paths import EVED, EVED_STATIC


from data.utils import getTrajectoriesBounds, getTrajectoryBatch, buildTrajectoryDataframe
from data.trajectory_parser.eVED_parser import EVEDParser

from SUMO.sumo_vehicles import mapSUMOVehicleTypes
from SUMO.sumo import generateSUMO3DNet, generateRoutes, runSimulation

from virtual_data.simulation_results import printSimulationStats
from virtual_data.dataset_generation import generateVirtualDataset

def runEVEDPipeline():
    # Initialize eVED parser
    parser = EVEDParser(
        staticPath=EVED_STATIC,
        vehicleTypes=args.eved_veh_types
    )

    # Retrieve data about trajectories from eVED
    eVEDTrajectories = parser.parse(EVED)

    # Generate SUMO 3D Net using dataset bounds obtained via trajectories data if requested
    if args.generate_net and args.generate_ruotes:
        minGPSPoint, maxGPSPoint = getTrajectoriesBounds(eVEDTrajectories)
        generateSUMO3DNet(minGPSPoint, maxGPSPoint)

    # Retrieve trajectory batch to process (15,000 trajectories per batch)
    trajectoryBatch = getTrajectoryBatch(
        eVEDTrajectories, args.trajectory_batch
    )

    # Build trajectories as dataframe so it is suitable for SUMO routes generation
    SUMOtrajectories = buildTrajectoryDataframe(trajectoryBatch, True)

    # Generate SUMO routes using trajectories data if requested
    if args.generate_ruotes:
        EVTrajectoryIds = []
        otherTrajectoryIds = []

        # Retrieve trajectory ids for both EV and ICE/HEV/PHEV trajectories
        for trajectoryId in SUMOtrajectories["trajectoryId"].unique():
            vehId = float(trajectoryId.split("_")[0])

            # 10, 541, 455: eVED EV veh ids
            if vehId in [10, 541, 455]:
                EVTrajectoryIds.append(trajectoryId)
            else:
                otherTrajectoryIds.append(trajectoryId)

        # Retrieve SUMO vehicle types map
        SUMOvehicleTypes = mapSUMOVehicleTypes(
            otherTrajectoryIds, EVTrajectoryIds, args.custom_vehicle, args.random_veh_types
        )

        # Generate SUMO routes
        generateRoutes(
            SUMOtrajectories, SUMOvehicleTypes, args.depart_delay
        )

    # Run SUMO simulation
    _, SUMOSimStats = runSimulation()

    # Log simulation stats
    printSimulationStats(SUMOSimStats)

    # Generate virtual dataset using simulation results
    generateVirtualDataset(
        args.scenario_name,
        SUMOtrajectories,
        args.keep_energy_steps
    )
