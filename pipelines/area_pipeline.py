from arguments import args

from SUMO.sumo import generateSUMO3DNet, generateRandomRoutes, runSimulation

from virtual_data.simulation_results import printSimulationStats
from virtual_data.dataset_generation import generateVirtualDataset

def runAreaPipeline():
    # Generate SUMO 3D Net using area's bounding box
    if args.generate_net and args.generate_ruotes:
        minGPSPoint, maxGPSPoint = args.scenario_bounding_box
        generateSUMO3DNet(minGPSPoint, maxGPSPoint)

    # Generate random SUMO routes if requested
    if args.generate_ruotes:
        generateRandomRoutes(
            args.trajectories_number, args.custom_vehicle, args.random_veh_types, args.depart_delay
        )

    # Run SUMO simulation
    _, SUMOSimStats = runSimulation()

    # Log simulation stats
    printSimulationStats(SUMOSimStats)

    # Generate virtual dataset using simulation results
    generateVirtualDataset(
        args.scenario_name,
        keepEnergySteps=args.keep_energy_steps
    )
