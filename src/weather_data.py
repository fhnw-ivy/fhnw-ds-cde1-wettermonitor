""" Weather Data Collector for Influxdb

This script allows the user to interact with weather data gathered
from city Zurich. See
https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen
for further information. The data can be stored in an influxdb, which is
required to be running before using the functions defined in this file. This
script requires influxdb version 1.8 or lower and is not compatible with
influxdb 2.0 and higher.

Authors:
Fabian Märki, Jelle Schutter, Lucas Brönnimann

Last Update:
2022-10-16
"""

import json
import logging
import os
import signal
import sys
import threading
from datetime import datetime, timedelta
from time import sleep

import numpy as np
import pandas as pd
import requests
from influxdb import DataFrameClient
from pandas import json_normalize
from requests.exceptions import ConnectionError

logger = logging.getLogger("app")


class Config:
    db_host = 'localhost'
    db_port = 8086
    db_name = 'meteorology'
    stations = ['mythenquai', 'tiefenbrunnen']
    stations_force_query_last_entry = False
    stations_last_entries = {}
    keys_mapping = {
        'timestamp': 'timestamp',
        'values.air_temperature.value': 'air_temperature',
        'values.barometric_pressure_qfe.value': 'barometric_pressure_qfe',
        'values.dew_point.value': 'dew_point',
        'values.global_radiation.value': 'global_radiation',
        'values.humidity.value': 'humidity',
        'values.precipitation.value': 'precipitation',
        'values.water_temperature.value': 'water_temperature',
        'values.wind_direction.value': 'wind_direction',
        'values.wind_force_avg_10min.value': 'wind_force_avg_10min',
        'values.wind_gust_max_10min.value': 'wind_gust_max_10min',
        'values.wind_speed_avg_10min.value': 'wind_speed_avg_10min',
        'values.windchill.value': 'windchill'
    }
    historic_data_chunksize = 10000
    client = None

def connect_db(config):
    """Connects to the database and initializes the client

    Parameters:
    config (Config): The Config containing the DB connection info

   """
    if config.client is None:
        # https://www.influxdata.com/blog/getting-started-python-influxdb/
        config.client = DataFrameClient(host=config.db_host,
                                        port=config.db_port)
        config.client.create_database(config.db_name)
        config.client.switch_database(config.db_name)


def execute_query(config, station, query_string):
    """
    Executes a given weather_query related to a specific weather station that is within the config
    Args:
        config: DB config
        station: Station from the weather config
        query_string: Influx weather_query string

    Returns: None in case of error or empty set or pandas DataFrame with data
    """

    if station not in config.stations:
        logger.info("Station not found")
        return None

    try:
        logger.debug(f"Query: {query_string}")
        result = config.client.query(query_string, database=config.db_name)
        df = result.get(station, None)
        return df

    except Exception as e:
        logger.error(f"Query '{query_string}' failed. Exception: {e}")

    return None


def clean_db(config):
    """Drops the whole database and creates it again

    Parameters:
    config (Config): The Config containing the DB connection info

   """
    config.client.drop_database(config.db_name)
    config.client.create_database(config.db_name)
    config.stations_last_entries.clear()


def import_csv_file(config, station, file_name):
    """Imports data from a .csv file

    Parameters:
    config (Config): The Config containing the DB connection info
    station (String): Either 'Mythenquai' or 'Tiefenbrunnen'
    file_name (String): Path to the file from which the data shall be imported

   """
    if os.path.isfile(file_name):
        logger.debug('\tLoad ' + file_name)
        for chunk in pd.read_csv(file_name, delimiter=',',
                                 chunksize=config.historic_data_chunksize):
            chunk = __define_types(chunk, '%Y-%m-%dT%H:%M:%S')
            logger.debug('Add ' + station + ' from ' + str(
                chunk.index[0]) + ' to ' + str(chunk.index[-1]))
            __add_data_to_db(config, chunk, station)
    else:
        logger.info(file_name + ' does not seem to exist.')


