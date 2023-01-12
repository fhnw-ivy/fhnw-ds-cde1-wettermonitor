import datetime
import enum
import logging
import os
import time

import requests

import weather_data as wd
from service_status import ServiceStatus

logger = logging.getLogger("app")

# Default config for the weather_data.py script
config = wd.Config()


class Measurement(enum.Enum):
    """
    Enum for the different measurements that can be queried from the database.
    The enum values are the names of the columns in the database.
    """
    Air_temp = "air_temperature"
    Water_temp = "water_temperature"
    Dew_point = "dew_point"
    Precipitation = "precipitation"
    Water_level = "water_level"
    Pressure = "barometric_pressure_qfe"
    Humidity = "humidity",
    Wind_direction = "wind_direction"
    Wind_force_avg_10min = "wind_force_avg_10min"
    Wind_gust_max_10min = "wind_gust_max_10min"
    Wind_speed_avg_10min = "wind_speed_avg_10min"
    Wind_chill = "windchill"
    Radiation = "global_radiation"


# Unit mapping for the different measurements that can be queried from the database.
# The keys are the names of the columns in the database.
# Units taken from https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen (Section: "Attribute")
unit_mapping = {
    "air_temperature": "°C",
    "water_temperature": "°C",
    "dew_point": "°C",
    "precipitation": "mm",
    "water_level": "m",
    "barometric_pressure_qfe": "hPa",
    "humidity": "%",
    "wind_direction": "°",
    "wind_gust_max_10min": "m/s",
    "wind_speed_avg_10min": "m/s",
    "windchill": "°C",
    "global_radiation": "W/m²"
}


def get_unit(variable_name):
    """
    Returns the unit for the given variable name.
    Args:
        variable_name: The variable name to get the unit for. The variable name is the name of the column in the database.
    Returns: The unit for the given variable name.
    """
    return unit_mapping[variable_name]


class WeatherQuery:
    def __init__(self, station, measurements=None, start_time=None, stop_time=None):
        self.station = station
        self.measurements = measurements
        self.start_time = start_time
        self.stop_time = stop_time

    def create_query_string(self):
        """
        Creates the weather_query string for the weather_query.

        The measurement names are converted to the names of the columns in the database.

        Per default the weather_query will return the latest measurement for each measurement type if no start and stop time is given.
        Otherwise, the weather_query will return all measurements between the start and stop time.

        Returns: The weather_query string for the weather_query.
        """
        time_string = WeatherQuery.create_time_where_string(start_datetime=self.start_time,
                                                            stop_datetime=self.stop_time)
        has_time = time_string is not None

        query = f'SELECT {WeatherQuery.create_measurements_string(self.measurements) if self.measurements is not None else "*"} ' \
                f'FROM {self.station} ' \
                f'{("WHERE " + time_string) if has_time else "ORDER BY time DESC"}' \
                f'{" LIMIT 1" if not has_time else ""}'

        return query

    @staticmethod
    def create_date_string(date):
        """
        Creates a date string for the weather_query and given date.
        Args:
            date: The date to create the date string for.
        Returns: The date string for the weather_query and given date.
        """
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def create_time_where_string(start_datetime, stop_datetime):
        """
        Creates the time where string for the weather_query.
        If only one of the function parameters is given, the time where string will only contain the parameter that is given.
        Args:
            start_datetime: The start time of the weather_query. >= start_time
            stop_datetime: The stop time of the weather_query. <= stop_datetime

        Returns: The time 'where' string for the weather_query.
        """
        if not stop_datetime and not start_datetime:
            return None

        if not stop_datetime:
            return f'time > now() - {WeatherQuery.create_date_string(start_datetime)}'

        return f'time >= \'{WeatherQuery.create_date_string(start_datetime)}\' AND time <= \'{WeatherQuery.create_date_string(stop_datetime)}\''

    @staticmethod
    def create_measurements_string(measurements):
        """
        Creates the measurement string for the weather_query.
        Args:
            measurements: The measurements to create the measurement string for.
        Returns: The measurement string for the weather_query.
        """
        return ','.join(str(x.value) for x in measurements)


def download_latest_csv_files(station):
    """
    Downloads the latest CSV files from the weather station. If the download files, a fallback CSV file is used.
    Args:
        station: The station to download the CSV files for.

    Returns: None
    """
    # Template for the CSV file paths
    file_name = f"./csv/messwerte_{station}.csv"

    logger.info(f"Downloading latest CSV file for station {station}..")
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    url = f"https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_{station}_{datetime.datetime.now().year}.csv"
    r = requests.get(url, allow_redirects=True)

    if r.status_code == 200 and r.headers['Content-Type'] == 'text/csv':
        open(file_name, 'wb').write(r.content)
        logger.info(f"Downloaded latest CSV file for station {station} to {file_name}")
    else:
        logger.warning(f"Could not download latest CSV file for station {station}.")
        logger.warning(f"Status code: {r.status_code}")
        logger.warning(f"Using fallback CSV file for station {station}..")


def init():
    """
    Initializes the database connection and creates the database if it does not exist.
    Imports the CSV files into the database.
    Checks if additional data can be fetched from the API.

    Returns: None
    """
    config.db_host = os.environ.get("INFLUXDB_HOST") if os.environ.get("INFLUXDB_HOST") else "localhost"
    config.debug = int(os.environ.get("INFLUXDB_PORT")) if os.environ.get("INFLUXDB_PORT") else 8086
    logger.debug(f"DB config: host {config.db_host}, port {config.db_port}")

    wd.connect_db(config)
    logger.debug("DB connected")

    logger.debug("Starting CSV import..")

    # Import CSV files for each station
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
    # Ensure that the latest data from the API is available before starting the service is ready
    wd.import_latest_data(config=config, periodic_read=False)
    logger.debug("Periodic read finished.")


def import_latest_data_periodic():
    """
    Wrapper function for the periodic read of the latest data from the API of the weather_data.py script.
    Updates the service status accordingly.
    Restarts the periodic read if it fails.

    Returns: None
    """
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


def run_query(weather_query, convert_timezone=True, timezone="Europe/Zurich"):
    """
    Wrapper function for the query_string function of the weather_data.py script.
    Converts the timezone of the result if passed as parameter.

    Args:
        weather_query: The query_string object to run the query_string for.
        convert_timezone: Whether to convert the timezone of the data or not.
        timezone: The timezone to convert the data to.

    Returns: The result of the query_string as a DataFrame or None if the query_string failed.
    """
    try:
        df = wd.execute_query(config=config, station=weather_query.station,
                              query_string=weather_query.create_query_string())

        # Convert DF index to specified timezone if requested
        if df is not None and convert_timezone and timezone is not None:
            df.index = df.index.tz_convert(timezone)

        return df
    except Exception as e:
        logger.error("run_query failed.")
        logger.error(e)

    return None


def get_stations():
    """
    Returns the stations that are available in the database.
    Returns: The stations that are available in the database.
    """
    return config.stations


def health_check():
    """
    Runs a weather_query on the database connection to check if the database is available and data can be retrieved.
    Updated the service status accordingly.

    Returns: Boolean indicating if the database is available.
    """
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
