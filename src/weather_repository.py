import datetime
import enum
import os

from pandas import DataFrame

import weather_data as wd


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


config = wd.Config()


def init() -> None:
    config.db_host = os.environ.get("INFLUXDB_HOST") if os.environ.get("INFLUXDB_HOST") else "localhost"
    config.db_port = int(os.environ.get("INFLUXDB_PORT")) if os.environ.get("INFLUXDB_PORT") else 8086
    print(f"DB config: host {config.db_host}, port {config.db_port}")

    wd.connect_db(config)
    print("DB connected")

    for station in config.stations:
        wd.import_csv_file(config=config, file_name=f"../csv/messwerte_{station}_2022.csv",
                           station=station)
        print(f"CSV '{station}' imported.")

    wd.import_latest_data(config, periodic_read=False)
    print("Latest data imported.")


def import_latest_data_periodic() -> None:
    print("Periodic read starting")
    wd.import_latest_data(config, periodic_read=True)


def get_all(station: str, start_time: datetime, stop_time: datetime = None) -> DataFrame | None:
    """
    Getting all entries form a specified time intervall and station
    Args:
        station: Station string
        start_time: < x
        stop_time:  > x
    """
    try:
        query = f"SELECT * FROM {station} WHERE {__create_query_time_where_string(start_time=start_time, stop_time=stop_time)}"
        return wd.execute_query(config=config, station=station, query=query)
    except Exception as e:
        print("get_all failed.")

    return None


def get_measurements(station: str, measurements: list[Measurement], start_time: datetime,
                     stop_time: datetime = None) -> DataFrame | None:
    """
    Getting all entries form a specified time intervall and station
    Args:
        measurements:
        station: Station string
        start_time: < x
        stop_time:  > x
    """
    try:
        query = f"SELECT {__create_query_measurements_string(measurements)} FROM {station} WHERE {__create_query_time_where_string(start_time=start_time, stop_time=stop_time)}"
        return wd.execute_query(config=config, station=station, query=query)
    except Exception as e:
        print("get_measurements failed.")

    return None


def get_latest_measurements(station: str, measurements: list[Measurement]) -> DataFrame | None:
    try:
        query = f"SELECT {__create_query_measurements_string(measurements)} FROM {station} ORDER BY time DESC LIMIT 1"
        return wd.execute_query(config=config, station=station, query=query)
    except Exception as e:
        print("get_latest_measurements failed.")

    return None


def __create_query_date_string(date: datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def __create_query_time_where_string(start_time: datetime, stop_time: datetime = None):
    if not stop_time:
        return f'time > now() - {__create_query_date_string(start_time)}'

    return f'time >= \'{__create_query_date_string(start_time)}\' AND time <= \'{__create_query_date_string(stop_time)}\''


def __create_query_measurements_string(measurements: list[Measurement]):
    return ','.join(str(x.value) for x in measurements)
