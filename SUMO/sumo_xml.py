import shutil
import math
import xml.etree.ElementTree as ET

from arguments import args
from custom_types import CustomVehicle, SUMOTrip, SUMOVehicleExtraData, SUMOBatteryData, SUMOSimStats

from SUMO.sumo_paths import configPath, customPath, outputPath
from SUMO.sumo_network import getLanePositionOnEdge, getLanePositionFromEdgeList

# Sets up SUMO config file based on the specified scenario
def setupSUMOConfig():
    scenario = args.scenario
    scenarioName = args.scenario_name

    sumoConfigFilePath = configPath / "scenario.sumocfg"
    scenarioOutputPath = outputPath / scenarioName

    # Remove scenario-specific output directory if it exists
    if scenarioOutputPath.exists():
        shutil.rmtree(scenarioOutputPath)

    # Create scenario-specific output directory
    scenarioOutputPath.mkdir(parents=True)

    # Configure simulation end time based on current scenario
    if scenario == "dataset":
        endValue = 50000
    else:
        endValue = 50000
        trajectoryCount = 5000

        while trajectoryCount < args.trajectories_number:
            endValue += 50000
            trajectoryCount += 5000

    # Create SUMO configuration
    sumoConfiguration = ET.Element("sumoConfiguration")

    inputConfig = ET.SubElement(sumoConfiguration, "input")

    ET.SubElement(
        inputConfig,
        "net-file",
        {"value": f"./{scenarioName}/{scenarioName}_3D.net.xml"}
    )

    ET.SubElement(
        inputConfig,
        "route-files",
        {"value": f"../custom/{scenarioName}/custom.rou.xml"}
    )

    ET.SubElement(
        inputConfig,
        "additional-files",
        {"value": "../custom/vehicle_types.add.xml"}
    )

    outputConfig = ET.SubElement(sumoConfiguration, "output")

    ET.SubElement(
        outputConfig,
        "tripinfo-output",
        {"value": f"../output/{scenarioName}/tripinfos.xml"}
    )

    timeConfig = ET.SubElement(sumoConfiguration, "time")

    ET.SubElement(
        timeConfig,
        "step-length",
        {"value": "1.0"}
    )

    ET.SubElement(
        timeConfig,
        "end",
        {"value": f"{endValue:.2f}"}
    )

    processingConfig = ET.SubElement(
        sumoConfiguration,
        "processing"
    )

    ET.SubElement(
        processingConfig,
        "seed",
        {"value": "42"}
    )

    ET.SubElement(
        processingConfig,
        "threads",
        {"value": "1"}
    )

    ET.SubElement(
        processingConfig,
        "ignore-route-errors",
        {"value": "true"}
    )

    ET.SubElement(
        processingConfig,
        "tls.actuated.jam-threshold",
        {"value": "30"}
    )

    ET.SubElement(
        processingConfig,
        "collision.action",
        {"value": "none"}
    )

    routingConfig = ET.SubElement(
        sumoConfiguration,
        "routing"
    )

    ET.SubElement(
        routingConfig,
        "device.rerouting.adaptation-steps",
        {"value": "18"}
    )

    ET.SubElement(
        routingConfig,
        "device.rerouting.adaptation-interval",
        {"value": "10"}
    )

    reportConfig = ET.SubElement(
        sumoConfiguration,
        "report"
    )

    ET.SubElement(
        reportConfig,
        "verbose",
        {"value": "true"}
    )

    ET.SubElement(
        reportConfig,
        "duration-log.statistics",
        {"value": "true"}
    )

    ET.SubElement(
        reportConfig,
        "no-step-log",
        {"value": "true"}
    )

    # Save SUMO configuration
    sumoConfigFile = ET.ElementTree(sumoConfiguration)
    ET.indent(sumoConfigFile, space="    ")

    sumoConfigFile.write(
        sumoConfigFilePath,
        encoding="UTF-8",
        xml_declaration=True
    )

