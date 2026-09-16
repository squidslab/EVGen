import math
import pandas as pd

from custom_types import GPSPoint, StopPoint, TrajectorySample, Trajectory

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2 +
        math.cos(phi1) *
        math.cos(phi2) *
        math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calculateTripDistance(trajectorySamples: list[TrajectorySample]):
    distance = 0.0

    for previous, current in zip(trajectorySamples[:-1], trajectorySamples[1:]):
        distance += haversine(
            previous.point.latitude,
            previous.point.longitude,
            current.point.latitude,
            current.point.longitude
        )

    return distance

def findStops(trajectorySamples: list[TrajectorySample]):
    stops: list[StopPoint] = []

    # Sort samples by timestamp when available
    trajectorySamples = sorted(
        trajectorySamples,
        key=lambda sample: sample.timestamp
        if sample.timestamp is not None
        else 0
    )

    # Identify consecutive samples where the vehicle is stopped
    stopped = [
        sample.speed is not None and abs(sample.speed) < 0.01
        for sample in trajectorySamples
    ]

    # Find groups of consecutive stopped samples
    groupStart = None

    for index, isStopped in enumerate(stopped):
        if isStopped and groupStart is None:
            # Start of a new stop
            groupStart = index

        elif not isStopped and groupStart is not None:
            # End of the current stop
            group = trajectorySamples[groupStart:index]

            startSample = group[0]
            endSample = group[-1]

            if (startSample.timestamp is not None and endSample.timestamp is not None):
                stops.append(
                    StopPoint(
                        point=startSample.point,
                        duration=float(
                            (endSample.timestamp - startSample.timestamp) / 1000
                        )
                    )
                )

            groupStart = None

    # Handle a stop that continues until the last sample
    if groupStart is not None:
        group = trajectorySamples[groupStart:]

        startSample = group[0]
        endSample = group[-1]

        if (startSample.timestamp is not None and endSample.timestamp is not None):
            stops.append(
                StopPoint(
                    point=startSample.point,
                    duration=float(
                        (endSample.timestamp - startSample.timestamp) / 1000
                    )
                )
            )

    return stops

def findWaypoints(TrajectorySamples: list[TrajectorySample], maxWaypoints: int = 15):
    # Remove first and last point since they are already represented by startpoint and endpoint
    intermediateSamples = TrajectorySamples[1:-1]

    if not intermediateSamples:
        return []

    distance = calculateTripDistance(TrajectorySamples)

    # One waypoint every 1000 meters, capped at maxWaypoints
    waypointCount = min(maxWaypoints, max(0, math.floor(distance / 1000)))

    if waypointCount == 0:
        return []

    interval = max(1, len(intermediateSamples) // waypointCount)

    return [
        sample.point
        for sample in intermediateSamples[::interval][:waypointCount]
    ]

def getTrajectoriesBounds(trajectories: list[Trajectory]) -> tuple[GPSPoint, GPSPoint]:
    minLat = float("inf")
    minLon = float("inf")
    maxLat = float("-inf")
    maxLon = float("-inf")

    for trajectory in trajectories:
        for sample in trajectory.samples:
            latitude = sample.point.latitude
            longitude = sample.point.longitude

            minLat = min(minLat, latitude)
            minLon = min(minLon, longitude)

            maxLat = max(maxLat, latitude)
            maxLon = max(maxLon, longitude)

    minGPSPoint = GPSPoint(
        latitude=minLat,
        longitude=minLon
    )

    maxGPSPoint = GPSPoint(
        latitude=maxLat,
        longitude=maxLon
    )

    return minGPSPoint, maxGPSPoint

def getTrajectoryBatch(trajectories: list[Trajectory], batch: int) -> list[Trajectory]:
    # Define trajectory batch
    start = (batch - 1) * 15000
    end = start + 15000

    trajectoryBatch = trajectories[start:end]

    # Log trajectory batch info
    print(
        f"Processing trajectory batch {batch}: "
        f"{len(trajectoryBatch)} trajectories"
    )

    return trajectoryBatch

def buildTrajectoryDataframe(trajectories: list[Trajectory], includeSpeedData: bool = False) -> pd.DataFrame:
    SUMOTrajectories = []

    for trajectory in trajectories:
        trajectoryData = {
            "trajectoryId": trajectory.trajectoryId,
            "startpoint": trajectory.samples[0].point,
            "endpoint": trajectory.samples[-1].point,
            "waypoints": findWaypoints(trajectory.samples),
            "startSpeed": None,
            "endSpeed": None,
            "stops": None
        }

        if includeSpeedData:
            trajectoryData.update(
                {
                    "startSpeed": trajectory.samples[0].speed,
                    "endSpeed": trajectory.samples[-1].speed,
                    "stops": findStops(trajectory.samples)
                }
            )

        SUMOTrajectories.append(trajectoryData)

    return pd.DataFrame(SUMOTrajectories)