def import_latest_data(config, periodic_read=False):
    """Reads the latest data from the Wasserschutzpolizei Zurich weather API

    Parameters:
    config (Config): The Config containing the DB connection info
    periodic_read (bool): Defines if the function should keep reading after it
    imported the latest data (blocking through a sleep)

   """
    # access API for current data
    current_time = datetime.utcnow() + timedelta(hours=1)
    current_day = current_time.replace(hour=0, minute=0, second=0,
                                       microsecond=0)
    last_db_days = [current_day] * len(config.stations)

    for idx, station in enumerate(config.stations):
        last_db_entry = __get_last_db_entry(config, station)
        last_db_days[idx] = __extract_last_db_day(last_db_entry, station,
                                                  last_db_days[
                                                      idx]) + timedelta(hours=1)

    if periodic_read and threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, __signal_handler)
        logger.debug('\nPress Ctrl+C to stop!\n')
    check_db_day = min(last_db_days)
    check_db_day = check_db_day.replace(hour=0, minute=0, second=0,
                                        microsecond=0)

    first_cycle = True
    last_cycle = False

    while True:
        # check if all historic data (retrieved from API) has been processed
        if (not first_cycle and periodic_read and check_db_day >= current_day
                and not first_cycle):
            # once every 10 Min
            current_time = datetime.utcnow() + timedelta(hours=1)
            sleep_until = current_time + timedelta(minutes=10)
            # once per day
            # sleep_until = current_time + timedelta(days = 1)
            # sleep_until = sleep_until.replace(hour=6, minute=0, second=0,
            #                                  microsecond=0)
            sleep_sec = (sleep_until - current_time).total_seconds()

            logger.debug('Sleep for ' + str(sleep_sec) + 's (from ' + str(
                current_time) + ' until ' + str(
                sleep_until) + ') when next data will be queried.')
            sleep(sleep_sec)
            current_day = current_time.replace(hour=0, minute=0, second=0,
                                               microsecond=0)

        if not periodic_read and check_db_day >= current_day:
            if last_cycle:
                return
            last_cycle = True

        for idx, station in enumerate(config.stations):
            if last_db_days[idx].replace(hour=0, minute=0, second=0,
                                         microsecond=0) > check_db_day:
                continue
            last_db_entry = __get_last_db_entry(config, station)
            last_db_days[idx] = __extract_last_db_day(last_db_entry, station,
                                                      last_db_days[idx])
            data_of_last_db_day = __get_data_of_day(check_db_day, station)

            normalized_data = __clean_data(config, data_of_last_db_day,
                                           last_db_entry, station)

            if normalized_data.size > 0:
                __add_data_to_db(config, normalized_data, station)
                logger.debug('Handle ' + station + ' from ' + str(
                    normalized_data.index[0]) + ' to ' + str(
                    normalized_data.index[-1]))
            else:
                logger.debug('No new data received for ' + station)

        if check_db_day < current_day:
            check_db_day = check_db_day + pd.DateOffset(1)
        elif periodic_read and check_db_day >= current_day:
            check_db_day = datetime.utcnow() + timedelta(hours=1)

        if first_cycle:
            first_cycle = False


def __set_last_db_entry(config, station, entry):
    current_last_time = __extract_last_db_day(
        config.stations_last_entries.get(station, None), station, None)
    entry_time = __extract_last_db_day(entry, station, None)

    if current_last_time is None and entry_time is not None:
        config.stations_last_entries[station] = entry
    elif (current_last_time is not None and entry_time is not None and
          current_last_time < entry_time):
        config.stations_last_entries[station] = entry