# Sets up duarouter config file based on specified scenario
def setupDuarouterConfig():
    scenarioName = args.scenario_name

    duarouterConfigFilePath = customPath / "custom.duarcfg"
    scenarioCustomPath = customPath / scenarioName

    # Remove scenario-specific custom directory if it exists
    if scenarioCustomPath.exists():
        shutil.rmtree(scenarioCustomPath)

    # Create scenario-specific custom directory
    scenarioCustomPath.mkdir(parents=True)

    # Create duarouter configuration
    duarouterConfiguration = ET.Element("duarouterConfiguration")

    inputConfig = ET.SubElement(duarouterConfiguration, "input")

    ET.SubElement(
        inputConfig,
        "net-file",
        {"value": f"../config/{scenarioName}/{scenarioName}_3D.net.xml"}
    )

    ET.SubElement(
        inputConfig,
        "route-files",
        {"value": "./custom.trips.xml"}
    )

    outputConfig = ET.SubElement(duarouterConfiguration, "output")

    ET.SubElement(
        outputConfig,
        "output-file",
        {"value": f"./{scenarioName}/custom.rou.xml"}
    )

    processingConfig = ET.SubElement(
        duarouterConfiguration,
        "processing"
    )

    ET.SubElement(
        processingConfig,
        "seed",
        {"value": "42"}
    )

    # Save duarouter configuration
    duarouterConfigFile = ET.ElementTree(duarouterConfiguration)
    ET.indent(duarouterConfigFile, space="    ")

    duarouterConfigFile.write(
        duarouterConfigFilePath,
        encoding="UTF-8",
        xml_declaration=True
    )

# Sets up vehicle types additional file if it does not exist
def setupVehicleTypes():
    vehicleTypesFilePath = customPath / "vehicle_types.add.xml"

    if vehicleTypesFilePath.exists():
        return

    # Create vehicle types configuration
    additional = ET.Element("additional")

    # Generic EV type
    evGeneric = ET.SubElement(
        additional,
        "vType",
        {
            "id": "ev_generic",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "mass": "1800",
            "accel": "2.5",
            "decel": "3.0",
            "maxSpeed": "44.44",
            "sigma": "1"
        }
    )

    ET.SubElement(
        evGeneric,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        evGeneric,
        "param",
        {"key": "device.battery.capacity", "value": "60000"}
    )

    # Custom EV type (Configurable by user)
    customEv = ET.SubElement(
        additional,
        "vType",
        {
            "id": "custom_ev",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "mass": "1700.0",
            "accel": "3.0",
            "decel": "3.0",
            "maxSpeed": "52.78",
            "sigma": "1"
        }
    )

    ET.SubElement(
        customEv,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        customEv,
        "param",
        {"key": "device.battery.capacity", "value": "80000.0"}
    )

    # Predefined EV type: 2013 Nissan Leaf SV
    leaf2013 = ET.SubElement(
        additional,
        "vType",
        {
            "id": "leaf_2013",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "length": "4.445",
            "width": "1.770",
            "height": "1.550",
            "mass": "1493",
            "accel": "2.71",
            "decel": "3.0",
            "maxSpeed": "40.27",
            "sigma": "1"
        }
    )

    ET.SubElement(
        leaf2013,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        leaf2013,
        "param",
        {"key": "device.battery.capacity", "value": "21400"}
    )

    # Predefined EV type: Tesla Model Y Premium RWD (Juniper, LG 5L)
    teslaModelY = ET.SubElement(
        additional,
        "vType",
        {
            "id": "tesla_model_y",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "length": "4.790",
            "width": "1.982",
            "height": "1.624",
            "mass": "1976",
            "accel": "4.96",
            "decel": "3.0",
            "maxSpeed": "55.83",
            "sigma": "1"
        }
    )

    ET.SubElement(
        teslaModelY,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        teslaModelY,
        "param",
        {"key": "device.battery.capacity", "value": "75000"}
    )

    # Predefined EV type: Tesla Model 3 RWD
    teslaModel3 = ET.SubElement(
        additional,
        "vType",
        {
            "id": "tesla_model_3",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "length": "4.720",
            "width": "1.850",
            "height": "1.440",
            "mass": "1847",
            "accel": "4.48",
            "decel": "3.0",
            "maxSpeed": "55.83",
            "sigma": "1"
        }
    )

    ET.SubElement(
        teslaModel3,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        teslaModel3,
        "param",
        {"key": "device.battery.capacity", "value": "60000"}
    )

    # Predefined EV type: Chevrolet Equinox EV 2025 LT FWD
    chevroletEquinoxEV = ET.SubElement(
        additional,
        "vType",
        {
            "id": "chevrolet_equinox_ev",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "length": "4.867",
            "width": "1.954",
            "height": "1.646",
            "mass": "2233",
            "accel": "3.97",
            "decel": "3.0",
            "maxSpeed": "52.77",
            "sigma": "1"
        }
    )

    ET.SubElement(
        chevroletEquinoxEV,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        chevroletEquinoxEV,
        "param",
        {"key": "device.battery.capacity", "value": "85000"}
    )

    # Predefined EV type: Ford Mustang Mach-E 2025 Select RWD Standard Range
    fordMustangMachE = ET.SubElement(
        additional,
        "vType",
        {
            "id": "ford_mustang_mach_e",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "length": "4.713",
            "width": "1.881",
            "height": "1.624",
            "mass": "2175",
            "accel": "4.48",
            "decel": "3.0",
            "maxSpeed": "50.0",
            "sigma": "1"
        }
    )

    ET.SubElement(
        fordMustangMachE,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        fordMustangMachE,
        "param",
        {"key": "device.battery.capacity", "value": "72600"}
    )

    # Predefined EV type: Hyundai IONIQ 5 Standard 2WD / 63 kWh RWD
    hyundaiIoniq5 = ET.SubElement(
        additional,
        "vType",
        {
            "id": "hyundai_ioniq_5",
            "vClass": "passenger",
            "emissionClass": "Energy",
            "length": "4.655",
            "width": "1.890",
            "height": "1.605",
            "mass": "1955",
            "accel": "3.27",
            "decel": "3.0",
            "maxSpeed": "51.38",
            "sigma": "1"
        }
    )

    ET.SubElement(
        hyundaiIoniq5,
        "param",
        {"key": "has.battery.device", "value": "true"}
    )

    ET.SubElement(
        hyundaiIoniq5,
        "param",
        {"key": "device.battery.capacity", "value": "63000"}
    )

    # Save vehicle types configuration
    vehicleTypesFile = ET.ElementTree(additional)
    ET.indent(vehicleTypesFile, space="    ")

    vehicleTypesFile.write(
        vehicleTypesFilePath,
        encoding="UTF-8",
        xml_declaration=True
    )

