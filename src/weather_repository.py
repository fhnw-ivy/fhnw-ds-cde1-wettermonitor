import datetime
import enum
import os

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


def init():
    config.db_host = os.environ.get("INFLUXDB_HOST") if os.environ.get("INFLUXDB_HOST") else "localhost"
    config.db_port = int(os.environ.get("INFLUXDB_PORT")) if os.environ.get("INFLUXDB_PORT") else 8086
    wd.connect_db(config)

    try:
        wd.import_csv_file(config=config, file_name="./data/messwerte_mythenquai_2022.csv",
                           station="mythenquai")

        wd.import_csv_file(config=config, file_name="./data/messwerte_tiefenbrunnen_2022.csv",
                           station="tiefenbrunnen")
    except:
        raise Exception("CSV import failed")

    wd.import_latest_data(config, periodic_read=False)


def import_latest_data_periodic():
    print("Periodic read starting")
    wd.import_latest_data(config, periodic_read=True)


def get_all_entries(station: str, start_time: datetime, stop_time: datetime = None):
    try:
        return wd.get_entries(config=config, station=station, start_time=start_time, stop_time=stop_time)
    except:
        print("get_all_entries entries failed")

    return None