def __get_last_db_entry(config, station):
    last_entry = None
    if not config.stations_force_query_last_entry:
        # speedup for Raspberry Pi - last entry weather_query takes > 2 Sec.!
        last_entry = config.stations_last_entries.get(station, None)

    if last_entry is None:
        try:
            # we are only interested in time, however need to provide any field
            # to make weather_query work
            query = (f'SELECT air_temperature FROM {station} ORDER BY time '
                     f'DESC LIMIT 1')
            last_entry = config.client.query(query)
        except:
            # There are influxDB versions which have an issue with above weather_query
            logger.error(
                'An exception occurred while querying last entry from DB for ',
                station, '. Try alternative approach.')
            query = f'SELECT * FROM {station} ORDER BY time DESC LIMIT 1'
            last_entry = config.client.query(query)

    __set_last_db_entry(config, station, last_entry)
    return last_entry


def __extract_last_db_day(last_entry, station, default_last_db_day):
    if last_entry is not None:
        val = None
        if isinstance(last_entry, pd.DataFrame):
            val = last_entry
        elif isinstance(last_entry, dict):
            val = last_entry.get(station, None)

        if val is not None:
            if not val.index.empty:
                return val.index[0].replace(tzinfo=None)

    return default_last_db_day


def __get_data_of_day(day, station):
    # convert to local time of station
    base_url = 'https://tecdottir.herokuapp.com/measurements/{}'
    day_str = day.strftime('%Y-%m-%d')
    end_date = day + timedelta(days=1)
    end_day_str = end_date.strftime('%Y-%m-%d')
    logger.debug('Query ' + station + ' at ' + day_str)
    payload = {
        'startDate': day_str,
        'endDate': end_day_str
    }
    url = base_url.format(station)
    while True:
        try:
            response = requests.get(url, params=payload)
            if response.ok:
                j_data = json.loads(response.content)
                return j_data
            else:
                response.raise_for_status()
                break
        except ConnectionError as e:
            logger.error(f"Request for '{e.request.url}' failed."
                         f"({e.args[0].args[0]})\nTrying again in 10 seconds...")
            sleep(10)


def __define_types(data, date_format):
    """Description:
    renames timestamp column,
    set timestamp to index  column,
    replace empty elements with 0,
    set datatype of all columns (except timestamp) to float64
    """
    del date_format
    if not data.empty:  # data is not empty
        if 'timestamp_cet' in data:
            data.drop('timestamp_cet', axis=1, inplace=True)
        if 'timestamp_utc' in data:
            data.rename(columns={"timestamp_utc": "timestamp"}, inplace=True)
        data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
        # set "timestamp" as the index column and delete the old index column
        data.set_index('timestamp', inplace=True)

    # replace al the missing values (represented as .) with a 0
    data.replace('.', 0,
                 inplace=True)
    for column in data.columns[0:]:  # iterate through all columns
        if column != 'timestamp':  # not the timestamp column
            data[column] = data[column].astype(
                np.float64)  # set datatype to float

    return data


def __clean_data(config, data_of_last_day, last_db_entry, station):
    normalized = json_normalize(data_of_last_day['result'])

    for column in normalized.columns[0:]:
        mapping = config.keys_mapping.get(column, None)
        if mapping is not None:
            normalized[mapping] = normalized[column]
        if mapping != column:
            normalized.drop(columns=column, inplace=True)

    normalized = __define_types(normalized, '%d.%m.%Y %H:%M:%S')

    # remove all entries older than last element
    last_db_entry_time = None
    if isinstance(last_db_entry, pd.DataFrame):
        last_db_entry_time = last_db_entry
    elif isinstance(last_db_entry, dict):
        last_db_entry_time = last_db_entry.get(station, None)
    last_db_entry_time = last_db_entry_time.index[0]
    normalized.drop(normalized[normalized.index <= last_db_entry_time].index,
                    inplace=True)

    return normalized


def __add_data_to_db(config, data, station):
    config.client.write_points(data, station, time_precision='s',
                               database=config.db_name)
    __set_last_db_entry(config, station, data.tail(1))


def __signal_handler(sig, frame):
    del sig
    del frame
    sys.exit(0)
