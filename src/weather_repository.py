import datetime
import enum
import logging
import os
import time
from builtins import str

import requests
from pandas import DataFrame

import weather_data as wd
from service_status import ServiceStatus

logger = logging.getLogger("app")


class Measurement(enum.Enum):
    Air_temp = "air_temperature"
    Water_temp = "water_temperature"
    Dew_point = "dew_point"
    Precipitation = "precipitation"
    Water_level = "water_level"
    Pressure = "barometric_pressure_qfe"
    Humidity = "humidity"
    Wind_direction = "wind_direction"
    Wind_force_avg_10min = "wind_force_avg_10min"
    Wind_gust_max_10min = "wind_gust_max_10min"
    Wind_speed_avg_10min = "wind_speed_avg_10min"
    Wind_chill = "windchill"
    Radiation = "global_radiation"


class WeatherQuery:
    def __init__(self, station: str, measurements: list[Measurement] = None, start_time: datetime = None,
                 stop_time: datetime = None):
        self.station = station
        self.measurements = measurements
        self.start_time = start_time
        self.stop_time = stop_time

    def create_query_string(self):

        time_string = WeatherQuery.create_time_where_string(start_time=self.start_time, stop_time=self.stop_time)
        has_time = time_string is not None

        query = f'SELECT {WeatherQuery.create_measurements_string(self.measurements) if self.measurements is not None else "*"} ' \
                f'FROM {self.station} ' \
                f'{("WHERE " + time_string) if has_time else "ORDER BY time DESC"} ' \
                f'{"LIMIT 1" if not has_time else ""}'

        return query

    @staticmethod
    def create_date_string(date: datetime) -> str:
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def create_time_where_string(start_time: datetime, stop_time: datetime = None):
        if not stop_time and not start_time:
            return None

        if not stop_time:
            return f'time > now() - {WeatherQuery.create_date_string(start_time)}'

        return f'time >= \'{WeatherQuery.create_date_string(start_time)}\' AND time <= \'{WeatherQuery.create_date_string(stop_time)}\''

    @staticmethod
    def create_measurements_string(measurements: list[Measurement]):
        return ','.join(str(x.value) for x in measurements)


config = wd.Config()


def download_latest_csv_files(station: str):
    """
    Downloads the latest CSV files from the weather station.
    Args:
        station: The station to download the CSV files for.

    Returns: None
    """
    file_name = f"./csv/messwerte_{station}.csv"
    if not os.path.exists(file_name) or os.path.getmtime(file_name) < time.time() - 604800:
        logger.info(f"Downloading latest CSV file for station {station}..")
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        url = f"https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_{station}_{datetime.datetime.now().year}.csv"
        r = requests.get(url, allow_redirects=True)
        open(file_name, 'wb').write(r.content)

        logger.info("Download latest CSV files finished for " + station)
    else:
        logger.info(f"CSV file for station {station} is up to date.")


def init() -> None:
    config.db_host = os.environ.get("INFLUXDB_HOST") if os.environ.get("INFLUXDB_HOST") else "localhost"
    config.debug = int(os.environ.get("INFLUXDB_PORT")) if os.environ.get("INFLUXDB_PORT") else 8086
    logger.debug(f"DB config: host {config.db_host}, port {config.db_port}")

    wd.connect_db(config)
    logger.debug("DB connected")

    logger.debug("Starting CSV import..")

    for station in config.stations:
        logger.info("Checking for latest CSV files started for " + station)
        try:
            download_latest_csv_files(station)
        except Exception as e:
            logger.error("Download latest CSV files failed for " + station)
            logger.error(e)

            # Use fallback data
            logger.info("Using fallback data..")

        wd.import_csv_file(config=config, file_name=f"./csv/messwerte_{station}.csv",
                           station=station)
        logger.debug(f"CSV '{station}' imported.")

    logger.debug("CSV import finished.")

    logger.debug("Starting periodic read..")
    # Ensure that the latest data is available before starting the service is ready
    wd.import_latest_data(config=config, periodic_read=False)
    logger.debug("Periodic read finished.")


def import_latest_data_periodic() -> None:
    try:
        logger.info("Periodic read started.")
        ServiceStatus.is_live = True

        wd.import_latest_data(config, periodic_read=True)
        logger.info("Periodic read finished.")

    except Exception as e:
        ServiceStatus.is_live = False
        logger.error("Periodic read failed.")
        logger.error(e)

    logger.debug("Restarting periodic read in 3s..")
    time.sleep(3)

    import_latest_data_periodic()


def run_query(query: WeatherQuery) -> DataFrame | None:
    try:
        return wd.execute_query(config=config, station=query.station, query=query.create_query_string())
    except Exception as e:
        logger.error("run_query failed.")
        logger.error(e)

    pass


def get_stations():
    return config.stations


def get_plots():
    return config.plots


def health_check():
    try:
        query = WeatherQuery(station=config.stations[0], measurements=[Measurement.Air_temp])
        data = run_query(query)

        if data is not None and len(data) > 0:
            ServiceStatus.last_fetch = data.index[-1]
            ServiceStatus.last_update = ServiceStatus.last_fetch
            ServiceStatus.is_live = True

            logger.debug("Health check successful.")
            return True

    except Exception as e:
        logger.error(e)

    logger.error("Health check failed.")
    ServiceStatus.is_live = False
    return False
