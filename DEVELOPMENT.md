# Project structure

The project is structured as follows:

```bash
.
├── api-analyser # API analyser to analyze intervals in which data is provided by the API
│   ├── analyse_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run_analyzer.sh
├── autostart # Autostart script for the weather monitor
├── DEVELOPMENT.md
├── docker-compose-dev.yml # Docker compose file for development
├── docker-compose.yml # Docker compose file for the weather monitor
├── Dockerfile # Dockerfile for the weather monitor
├── download_model.sh # Script to download the model in order to make predictions
├── example.env # Example configuration file
├── images # Images used in the README
│   └── dashboard.png
├── install.sh # Script to install the weather monitor
├── prediction # Prediction related files (notebooks, CSVs used to train the model)
│   ├── input
│   │   ├── input.csv
│   │   ├── messwerte_mythenquai_2007-2021.csv
│   │   └── messwerte_tiefenbrunnen_2007-2021.csv
│   └── weather_prediction.ipynb
├── README.md
├── requirements.txt # Requirements for the weather monitor
└── src 
    ├── app.py # Main application file
    ├── csv # CSV files to import on startup
    │   ├── messwerte_mythenquai_2022.csv
    │   └── messwerte_tiefenbrunnen.csv
    ├── plotting.py # Plotting related functions
    ├── prediction.py # Prediction related functions
    ├── service_status.py # Service status related functions
    ├── static # Static files (CSS, JS, images)
    │   ├── css
    │   │   └── style.css
    │   └── images
    │       └── direction.png
    ├── templates # HTML templates
    │   ├── index.html
    │   ├── loading.html
    │   ├── plots.html
    │   ├── prediction.html
    │   └── station.html
    ├── weather_data.py # Database and API communication related functions
    └── weather_repository.py # Management of data and query related functions
```

