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