# Builds custom vehicle type as requested and saves it into vehicle_types.add.xml
def buildCustomVehType(customType: CustomVehicle):
    vehicleTypesAddFilePath = customPath / "vehicle_types.add.xml"

    # Default parameters values
    defaultParameters = {
        "mass": 1800,      # kg
        "accel": 2.5,      # m/s^2
        "decel": 3.0,      # m/s^2
        "maxSpeed": 44.44,  # m/s
        "sigma": 1,
        "battery": 60000   # Wh
    }

    # Use custom values when specified, otherwise use defaults
    mass = (
        customType.mass
        if customType.mass is not None
        else defaultParameters["mass"]
    )

    accel = (
        customType.accel
        if customType.accel is not None
        else defaultParameters["accel"]
    )

    maxSpeed = (
        round(customType.maxSpeed / 3.6, 2)
        if customType.maxSpeed is not None
        else defaultParameters["maxSpeed"]
    )

    battery = (
        customType.battery * 1000
        if customType.battery is not None
        else defaultParameters["battery"]
    )

    # Parse vehicle types additional file
    vehicleTypesAddFile = ET.parse(vehicleTypesAddFilePath)
    additional = vehicleTypesAddFile.getroot()

    # Find existing custom vehicle type
    customVehType = additional.find("./vType[@id='custom_ev']")

    if customVehType is None:
        customVehType = ET.SubElement(
            additional,
            "vType",
            {
                "id": "custom_ev",
                "vClass": "passenger",
                "emissionClass": "Energy"
            }
        )

    # Set/update vehicle parameters
    customVehType.set("mass", str(mass))
    customVehType.set("accel", str(accel))
    customVehType.set("decel", str(defaultParameters["decel"]))
    customVehType.set("maxSpeed", str(maxSpeed))
    customVehType.set("sigma", str(defaultParameters["sigma"]))

    # Battery parameters
    hasBatteryDevice = customVehType.find(
        "./param[@key='has.battery.device']"
    )

    if hasBatteryDevice is None:
        ET.SubElement(
            customVehType,
            "param",
            {
                "key": "has.battery.device",
                "value": "true"
            }
        )
    else:
        hasBatteryDevice.set("value", "true")

    batteryCapacity = customVehType.find(
        "./param[@key='device.battery.capacity']"
    )

    if batteryCapacity is None:
        ET.SubElement(
            customVehType,
            "param",
            {
                "key": "device.battery.capacity",
                "value": str(battery)
            }
        )
    else:
        batteryCapacity.set("value", str(battery))

    # Save updated additional file
    vehicleTypesAddFile.write(
        vehicleTypesAddFilePath,
        encoding="UTF-8",
        xml_declaration=True
    )