# Tech stack
The weather monitor is built with the following technologies:
- [Docker](https://www.docker.com/) used to containerize the application
- [Docker Compose](https://docs.docker.com/compose/) used to orchestrate the application
- [Python](https://www.python.org/) as programming language
    - Used version: 3.10
- [Flask](https://flask.palletsprojects.com/en/2.0.x/) as web framework
- [Plotly](https://plotly.com/python/) as plotting library
- [sci-kit learn](https://scikit-learn.org/stable/) used to make predictions with the help of [K-nearest neighbors algorithm](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsRegressor.html)
- [schedule](https://schedule.readthedocs.io/en/stable/) used to schedule the generation of predictions, plots and health checks
- [InfluxDB](https://www.influxdata.com/) used as database. Official python client is used to communicate with the database.
- [Bash scripts](https://www.gnu.org/software/bash/) used to automate the download of files on build time and the installation of the weather monitor
- [Intro.js](https://introjs.com/) used to provide a guided tour of the weather monitor
- [Bulma](https://bulma.io/) used as CSS framework
- [Pickle](https://docs.python.org/3/library/pickle.html) used to serialize and deserialize the prediction model

All python dependencies are also listed in the `requirements.txt` file with their respective version.

# Environment
The weather monitor is built with Docker. The `Dockerfile` is used to build the image and the `docker-compose.yml` file is used to run the image. The `docker-compose-dev.yml` file is used to run the image in development mode.

## Run in development mode (Docker)
> **Note**: The scripts used are based on a Linux environment. They may not work on other operating systems. On Windows the scripts can be run using [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

First the current model has to be downloaded using the script `download_model.sh`:
```bash
./download_model.sh
```
After that the model file has to be moved to the `src` folder:

```bash
mv weather_model.pkl ./src/weather_model.pkl
```

The weather monitor can be run in development mode using the `docker-compose-dev.yml` file. This file is configured to use the `Dockerfile` file in the root of the project. This means that the Docker image will be built locally instead of pulling the image from the GitHub Container Registry.

The following command can be used to run the weather monitor in development mode:
```bash
docker-compose -f docker-compose-dev.yml up -d --build --force-recreate --remove-orphans
```

## Run in development mode (Python)
Follow the steps from above apart from the last one. Instead of running the weather monitor in Docker, it can be run in Python. The following command can be used to run the weather monitor in development mode:

A minimum version of [Python 3.10](https://www.python.org/downloads/) is required to run the weather monitor.

> **Note**: The `requirements.txt` file has to be installed first. This can be done using the following command:
> ```bash
> pip install -r requirements.txt
> ```
> 
```bash
docker-compose -f docker-compose-dev.yml up -d influxdb
python3 src/app.py
```

This way we will only run the InfluxDB database in Docker and the rest of the application will be run in Python. This is useful if you want to make changes to the application and see the changes without rebuilding the Docker image every time.

# Logs
Logs can be viewed through the Docker container logs. The following command can be used to view the logs of the weather monitor container:
```bash
sudo docker logs -f fhnw-ds-cde1-wettermonitor-weather-monitor-1
```

You may have to replace `fhnw-ds-cde1-wettermonitor-weather-monitor-1` with the name of the container. The name of the container can be found using the following command:
```bash
sudo docker ps
```

The matching container name will be listed in the `NAMES` column of the container running under the `ghcr.io/fhnw-ivy/fhnw-ds-cde1-wettermonitor:main` image.

If you're running the weather monitor in development mode and with Python, the logs can be viewed in the execution terminal.

# Accessing the application
The dashboard can be locally accessed through the following URL: http://localhost:6540

Make sure that the port `6540` is not used by another application or instance running in order to avoid conflicts.

# Configuration
The configuration of the weather monitor can be done through the `example.env` file. The following options are available:

| Option               | Description                            | Default |
|----------------------|----------------------------------------| --- |
| `INFLUXDB_HOST`      | Hostname of the InfluxDB instance      | `influxdb` |
| `INFLUXDB_PORT`      | Port of the InfluxDB instance          | `8086` |
| `INFLUXDB_PASSWORD`  | Password used on the InfluxDB instance | `mysecretpassword` |

The example configuration must be copied to a `.env` file in order to utilize it. The `.env` file is ignored by Git and will not be committed to the repository. This is done to prevent the accidental commit of sensitive information. The `.env` file is also ignored by Docker Compose. This is done to prevent the accidental commit of sensitive information to the Docker image.

You can copy and edit the example configuration using the following command (Linux):
```bash
cp example.env .env
nano .env
```

> **Note**: This is necessary because the `docker-compose.yml` file is configured to use the `.env` file as configuration file.

After that the docker stack has to redeployed (if already running or not) using the following command:
```bash
sudo docker-compose up -d
```

# Updating the application
The application pulls the latest version of the Docker image from the GitHub Container Registry on every boot. This means that the application will automatically update to the latest version regularly.

This is done through the [Watchtower](https://containrrr.dev/watchtower/) Docker container. The Watchtower container will automatically update the Docker container running the weather monitor application as well as the InfluxDB container.

# How can I add a new weather station?
The weather monitor can be extended to support new weather stations. The following steps have to be done to add a new weather station:

1. Add the new weather station identifier (e.g. 'mythenquai') to the `stations` list within the `Config` class in the `src/weather_data.py` file.
2. Extend or create a new module with `src/weather_data.py` as a role model to fetch data from the data source that provides the weather data for the new weather station.
   1. Be sure to follow the structure of the InfluxDB when adding new data points. The structure of the InfluxDB can be found in the `src/weather_data.py` file.
3. Schedule the fetching of the new weather station data in the `src/app.py` file. The fetching of the data can be scheduled using the `schedule.every().hour.do(fetch_weather_data)` function. The `fetch_weather_data` is a placeholder for a function that can be found in the new or extended module created for that station.

If the data from the new data source and station is successfully fetched and stored in the InfluxDB, the weather monitor will automatically generate a new prediction and plot for the new weather station. The new weather station will also be available in the dashboard.

> **Note**: The weather monitor will only generate a new prediction and plot if the data for the new weather station is available in the InfluxDB. This means that the weather monitor will not generate a new prediction and plot for the new weather station if the data with the needed variables for the respective operation and new weather station is not available in the InfluxDB.

# Shutdown
The following command can be used to shut down the weather monitor in development mode (Docker):
```bash
docker-compose -f docker-compose-dev.yml down
```

If you're running the weather monitor in development mode and with Python, the weather monitor can be shut down by pressing `CTRL+C` in the execution terminal.

# Known issues
- Running the application outside Docker on a Windows machine is not supported. The application can be run using WSL on Windows.
  - This issue is related to the saving of plots on a Windows file system. The application will not be able to save the plots on a Windows file system. See function `save_plot` in `src/plotting.py`.
- 

# Future roadmap
- [ ] Add more stations
- [ ] Add more plots
- [ ] Artificial intelligence to predict the weather
- [ ] Add more data sources