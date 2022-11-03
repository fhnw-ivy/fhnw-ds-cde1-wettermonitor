import datetime
import enum
import os
import time

from pandas import DataFrame

import weather_data as wd

config = wd.Config()


def init() -> None:
    config.db_host = os.environ.get("INFLUXDB_HOST") if os.environ.get("INFLUXDB_HOST") else "localhost"
    config.db_port = int(os.environ.get("INFLUXDB_PORT")) if os.environ.get("INFLUXDB_PORT") else 8086
    print(f"DB config: host {config.db_host}, port {config.db_port}")

    try:
        wd.connect_db(config)
        print("DB connected")

        wd.import_csv_file(config=config, file_name="./data/messwerte_mythenquai_2022.csv",
                           station="mythenquai")
        print("CSV 'mythenquai' imported.")

        wd.import_csv_file(config=config, file_name="./data/messwerte_tiefenbrunnen_2022.csv",
                           station="tiefenbrunnen")
        print("CSV 'tiefenbrunnen' imported.")

        wd.import_latest_data(config, periodic_read=False)
        print("Latest data imported.")
    except:
        print("Weather repo init failed")

        print("Retrying in 3s...")
        time.sleep(3)

        init()


def import_latest_data_periodic() -> None:
    print("Periodic read starting")
    wd.import_latest_data(config, periodic_read=True)


def __create_query_date_string(date: datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_all_entries(station: str, start_time: datetime, stop_time: datetime = None) -> DataFrame | None:
    """
    Getting all entries form a specified time intervall and station
    Args:
        station: Station string
        start_time: < x
        stop_time:  > x
    """

    try:
        if not stop_time:
            query = f'SELECT * FROM {station} WHERE time > now() - {__create_query_date_string(start_time)}'

        else:
            query = f'SELECT * FROM {station} WHERE time >= \'{__create_query_date_string(start_time)}\' AND time <= \'{__create_query_date_string(stop_time)}\''

        return wd.execute_query(config=config, station=station, query=query)
    except Exception as e:
        print("get_all_entries entries failed.")

    return None


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
