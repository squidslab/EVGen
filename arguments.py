import argparse

from custom_types import GPSPoint, CustomVehicle

# Checks if an int argument is positive
def positiveInteger(intArg: str) -> int:
    integerValue = int(intArg)

    if integerValue <= 0:
        raise argparse.ArgumentTypeError(
            "Value must be a positive integer"
        )

    return integerValue

# Checks if a float argument is positive
def positiveFloat(floatArg: str) -> float:
    floatValue = float(floatArg)

    if floatValue <= 0:
        raise argparse.ArgumentTypeError(
            "Value must be a positive integer"
        )

    return floatValue

# Parses the scenario bouding box string argument into an internal rappresentation
def parseBoundingBox(boundingBoxArg: str) -> tuple[GPSPoint, GPSPoint]:
    try:
        coordinates = [
            float(coordinate.strip())
            for coordinate in boundingBoxArg.split(",")
        ]
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Area's bounding box must contain four numeric coordinates "
            "in the format 'min-lat,min-lon,max-lat,max-lon'"
        )

    # Validate bounding box
    if len(coordinates) != 4:
        raise argparse.ArgumentTypeError(
            "Area's bounding box must contain exactly four coordinates "
            "in the format 'min-lat,min-lon,max-lat,max-lon'"
        )

    minLat, minLon, maxLat, maxLon = coordinates

    if not -90 <= minLat <= 90 or not -90 <= maxLat <= 90:
        raise argparse.ArgumentTypeError(
            "Latitude must be between -90 and 90"
        )

    if not -180 <= minLon <= 180 or not -180 <= maxLon <= 180:
        raise argparse.ArgumentTypeError(
            "Longitude must be between -180 and 180"
        )

    if minLat >= maxLat:
        raise argparse.ArgumentTypeError(
            "Minimum latitude must be smaller than maximum latitude"
        )

    if minLon >= maxLon:
        raise argparse.ArgumentTypeError(
            "Minimum longitude must be smaller than maximum longitude"
        )

    # Build GPS Points
    minGPSPoint = GPSPoint(
        latitude=minLat,
        longitude=minLon
    )

    maxGPSPoint = GPSPoint(
        latitude=maxLat,
        longitude=maxLon
    )

    return minGPSPoint, maxGPSPoint

# Parses the custom vehicle string argument into an internal representation
def parseCustomVehicle(customVehicleArg: str) -> CustomVehicle:
    allowedParameters = {"mass", "accel", "max-speed", "battery"}

    parameters = {}

    for parameter in customVehicleArg.split(","):
        parameter = parameter.strip()

        # Must be a key=value pair
        if "=" not in parameter:
            raise argparse.ArgumentTypeError(
                f"invalid parameter '{parameter}', expected key=value"
            )

        key, parameterValue = parameter.split("=", 1)
        key = key.strip()
        parameterValue = parameterValue.strip()

        # Unknown parameter
        if key not in allowedParameters:
            raise argparse.ArgumentTypeError(
                f"unknown parameter '{key}'"
            )

        # Value must be numeric
        try:
            parameters[key] = float(parameterValue)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"invalid value for '{key}': '{parameterValue}'"
            )

    return CustomVehicle(
        mass=parameters.get("mass"),
        accel=parameters.get("accel"),
        maxSpeed=parameters.get("max-speed"),
        battery=parameters.get("battery")
    )


parser = argparse.ArgumentParser()

# Main arguments
parser.add_argument(
    "--validation",
    action="store_true",
    help="Run SUMO validation. "
         "This config doesn't require a set database since it always uses eVED."
)

parser.add_argument(
    "--scenario",
    type=str,
    choices=["dataset", "city", "area"],
    default="dataset",
    help="Specify the simulation scenario type: "
         "'dataset' for a trajectory dataset, "
         "'city' for a city, or "
         "'area' for a custom geographical area."
)

parser.add_argument(
    "--scenario-name",
    type=str,
    default="eVED",
    help="Name of the simulation scenario: a trajectory dataset, "
         "a city, or a custom name for a geographical area. "
         "For the 'dataset' scenario, this argument specifies the name "
         "of a supported trajectory dataset for which a processing "
         "pipeline has been implemented. "
         "For the 'city' scenario, it is recommended to use the format "
         "'City, Country', e.g. 'Naples, Italy'. "
         "For the 'area' scenario, this argument specifies the name "
         "assigned to the custom geographical area."
)

parser.add_argument(
    "--scenario-bounding-box",
    type=parseBoundingBox,
    default=None,
    metavar="MIN-LAT,MIN-LON,MAX-LAT,MAX-LON",
    help="Specify the bounding box of a custom geographical area "
         "using the format 'min-lat,min-lon,max-lat,max-lon'. "
         "If the first coordinate is negative, use the '=' syntax "
         "to prevent argparse from interpreting it as an option, "
         "e.g. '--scenario-bounding-box=-1,2,3,4'. "
         "This argument is required when using the 'area' scenario "
         "and is ignored for other scenarios."
)

# Skip arguments
parser.add_argument(
    "--skip-net-generation",
    action="store_false",
    dest="generate_net",
    default=True,
    help="Skip generation of a new 3D SUMO network."
)

parser.add_argument(
    "--skip-route-generation",
    action="store_false",
    dest="generate_ruotes",
    default=True,
    help="Skip generation of new SUMO routes."
)

# Scenario-specific arguments
parser.add_argument(
    "--trajectory-batch",
    type=positiveInteger,
    default=1,
    help="Batch of trajectories to process (15,000 trajectories per batch). "
         "Only applicable to the 'dataset' scenario."
)

parser.add_argument(
    "--trajectories-number",
    type=positiveInteger,
    default=5000,
    help="Number of random trajectories to generate. "
         "Only applicable to the 'city' and 'area' scenarios."
)

# Vehicle types arguments
parser.add_argument(
    "--eved-veh-types",
    nargs="+",
    choices=["ICE", "HEV", "PHEV", "EV"],
    default=["HEV", "PHEV", "EV"],
    metavar="TYPE",
    help="Vehicle types to include in the simulation when using eVED."
)

parser.add_argument(
    "--random-veh-types",
    action="store_true",
    help="Randomly assign electric vehicle types to trajectories "
         "with unknown vehicle models. By default, these trajectories "
         "are assigned the generic 'ev_generic' vehicle type. "
         "When specified alone, trajectories are randomly assigned "
         "among the predefined electric vehicle types. "
         "When used together with --custom-vehicle, the custom vehicle "
         "is also included in the randomization pool. "
)

parser.add_argument(
    "--custom-vehicle",
    type=parseCustomVehicle,
    metavar="PARAMETERS",
    default=None,
    help="Specify a custom electric vehicle using the format: "
         "'mass=1800,accel=2.5,max-speed=160,battery=75'. "
         "Mass is expressed in kg, acceleration in m/s², "
         "maximum speed in km/h and battery capacity in kWh. "
         "When specified alone, the custom vehicle is used instead "
         "of the default 'ev_generic' type for trajectories with "
         "unknown vehicle models. "
         "When used together with --random-veh-types, the custom "
         "vehicle is added to the randomization pool."
)

# Depart delay argument
parser.add_argument(
    "--depart-delay",
    type=positiveFloat,
    default=0,
    help="Delay between each simulated vehicle departure."
)

args = parser.parse_args()