# Generate custom.trips.xml and add trips to it
def generateSUMOTrips(sumoTrips: list[SUMOTrip]):
    customTripsFilePath = customPath / "custom.trips.xml"

    # Remove previous trip generation if present
    if customTripsFilePath.exists():
        customTripsFilePath.unlink()

    # Create new trips file
    routes = ET.Element("routes")
    customTripsFile = ET.ElementTree(routes)

    # Generate sumo trips
    for sumoTrip in sumoTrips:
        attributes = {
            "id": sumoTrip.id,
            "type": sumoTrip.type,

            "depart": str(sumoTrip.depart),

            "fromLonLat": sumoTrip.fromLonLat,
            "toLonLat": sumoTrip.toLonLat,
            "viaLonLat": sumoTrip.viaLonLat,
        }

        if sumoTrip.startSpeed is not None and not math.isnan(sumoTrip.startSpeed):
            attributes["departSpeed"] = str(sumoTrip.startSpeed)

        if sumoTrip.endSpeed is not None and not math.isnan(sumoTrip.endSpeed):
            attributes["arrivalSpeed"] = str(sumoTrip.endSpeed)

        routes.append(ET.Element("trip", attributes))

    customTripsFile.write(
        customTripsFilePath,
        encoding="utf-8",
        xml_declaration=True,
    )

# Adds some additional properties to vehicles into custom.rou.xml
def addExtraToSUMOVehicles(vehiclesExtra: dict[str, SUMOVehicleExtraData]):
    customRoutesFilePath = (
        customPath / "custom.rou.xml" if args.validation
        else customPath / args.scenario_name / "custom.rou.xml"
    )

    customRoutesFile = ET.parse(customRoutesFilePath)
    routes = customRoutesFile.getroot()

    # Iterate over each vehicle inside routes element
    for vehicle in routes.findall("vehicle"):
        # Retrieve vehicle id and edges that constitutes its route
        sumoVehicleId = vehicle.get("id")
        edges = vehicle.find("route").get("edges").split()

        # Calculate precise departPos as an offset from the begginning of the lane closest to GPS point on the first edge
        departPos = getLanePositionOnEdge(
            vehiclesExtra[sumoVehicleId].startpoint.latitude,
            vehiclesExtra[sumoVehicleId].startpoint.longitude,
            edges[0]
        ).offset

        # Calculate precise arrivalPos as an offset from the begginning of the lane closest to GPS point on the last edge
        arrivalPos = getLanePositionOnEdge(
            vehiclesExtra[sumoVehicleId].endpoint.latitude,
            vehiclesExtra[sumoVehicleId].endpoint.longitude,
            edges[-1]
        ).offset

        # Set calculated departPos and arrivalPos
        vehicle.set("departPos", str(departPos))
        vehicle.set("arrivalPos", str(arrivalPos))

        # Add each stop to the vehicle
        if vehiclesExtra[sumoVehicleId].stops is not None:
            for stop in vehiclesExtra[sumoVehicleId].stops:
                stopLane = getLanePositionFromEdgeList(
                    stop.point.latitude,
                    stop.point.longitude,
                    edges
                ).lane.getID()

                vehicle.append(
                    ET.Element("stop", {
                        "lane": stopLane,
                        "duration": str(stop.duration)
                    })
                )

    customRoutesFile.write(
        customRoutesFilePath,
        encoding="utf-8",
        xml_declaration=True,
    )

