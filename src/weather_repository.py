import datetime
import enum
import os
import time
from builtins import str

from pandas import DataFrame

import weather_data as wd
from src import plotting


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
    plotting.generate_last_week_plots()

    try:
        print("Periodic read started.")
        wd.import_latest_data(config, periodic_read=True)
        print("Periodic read finished.")

    except Exception as e:
        print("Periodic read failed.")
        print(e)

    print("Restarting periodic read in 3s..")
    time.sleep(3)

    import_latest_data_periodic()


def run_query(query: WeatherQuery) -> DataFrame | None:
    try:
        return wd.execute_query(config=config, station=query.station, query=query.create_query_string())
    except Exception as e:
        print("run_query failed.")
        print(e)

    pass
