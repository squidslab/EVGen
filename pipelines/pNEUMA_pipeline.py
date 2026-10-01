from arguments import args
from paths import PNEUMA

from data.utils import getTrajectoriesBounds, getTrajectoryBatch, buildTrajectoryDataframe
from data.trajectory_parser.pNEUMA_parser import pNEUMAParser

from SUMO.sumo_vehicles import mapSUMOVehicleTypes
from SUMO.sumo import generateSUMO3DNet, generateRoutes, runSimulation

from virtual_data.simulation_results import printSimulationStats
from virtual_data.dataset_generation import generateVirtualDataset

def runPNEUMAPipeline():
    # Initialize pNEUMA parser
    parser = pNEUMAParser()

    # Retrieve data about trajectories from pNEUMA
    pNEUMATrajectories = parser.parse(PNEUMA)

    # Generate SUMO 3D Net using dataset bounds obtained via trajectories data if requested
    if args.generate_net and args.generate_ruotes:
        minGPSPoint, maxGPSPoint = getTrajectoriesBounds(pNEUMATrajectories)
        generateSUMO3DNet(minGPSPoint, maxGPSPoint)

    # Retrieve trajectory batch to process (15,000 trajectories per batch)
    trajectoryBatch = getTrajectoryBatch(
        pNEUMATrajectories, args.trajectory_batch
    )

    # Build trajectory as dataframe so it is suitable for SUMO routes generation
    SUMOtrajectories = buildTrajectoryDataframe(trajectoryBatch, True)

    # Generate SUMO routes using trajectories data if requested
    if args.generate_ruotes:
        # Retrieve trajectory ids for each trajectory
        trajectoryIds = SUMOtrajectories["trajectoryId"].unique().tolist()

        # Retrieve SUMO vehicle types map
        SUMOvehicleTypes = mapSUMOVehicleTypes(
            trajectoryIds, customType=args.custom_vehicle, randomize=args.random_veh_types
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