# Adds missing depart times and vehicle types to randomly generated vehicles into custom.rou.xml
def finalizeRandomSUMOVehicles(customVehicle: CustomVehicle | None, randomizeVehTypes: bool, departDelay: float):
    from SUMO.sumo_vehicles import mapSUMOVehicleTypes

    customRoutesFilePath = (
        customPath / "custom.rou.xml" if args.validation
        else customPath / args.scenario_name / "custom.rou.xml"
    )

    customRoutesFile = ET.parse(customRoutesFilePath)
    routes = customRoutesFile.getroot()
    vehicles = routes.findall("vehicle")

    # Assign a SUMO vehicle type to each vehicle into custom.rou.xml
    vehicleIds = [vehicle.get("id")for vehicle in vehicles]

    SUMOvehicleTypes = mapSUMOVehicleTypes(
        vehicleIds, customType=customVehicle, randomize=randomizeVehTypes
    )

    # Set current depart
    currentDepart: float = 0.00

    # Iterate over each vehicle and assign type and depart
    for vehicle in vehicles:
        vehicle.set("type", SUMOvehicleTypes[vehicle.get("id")])
        vehicle.set("depart", str(currentDepart))

        # Increment current depart based on specified delay
        currentDepart += departDelay

    customRoutesFile.write(
        customRoutesFilePath,
        encoding="utf-8",
        xml_declaration=True,
    )

# Returns the duration of the longest trip resulted after a simulation
def getMaxTripDuration():
    try:
        tripInfosFile = ET.parse(outputPath / "tripinfos.xml")
        tripinfos = tripInfosFile.getroot()

        maxDuration = None

        for tripinfo in tripinfos.findall("tripinfo"):
            duration = float(tripinfo.get("duration"))

            if maxDuration is None or duration > maxDuration:
                maxDuration = duration

        return maxDuration if maxDuration is not None else 970.0
    except Exception:
        return 970.0

# Reads tripinfos.xml to return resulting battery data generated by a simulation
def readSUMOBatteryOut():
    batteryData: dict[str, SUMOBatteryData] = {}
    tripInfosFilePath = (
        outputPath / "tripinfos.xml" if args.validation
        else outputPath / args.scenario_name / "tripinfos.xml"
    )

    tripInfosFile = ET.parse(tripInfosFilePath)
    tripinfos = tripInfosFile.getroot()

    for tripinfo in tripinfos.findall("tripinfo"):
        tripinfoId = tripinfo.get("id")

        batteryData[tripinfoId] = SUMOBatteryData(
            totalEnergyConsumed=float(
                tripinfo.find("battery").get("totalEnergyConsumed")
            )
        )

    return batteryData

# Reads custom.trips.xml, custom.rou.xml and tripinfos.xml to generate some stats about last simulation
def getSUMOSimulationStats():
    customTripsFilePath = (
        customPath / "custom.trips.xml" if args.scenario == "dataset"
        else customPath / "trips.trips.xml"
    )

    customRoutesFilePath = (
        customPath / "custom.rou.xml" if args.validation
        else customPath / args.scenario_name / "custom.rou.xml"
    )

    tripInfosFilePath = (
        outputPath / "tripinfos.xml" if args.validation
        else outputPath / args.scenario_name / "tripinfos.xml"
    )

    # Count generated trips
    customTripsFile = ET.parse(customTripsFilePath)
    trips = customTripsFile.getroot().findall("trip")
    generatedTrips = len(trips)

    # Count vehicles generated by duarouter
    customRoutesFile = ET.parse(customRoutesFilePath)
    vehicles = customRoutesFile.getroot().findall("vehicle")
    generatedVehicles = len(vehicles)

    # Count vehicles actually simulated
    tripInfosFile = ET.parse(tripInfosFilePath)
    tripinfos = tripInfosFile.getroot().findall("tripinfo")
    simulatedVehicles = len(tripinfos)

    return SUMOSimStats(
        generatedTrips=generatedTrips,
        generatedVehicles=generatedVehicles,
        simulatedVehicles=simulatedVehicles,

        discardedByDuarouter=generatedTrips - generatedVehicles,
        failedSimulation=generatedVehicles - simulatedVehicles
    )
