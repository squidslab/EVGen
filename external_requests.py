import os
import requests
import json

from pathlib import Path
from custom_types import GPSPoint

# Calls an endpoint from OpenTopography API to download a .tif file within a bounding box specified by given GPSPoints
# API key is secret and provided using a .env file
def downloadElevation(minGPSPoint: GPSPoint, maxGPSPoint: GPSPoint, outputPath: Path):
    try:
        apiKey = os.getenv("OPENTOPOGRAPHY_API_KEY")

        # A dynamic margin corresponding to 10% of the largest bounding-box dimension is applied, constrained
        # between 0.03° and 0.10°, to provide sufficient elevation coverage around the target area while limiting the
        # size of the requested DEM.
        latitudeRange = maxGPSPoint.latitude - minGPSPoint.latitude
        longitudeRange = maxGPSPoint.longitude - minGPSPoint.longitude

        margin = max(
            0.03,
            min(max(latitudeRange, longitudeRange) * 0.10, 0.10)
        )

        # Check if OpenTopography API Key is set
        if not apiKey:
            raise RuntimeError(
                "OPENTOPOGRAPHY_API_KEY is not set in the environment")

        # Log outgoing request
        print("Sending request to OpenTopography API to retrieve .tif elevation file needed to build 3D network...")

        # Send request to OpenTopography API
        response = requests.get(
            "https://portal.opentopography.org/API/globaldem",
            params={
                "demtype": "COP30",
                "south": minGPSPoint.latitude - margin,
                "north": maxGPSPoint.latitude + margin,
                "west": minGPSPoint.longitude - margin,
                "east": maxGPSPoint.longitude + margin,
                "outputFormat": "GTiff",
                "API_Key": apiKey
            },
            timeout=(10, 60)
        )

        # Check for any errors based on response status
        response.raise_for_status()

        # Save .tif file
        outputPath.write_bytes(response.content)

        # Log successful response
        print("Elevation file successfully retrieved using OpenTopography API")

    except requests.RequestException as error:
        raise RuntimeError(
            f"Failed to download elevation data from OpenTopography: {error}"
        ) from error

# Calls an endpoint from Nominatim API to retrieve the bounding box of a given city
def getCityBoundingBox(city: str) -> tuple[GPSPoint, GPSPoint]:
    try:
        cachePath: Path = Path("./cities_bounding_boxes.json")

        # Load cached bounding boxes if available
        if cachePath.exists():
            with open(cachePath, "r", encoding="utf-8") as file:
                cache = json.load(file)
        else:
            cache = {}

        # Return cached result if available
        if city in cache:
            minGPSPoint = GPSPoint(
                latitude=cache[city]["minLatitude"],
                longitude=cache[city]["minLongitude"]
            )

            maxGPSPoint = GPSPoint(
                latitude=cache[city]["maxLatitude"],
                longitude=cache[city]["maxLongitude"]
            )

            return minGPSPoint, maxGPSPoint

        # Log outgoing request
        print("Sending request to Nominatim API to retrieve city's bounding box...")

        # Send request to Nominatim API
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": city,
                "format": "jsonv2",
                "limit": 1,
                "featureType": "city",
            },
            headers={
                "User-Agent": (
                    "EVGen/1.0 "
                    "(University of Naples Federico II)"
                )
            },
            timeout=10,
        )

        # Check for any errors based on response status
        response.raise_for_status()

        # Log successful response
        print("City's bounding box successfully retrieved using Nominatim API")

        # Retrieve response json
        results = response.json()

        # Raise an error if city was not found
        if not results:
            raise ValueError(f"City not found: {city}")

        # Build bounding box from results
        minGPSPoint = GPSPoint(
            latitude=float(results[0]["boundingbox"][0]),
            longitude=float(results[0]["boundingbox"][2])
        )

        maxGPSPoint = GPSPoint(
            latitude=float(results[0]["boundingbox"][1]),
            longitude=float(results[0]["boundingbox"][3])
        )

        # Save bounding box to cache
        cache[city] = {
            "minLatitude": minGPSPoint.latitude,
            "minLongitude": minGPSPoint.longitude,
            "maxLatitude": maxGPSPoint.latitude,
            "maxLongitude": maxGPSPoint.longitude
        }

        with open(cachePath, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=4)

        # Return bounding box for given city
        return minGPSPoint, maxGPSPoint

    except requests.RequestException as error:
        raise RuntimeError(
            f"Failed to retrieve bounding box from Nominatim: {error}"
        ) from error
