# EVGen

**EVGen** is a software framework for generating virtual electric vehicle consumption datasets through [SUMO (Simulation of Urban MObility)](https://www.eclipse.org/sumo/). It provides a command-line interface (CLI) for configuring and executing different data generation scenarios.

The tool supports different simulation scenarios and can either enrich existing trajectory datasets with simulated electric-vehicle consumption data or generate completely synthetic datasets from a given city or custom geographical area.

---

## Requirements

Before running the tool, make sure the following are installed:

* Python
* SUMO
* The Python dependencies listed below

SUMO must be installed locally because the tool uses several SUMO utilities, including:

* `osmGet`
* `osmBuild`
* `netconvert`
* `randomTrips`
* `duarouter`
* `sumo`

### Python dependencies

The project uses several external Python modules and libraries for different aspects of the tool. The required Python dependencies, including their specific versions, are listed in the `requirements.txt` file.

The modules are used for different aspects of the tool, including:

* **pyproj** — coordinate system transformations.
* **pandas** — loading and processing trajectory datasets.
* **matplotlib** — plotting and visualizing validation results.
* **rtree** — spatial indexing and geographical queries.
* **python-dotenv** — loading configuration variables from the `.env` file.
* **requests** — communicating with external APIs, including OpenTopography and Nominatim.
* **numpy** — numerical computations and array-based data processing.
* **sumolib** — interacting with SUMO networks and performing SUMO-related operations.

To install all the required Python dependencies, run the following command from the project root:

```bash
pip install -r requirements.txt
```

This installs the Python packages required by the project with the versions specified in `requirements.txt`.

---

# Environment configuration

The tool uses a `.env` file to store environment-specific configuration.

Create a `.env` file in the root directory of the project:

```text
SUMO_HOME_PATH="C:\path\to\sumo"
OPENTOPOGRAPHY_API_KEY="your_api_key"
```

### `SUMO_HOME_PATH`

`SUMO_HOME_PATH` specifies the location of the SUMO installation that should be used by the tool.

For example:

```text
SUMO_HOME_PATH="C:\Program Files (x86)\Eclipse\Sumo"
```

The path is used to locate SUMO executables and Python tools such as:

* `netconvert.exe`
* `sumo.exe`
* `osmGet.py`
* `osmBuild.py`
* `randomTrips.py`

Using this variable instead of relying directly on the system `SUMO_HOME` variable allows each user to specify which SUMO installation should be used by the tool.

### `OPENTOPOGRAPHY_API_KEY`

`OPENTOPOGRAPHY_API_KEY` is the API key used to access the [OpenTopography](https://opentopography.org/) API.

The tool uses OpenTopography to automatically download elevation data covering the geographical area required by the current scenario. This elevation data is subsequently used by `netconvert` to generate a 3D SUMO network.

The API key should be kept private and must **not** be committed to the repository.

The `.env` file is therefore included in `.gitignore`.

---

# Simulation scenarios

The tool organizes its execution around the concept of a **scenario**.

A scenario defines the type of input provided to the tool and therefore determines how trajectories are obtained and how the virtual dataset is generated.

The `--scenario` argument currently supports three scenario types:

* `dataset`
* `city`
* `area`

These represent the main use cases of the tool.

## `dataset` scenario

The `dataset` scenario is used when an existing trajectory dataset is available.

In this mode, the tool:

1. Loads trajectories from an existing dataset.
2. Converts them into the common trajectory representation.
3. Generates a suitable SUMO network based on the trajectory data.
4. Converts the trajectories into SUMO-compatible trips and routes.
5. Runs the SUMO simulation.
6. Uses the simulation results to generate a virtual dataset.

The resulting virtual dataset **enriches the original trajectory data** with information obtained from the SUMO simulation, such as:

* vehicle type
* trip duration
* trip distance
* average speed
* battery capacity
* energy consumption
* regenerated energy

The original trajectory metadata, such as starting point, ending point and waypoints, is retained in the resulting dataset.

Currently supported trajectory datasets include:

* eVED
* pNEUMA
* DLR

## `city` scenario

The `city` scenario is used when no trajectory dataset is available.

Instead of providing an existing dataset, the user specifies a city. The tool:

1. Uses the city name to query the [Nominatim](https://nominatim.org/) geocoding service and obtain the geographical bounding box of the selected city.
2. Uses the retrieved bounding box to generate a suitable 3D SUMO network covering the selected area.
3. Generates a specified number of random SUMO trajectories within the network.
4. Runs the SUMO simulation.
5. Generates a virtual dataset from the simulation results.

This mode therefore performs **synthetic dataset generation** rather than enriching an existing dataset.

For example:

```bash
python main.py --scenario city --scenario-name "Naples, Italy"
```

The resulting virtual dataset contains the information generated by the SUMO simulation, such as trip and energy-consumption data.

Since there is no original trajectory dataset in this scenario, there are no input trajectory metadata to preserve. Consequently, the resulting dataset does **not** contain metadata such as original startpoints, endpoints or waypoints.

## `area` scenario

The `area` scenario is used when no trajectory dataset is available and the user wants to generate a synthetic dataset for a specific geographical area without relying on a city name.

Instead of querying a geocoding service, the user directly provides both a custom name for the area and its geographical bounding box.

The tool:

1. Uses the user-provided bounding box to define the geographical area of the simulation.
2. Uses the bounding box to generate a suitable 3D SUMO network covering the selected area.
3. Generates a specified number of random SUMO trajectories within the network.
4. Runs the SUMO simulation.
5. Generates a virtual dataset from the simulation results.

The `area` scenario therefore provides the same synthetic dataset generation workflow as the `city` scenario, but allows the user to define the geographical area explicitly.

The area name does not need to correspond to a real geographical entity. It is simply used as the name of the custom simulation scenario and can be chosen freely.

For example:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box "40.8000,14.1500,40.9000,14.3000"
```

The bounding box must be specified using the following format:

```text
min-lat,min-lon,max-lat,max-lon
```

where:

* `min-lat` — minimum latitude of the area.
* `min-lon` — minimum longitude of the area.
* `max-lat` — maximum latitude of the area.
* `max-lon` — maximum longitude of the area.

Latitude values must be between `-90` and `90`, while longitude values must be between `-180` and `180`. The minimum latitude and longitude must be smaller than their corresponding maximum values.

If the first coordinate is negative, the `=` syntax should be used when passing the argument to prevent the command-line parser from interpreting the negative value as another option. For example:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="-1,2,3,4"
```

The `--scenario-bounding-box` argument is required when using the `area` scenario and is not used by the other scenarios.

As with the `city` scenario, there is no original trajectory dataset whose metadata can be preserved. Consequently, the generated dataset contains only information produced by the SUMO simulation rather than original startpoints, endpoints or waypoints.

---

# Adding a new trajectory dataset

The tool is designed to support multiple trajectory datasets through a common parser interface and dataset-specific pipelines.

To integrate a new dataset from scratch, three main steps are required:

1. Implement the trajectory parser.
2. Create a pipeline for the dataset.
3. Register the pipeline in `main.py`.

---

## 1. Implement the trajectory parser

Every trajectory dataset must be converted into the common trajectory representation used by the tool.

The abstract parser interface is located at:

```text
data/
└── trajectory_parser/
    └── interface.py
```

The interface defines the methods that every dataset-specific parser must implement.

Create a new Python file inside `data/trajectory_parser/` for the dataset.

For example:

```text
data/
└── trajectory_parser/
    ├── interface.py
    ├── eved_parser.py
    └── my_dataset_parser.py
```

The new parser must inherit from `TrajectoryParser`:

```python
from pathlib import Path

from data.trajectory_parser.interface import TrajectoryParser
from custom_types import Trajectory

class MyDatasetParser(TrajectoryParser):

    def parse(self, path: Path) -> list[Trajectory]:
        ...
```

The parser is responsible for converting the original dataset format into the common representation:

```python
@dataclass
class Trajectory:
    trajectoryId: str
    samples: list[TrajectorySample]

@dataclass
class TrajectorySample:
    point: GPSPoint
    timestamp: float | None = None
    speed: float | None = None

@dataclass
class GPSPoint:
    latitude: float
    longitude: float
```

The implementation can contain dataset-specific logic such as:

* Loading CSV or other source files.
* Filtering trajectories or vehicles.
* Converting coordinate systems.
* Converting timestamps.
* Extracting speed.
* Ordering trajectory samples.
* Grouping samples into trajectories.

A parser should expose the dataset through the common `Trajectory` representation regardless of how the original dataset is structured.

### Recommended parser structure

When appropriate, the parser can be organized into separate methods for loading the original dataset and converting it into trajectories:

```python
class MyDatasetParser(TrajectoryParser):

    def parse(self, path: Path) -> list[Trajectory]:
        dataset = self.loadDataset(path)

        # Dataset-specific preprocessing

        return self.buildTrajectories(dataset)

    def loadDataset(self, path: Path):
        ...

    def buildTrajectories(self, dataset) -> list[Trajectory]:
        ...
```

The exact implementation depends on the structure of the dataset.

---

## 2. Create a dataset-specific pipeline

Once the parser has been implemented, create a pipeline for the new dataset inside:

```text
pipelines/
```

For example:

```text
pipelines/
├── eVED_pipeline.py
├── DLR_pipeline.py
└── my_dataset_pipeline.py
```

The pipeline is responsible for orchestrating the operations required for that dataset.

A typical dataset pipeline performs the following operations:

1. Initialize the dataset parser.
2. Parse the dataset.
3. Generate the SUMO 3D network if required.
4. Convert trajectories into SUMO-compatible trips.
5. Generate SUMO routes if required.
6. Run the SUMO simulation
7. Generate the resulting virtual dataset.

Dataset-specific operations should remain inside the dataset's pipeline rather than being added to the generic parser.

The `city` and `area` scenarios use their own synthetic trajectory generation workflow and do not require a trajectory dataset parser.

---

## 3. Add the pipeline to `main.py`

Finally, the new pipeline must be made available from `main.py`.

Dataset selection is performed through the `--scenario-name` argument when `--scenario dataset` is selected.

The main program dispatches execution to the appropriate pipeline using a `match` statement:

```python
match args.scenario_name:
    case "eVED":
        runEVEDPipeline()
    case "pNEUMA":
        runPNEUMAPipeline()
    case "DLR":
        runDLRPipeline()
    case _:
        print("Invalid dataset!")
        quit()
```

When adding a new dataset, remember to:

* Implement its trajectory parser.
* Create its dataset-specific pipeline.
* Import the pipeline in `main.py`.
* Add a corresponding case to the `match` statement.
* Add the dataset files under the appropriate directory in `datasets/`.

For example, adding a dataset called `MyDataset` would require a corresponding case:

```python
case "MyDataset":
    runMyDatasetPipeline()
```

The dataset name passed to `--scenario-name` must therefore match the name handled by the `match` statement.

---

# Command-line arguments

The tool can be configured through command-line arguments.

## `--scenario`

Specifies the type of scenario to execute.

The currently supported values are:

* `dataset` — use an existing trajectory dataset and enrich it with simulated consumption data.
* `city` — use a city as input and generate a completely synthetic dataset from randomly generated trajectories.
* `area` — use a custom geographical area as input and generate a completely synthetic dataset from randomly generated trajectories.

The default value is `dataset`.

For example:

```bash
python main.py --scenario dataset
```

or:

```bash
python main.py --scenario city
```

or:

```bash
python main.py --scenario area
```

---

## `--scenario-name`

Specifies the name of the dataset, city or custom geographical area used by the selected scenario.

When using the `dataset` scenario, the value must correspond to a dataset supported by the tool.

For example:

```bash
python main.py --scenario dataset --scenario-name eVED
```

When using the `city` scenario, the value specifies the city for which the simulation area should be generated.

It is recommended to specify the city using the format:

```text
City, Country
```

For example:

```bash
python main.py --scenario city --scenario-name "Naples, Italy"
```

The city name is used to retrieve the corresponding geographical bounding box.

When using the `area` scenario, the value specifies the name assigned to the custom geographical area. It does not need to correspond to a real geographical name and can be chosen freely.

For example:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="40.8000,14.1500,40.9000,14.3000"
```

The geographical extent of the area is specified separately through the `--scenario-bounding-box` argument.

---

## `--scenario-bounding-box`

Specifies the geographical bounding box of a custom area when using the `area` scenario.

The bounding box must be provided using the following format:

```text
min-lat,min-lon,max-lat,max-lon
```

For example:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="40.8000,14.1500,40.9000,14.3000"
```

The four coordinates represent:

* `min-lat` — minimum latitude.
* `min-lon` — minimum longitude.
* `max-lat` — maximum latitude.
* `max-lon` — maximum longitude.

The latitude must be between `-90` and `90`, while the longitude must be between `-180` and `180`. The minimum values must also be smaller than their corresponding maximum values.

Negative coordinates are valid. For example:

```text
-1,2,3,4
```

represents a valid bounding box with a minimum latitude of `-1`.

When the first coordinate is negative, the argument should be passed using the `=` syntax:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="-1,2,3,4"
```

This prevents the command-line parser from interpreting the negative first coordinate as another command-line option.

This argument is **required** when using the `area` scenario and is ignored for the other scenarios.

---

## `--validation`

Runs the SUMO validation workflow.

```bash
python main.py --validation
```

This mode is intended to validate the reliability of the SUMO simulation by comparing the simulated trajectories with the original reference trajectories and calculating the corresponding errors regarding energy consumption.

**Important:** `--validation` is currently only supported for **eVED**.

The required eVED dataset must therefore be correctly placed inside:

```text
datasets/eVED/
```

before using this option.

---

## `--skip-net-generation`

Skips the automatic generation of the 3D SUMO network.

```bash
python main.py --scenario dataset --scenario-name eVED --skip-net-generation
```

This is useful when a suitable network has already been generated and should be reused instead of downloading OSM and elevation data and rebuilding the network.

---

## `--skip-route-generation`

Skips the generation of SUMO routes.

```bash
python main.py --scenario dataset --scenario-name eVED --skip-route-generation
```

When this option is specified, the tool also assumes that the SUMO network already exists and therefore **implicitly skips network generation as well**.
Consequently, `--skip-route-generation` does not need to be combined with `--skip-net-generation`.

This option is useful when both the required network and routes have already been generated and should be reused.

This option can also be specified in validation mode, when the routes have already been generated. In validation mode, the network is predefined and does not need to be generated.

### Important when using the `dataset` scenario

When `--skip-route-generation` is used with the `dataset` scenario, the existing routes must correspond to the same trajectory batch selected through `--trajectory-batch`.
The generated routes contain the trajectory IDs that are later used to match SUMO simulation results with the original trajectory metadata.

For example, if:

```bash
python main.py --scenario dataset --scenario-name eVED --trajectory-batch 2 --skip-route-generation
```

is executed, the reused routes must have been generated for **trajectory batch 2**.

If the routes correspond to a different batch, their trajectory IDs will not match the original trajectories loaded by the current execution. As a result, the simulated trips cannot be associated with the corresponding original trajectory metadata and the generated virtual dataset may be empty.

---

## `--trajectory-batch`

Specifies which batch of trajectories should be processed when using the `dataset` scenario.

The tool processes trajectories in batches of **15,000 trajectories** by default. This allows large trajectory datasets to be processed through multiple executions, keeping individual simulation times more manageable.

The argument specifies the batch number:

* `1` — first 15,000 trajectories
* `2` — trajectories 15,001–30,000
* `3` — trajectories 30,001–45,000
* and so on.

For example:

```bash
python main.py --scenario dataset --scenario-name eVED --trajectory-batch 2
```

This processes the second batch of 15,000 trajectories.

The default value is `1`, meaning that the first batch is processed when no value is explicitly specified.

If the selected batch contains fewer than 15,000 remaining trajectories, all remaining trajectories are processed.

This option is particularly useful for generating a virtual dataset in multiple smaller executions, which can subsequently be combined into a larger dataset.

This option is used with the **`dataset` scenario** and is not applicable to `city` or `area`.

---

## `--trajectories-number`

Specifies the number of random trajectories to generate when using the `city` or `area` scenario.

The default value is **5,000 trajectories**.

For example:

```bash
python main.py --scenario city --scenario-name "Naples, Italy" --trajectories-number 10000
```

This requests the generation of 10,000 random trajectories within the selected city's SUMO network.

For a custom area, the same argument can be used:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="40.8000,14.1500,40.9000,14.3000" --trajectories-number 10000
```

This generates 10,000 random trajectories within the SUMO network corresponding to the specified bounding box.

This option only applies to the **`city`** and **`area`** scenarios.

Unlike `--trajectory-batch`, this argument does not select a portion of an existing dataset: it directly determines the number of synthetic trajectories to generate.

---

## `--eved-veh-types`

Specifies which vehicle types should be extracted when running the eVED pipeline or in validation mode.

The supported vehicle types are:

* `ICE` — Internal Combustion Engine
* `HEV` — Hybrid Electric Vehicle
* `PHEV` — Plug-in Hybrid Electric Vehicle
* `EV` — Electric Vehicle

When running in validation mode, the ICE vehicle type is ignored even if specified, since validation is only supported for HEV, PHEV, and EV vehicles.
Using EV is recommended for validation, as it provides the most direct comparison for electric-vehicle consumption.

For example, to process only electric vehicles:

```bash
python main.py --scenario dataset --scenario-name eVED --eved-veh-types EV
```

Multiple types can be specified:

```bash
python main.py --scenario dataset --scenario-name eVED --eved-veh-types EV HEV PHEV
```

For example, to include all supported vehicle types:

```bash
python main.py --scenario dataset --scenario-name eVED --eved-veh-types ICE HEV PHEV EV
```

This option only applies to the eVED dataset.

---

## `--random-veh-types`

Randomly assigns SUMO electric vehicle models to vehicles whose original vehicle model is unknown.

```bash
python main.py --scenario dataset --scenario-name eVED --random-veh-types
```

By default, vehicles without a specific vehicle model are assigned the generic SUMO electric vehicle type:

```text
ev_generic
```

When `--random-veh-types` is enabled, these vehicles are instead assigned to one of the available predefined electric vehicle model types:

* `tesla_model_y`
* `tesla_model_3`
* `chevrolet_equinox_ev`
* `ford_mustang_mach_e`
* `hyundai_ioniq_5`

The assignment is randomized while keeping the distribution of vehicle models as balanced as possible. Therefore, the number of trajectories assigned to each model differs by at most one.

For the eVED dataset, electric vehicles with an explicitly identified electric-vehicle classification continue to use the `leaf_2013` SUMO vehicle type.

The option is also applicable to the `city` and `area` scenarios. Since randomly generated trajectories do not have an original vehicle model, they use the generic electric vehicle type by default or one of the available specific models when randomization is enabled.

The option is **disabled by default**.

Without this option, vehicles with an unknown model use `ev_generic`.

---

## `--custom-vehicle`

Specifies a custom electric vehicle type to be used for trajectories whose original vehicle model is unknown.

The custom vehicle is specified as a comma-separated list of `key=value` parameters:

```text
mass=1800,accel=2.5,max-speed=160,battery=75
```

The supported parameters are:

* `mass` — vehicle mass in kg.
* `accel` — vehicle acceleration in m/s².
* `max-speed` — maximum speed in km/h.
* `battery` — battery capacity in kWh.

For example:

```bash
python main.py --scenario dataset --scenario-name eVED --custom-vehicle "mass=1900,accel=2.8,max-speed=180,battery=75"
```

The custom vehicle is represented internally by the SUMO vehicle type:

```text
custom_ev
```

When `--custom-vehicle` is specified, the corresponding `custom_ev` vehicle type is created or updated in the SUMO vehicle configuration.

Parameters that are not specified use the default values of the generic electric vehicle:

| Parameter   |                      Default value |
| ----------- | ---------------------------------: |
| `mass`      |                            1800 kg |
| `accel`     |                           2.5 m/s² |
| `decel`     |                           3.0 m/s² |
| `max-speed` | 44.44 m/s (approximately 160 km/h) |
| `sigma`     |                                  1 |
| `battery`   |                             60 kWh |

Only `mass`, `accel`, `max-speed` and `battery` can be customized through this argument. `decel` and `sigma` always use the default values.
The input values are automatically converted to the units required by SUMO: `max-speed` is converted from km/h to m/s and `battery` is converted from kWh to Wh.

The argument can be used independently or together with `--random-veh-types`.

### Interaction with `--random-veh-types`

The behavior depends on whether `--custom-vehicle` and `--random-veh-types` are specified.

| `--custom-vehicle` | `--random-veh-types` | Vehicle types assigned to unknown-model trajectories |
| ------------------ | -------------------- | ---------------------------------------------------- |
| Not specified      | Not specified        | `ev_generic`                                         |
| Specified          | Not specified        | `custom_ev`                                          |
| Not specified      | Specified            | Predefined electric vehicle types                    |
| Specified          | Specified            | Predefined electric vehicle types + `custom_ev`      |

When both options are specified, the custom vehicle is added to the randomization pool together with the predefined electric vehicle models.

For example:

```bash
python main.py --scenario dataset --scenario-name eVED --custom-vehicle "mass=1900,accel=2.8,max-speed=180,battery=75" --random-veh-types
```

In this case, unknown-model trajectories are randomly assigned among:

* `tesla_model_y`
* `tesla_model_3`
* `chevrolet_equinox_ev`
* `ford_mustang_mach_e`
* `hyundai_ioniq_5`
* `custom_ev`

The custom vehicle therefore replaces the generic `ev_generic` type when used without randomization, while with randomization it becomes an additional available vehicle type rather than replacing any of the predefined models.

For eVED, electric vehicles with an explicitly identified electric-vehicle classification always use `leaf_2013`, regardless of whether `--custom-vehicle` or `--random-veh-types` is specified. These options affect only trajectories whose original vehicle model is unknown.

The option is applicable to the `dataset`, `city` and `area` scenarios.

---

## `--depart-delay`

Specifies the delay in seconds between the departure times of generated SUMO trips.

For example:

```bash
python main.py --scenario dataset --scenario-name eVED --depart-delay 10
```

The shortest execution time is achieved by setting this argument to `0`, which is also the default value.
Collisions are disabled by default for all SUMO simulations, ensuring that vehicles do not interact with or influence each other's behavior.

---

# Example workflows

## Run a dataset normally

```bash
python main.py --scenario dataset --scenario-name eVED
```

This performs the complete eVED pipeline, including network and route generation.

---

## Run a city simulation

```bash
python main.py --scenario city --scenario-name "Naples, Italy"
```

This retrieves the geographical area of Naples, generates a corresponding SUMO network, creates the default number of random trajectories and produces a synthetic virtual dataset.

---

## Run a custom area simulation

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="40.8000,14.1500,40.9000,14.3000"
```

This uses the specified bounding box to define the simulation area, generates a corresponding SUMO network, creates the default number of random trajectories and produces a synthetic virtual dataset.

The name `Area01` is a custom identifier assigned to the area and does not need to correspond to a real geographical entity.

---

## Generate a specific number of city trajectories

```bash
python main.py --scenario city --scenario-name "Rome, Italy" --trajectories-number 10000
```

This generates a synthetic dataset based on 10,000 random trajectories within the selected city's area.

---

## Generate a specific number of trajectories in a custom area

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="40.8000,14.1500,40.9000,14.3000" --trajectories-number 10000
```

This generates a synthetic dataset based on 10,000 random trajectories within the specified bounding box.

---

## Reuse an existing network

```bash
python main.py --scenario dataset --scenario-name eVED --skip-net-generation
```

This reuses an already generated SUMO network while still generating the routes required for the selected trajectory batch.

---

## Reuse an existing network and routes

```bash
python main.py --scenario dataset --scenario-name eVED --trajectory-batch 2 --skip-route-generation
```

This reuses both the network and routes.

The reused routes must correspond to trajectory batch 2. Otherwise, the simulated trajectory IDs will not match the original trajectory metadata and the resulting virtual dataset may be empty.

---

## Process a specific trajectory batch

```bash
python main.py --scenario dataset --scenario-name eVED --trajectory-batch 2
```

This processes the second batch of 15,000 trajectories.

---

## Combine trajectory batching with other options

For example:

```bash
python main.py --scenario dataset --scenario-name eVED --trajectory-batch 3 --skip-net-generation
```

This processes the third trajectory batch while reusing an already generated SUMO network.

---

## Randomize unknown vehicle types

```bash
python main.py --scenario dataset --scenario-name eVED --random-veh-types
```

This randomly assigns specific SUMO electric vehicle models to vehicles whose original model is unknown, while keeping the distribution of the models balanced.

Without this option, such vehicles use the generic `ev_generic` SUMO vehicle type.

For a city scenario:

```bash
python main.py --scenario city --scenario-name "Naples, Italy" --random-veh-types
```

randomly generated vehicles are assigned the available specific SUMO electric vehicle models instead of the generic type.

The same option can be used with an area scenario:

```bash
python main.py --scenario area --scenario-name "Area01" --scenario-bounding-box="40.8000,14.1500,40.9000,14.3000" --random-veh-types
```

---

## Use a custom electric vehicle

```bash
python main.py --scenario dataset --scenario-name eVED --custom-vehicle "mass=1900,accel=2.8,max-speed=180,battery=75"
```

This creates or updates the `custom_ev` SUMO vehicle type and assigns it to trajectories whose original vehicle model is unknown.

---

## Use a custom vehicle with randomization

```bash
python main.py --scenario dataset --scenario-name eVED --custom-vehicle "mass=1900,accel=2.8,max-speed=180,battery=75" --random-veh-types
```

This adds `custom_ev` to the pool of predefined electric vehicle types. Unknown-model trajectories are then randomly assigned among all available predefined models and the custom vehicle, while maintaining a balanced distribution.

---

## Run SUMO validation

```bash
python main.py --validation --eved-veh-types EV
```

The validation workflow currently uses eVED as its reference dataset.

---

# Project structure

A simplified project structure is:

```text
EVGen/
│
├── data/
│   └── trajectory_parser/
│       ├── interface.py
│       ├── eved_parser.py
│       └── ...
│
├── datasets/
│   ├── eVED/
│   ├── pNEUMA/
│   └── ...
│
├── pipelines/
│   ├── eVED_pipeline.py
│   ├── pNEUMA_pipeline.py
│   └── ...
│
├── SUMO/
│   ├── sumo_files/
│   │   ├── config/
│   │   ├── custom/
│   │   └── output/
│   │
│   └── sumo_files_validation/
│       ├── config/
│       ├── custom/
│       └── output/
│
├── virtual_data/
│   └── dataset_generation.py
│
├── virtual_datasets/
│   ├── 20260815_eVED_001.csv
│   ├── ...
│   └── ...
│
├── main.py
├── .env
└── ...
```

### `data/`

Contains the common trajectory representation and the dataset-specific trajectory parsers.

### `datasets/`

Contains the original trajectory datasets used as input by the `dataset` scenario.

Each supported dataset has its own directory.

### `pipelines/`

Contains the dataset-specific execution pipelines and city pipeline.

Each pipeline coordinates parsing, network generation, route generation, SUMO simulation and virtual dataset generation for its corresponding scenario.

The `city` and `area` scenarios use synthetic trajectory generation instead of dataset-specific trajectory parsers.

### `SUMO/`

Contains SUMO configuration and generated SUMO-related files.

`sumo_files/` contains the configuration used for normal simulations, while `sumo_files_validation/` contains the configuration and reference resources used for validation.

Generated networks, routes and other execution-specific files are not intended to be committed to the repository.

### `virtual_data/`

Contains the logic responsible for generating virtual datasets from SUMO simulation results.

Currently it contains:

```text
virtual_data/
└── dataset_generation.py
```

### `virtual_datasets/`

Contains the virtual trajectory datasets generated by the tool.

Generated datasets use a naming convention such as:

```text
20260815_eVED_001.csv
```

where the filename identifies the generation date, source scenario and generated dataset number.

---

# Quick reference

| Argument                  | Purpose                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------- |
| `--scenario`              | Select the scenario type: `dataset`, `city` or `area`                                       |
| `--scenario-name`         | Specify the dataset name, city name or custom area name, depending on the selected scenario |
| `--scenario-bounding-box` | Specify the bounding box of a custom area when using the `area` scenario                    |
| `--validation`            | Run the SUMO validation workflow                                                            |
| `--skip-net-generation`   | Reuse an existing SUMO 3D network                                                           |
| `--skip-route-generation` | Reuse existing SUMO routes and implicitly reuse the existing network                        |
| `--trajectory-batch`      | Select the 15,000-trajectory batch to process in the `dataset` scenario                     |
| `--trajectories-number`   | Specify the number of random trajectories to generate in the `city` or `area` scenario      |
| `--eved-veh-types`        | Select ICE/HEV/PHEV/EV vehicles when using eVED                                             |
| `--random-veh-types`      | Randomly assign balanced SUMO EV models to vehicles without a known model                   |
| `--custom-vehicle`        | Specify a custom electric vehicle type and its parameters                                   |
| `--depart-delay`          | Set the departure delay between generated trips                                             |

The `--scenario` argument currently supports three scenario types:

* `dataset` — enrich an existing trajectory dataset with simulated consumption data.
* `city` — generate a synthetic virtual dataset from random trajectories within a selected city.
* `area` — generate a synthetic virtual dataset from random trajectories within a user-defined geographical area.

`--trajectory-batch` is used only with the `dataset` scenario and defaults to `1`.

`--trajectories-number` is used with the `city` and `area` scenarios and defaults to `5,000`.

`--scenario-bounding-box` is required when using the `area` scenario. It defines the geographical area using the format `min-lat,min-lon,max-lat,max-lon`.

When `--skip-route-generation` is specified, network generation is also skipped. When using this option with the `dataset` scenario, the reused routes must correspond to the selected `--trajectory-batch`; otherwise, the simulated trajectory IDs will not match the original trajectory metadata and the resulting virtual dataset may be empty.

`--random-veh-types` is disabled by default. When enabled, vehicles without a known model are assigned specific SUMO electric vehicle models in a randomized but balanced distribution instead of using the generic `ev_generic` type.

`--custom-vehicle` is disabled by default. When specified without `--random-veh-types`, vehicles without a known model are assigned the resulting `custom_ev` type. When used together with `--random-veh-types`, the custom vehicle is added to the pool of predefined electric vehicle models and participates in the balanced randomization.

For eVED, explicitly identified electric vehicles always use the `leaf_2013` SUMO vehicle type, regardless of the custom vehicle or randomization options.

---

# Author

**Giuseppe Tarallo**

University of Naples Federico II