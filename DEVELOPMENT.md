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

# Accessing the application
The dashboard can be accessed through the following URL: http://localhost:6540

# Configuration
The configuration of the weather monitor can be done through the `example.env` file. The following options are available:

| Option               | Description                            | Default |
|----------------------|----------------------------------------| --- |
| `INFLUXDB_HOST`      | Hostname of the InfluxDB instance      | `influxdb` |
| `INFLUXDB_PORT`      | Port of the InfluxDB instance          | `8086` |
| `INFLUXDB_PASSWORD`  | Password used on the InfluxDB instance | `mysecretpassword` |

The example configuration can be copied to a `.env` file using the following command:
```bash
cp example.env .env
```

This is necessary because the `docker-compose.yml` file is configured to use the `.env` file as configuration file.

After that the docker stack has to redeployed (if already running or not) using the following command:
```bash
sudo docker-compose up -d
```

# Updating the application

The application pulls the latest version of the Docker image from the GitHub Container Registry on every boot. This means that the application will automatically update to the latest version regularly.

This is done through the [Watchtower](https://containrrr.dev/watchtower/) Docker container. The Watchtower container will automatically update the Docker container running the weather monitor application as well as the InfluxDB container.

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

# Run in development mode

> **Note**: The scripts used are based on a Linux environment. They may not work on other operating systems. On Windows the scripts can be run using [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

First the current model has to be downloaded using the script `download_model.sh`:
```bash
./download_model.sh
```
After that the model file has to be moved to the `src` folder:

```bash
mv weather_model.pkl weather_model.pkl
```

The weather monitor can be run in development mode using the `docker-compose-dev.yml` file. This file is configured to use the `Dockerfile` file in the root of the project. This means that the Docker image will be built locally instead of pulling the image from the GitHub Container Registry.

The following command can be used to run the weather monitor in development mode:
```bash
docker-compose -f docker-compose-dev.yml up -d --build --force-recreate --remove-orphans
```

Alternatively only the InfluxDB container can be started and the weather monitor can be started with Python using the following command:
```bash
docker-compose -f docker-compose-dev.yml up -d influxdb
pip install -r requirements.txt
python3 src/app.py
```

## Shutdown
The following command can be used to shut down the weather monitor in development mode:
```bash
docker-compose -f docker-compose-dev.yml down
```

# Known issues
- Running the application outside Docker on a Windows machine is not supported. The application can be run using WSL on Windows.

# Future roadmap
- [ ] Add more stations
- [ ] Add more plots
- [ ] Artificial intelligence to predict the weather
- [ ] Add more data sources