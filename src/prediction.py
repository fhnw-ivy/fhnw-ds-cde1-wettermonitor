import datetime
import logging
import pickle

import numpy as np
import pandas as pd
import schedule

import weather_repository as wr

logger = logging.getLogger("app")

predicted_measurements = [wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_direction, wr.Measurement.Air_temp]
prediction_cache = {}


def get_predictions(station, relative_datetime_labels=False):
    """
    Returns a dictionary of predictions for the given station. Cache is used if data has not changed since and cache is allowed.
    Args:
        station: The station to get predictions for
        relative_datetime_labels: If true, the keys of the dictionary will be absolute datetimes, otherwise they will be strings relative to NOW
    Returns: A list of dictionaries, each dictionary containing a key-value pair of the relative time and the prediction
    """
    query = wr.WeatherQuery(station, predicted_measurements)
    pred_data = wr.run_query(query)
    latest_data_datetime = pred_data.index[-1]

    cached_predictions = __get_cached_predictions(station, latest_data_datetime)
    if cached_predictions is not None:
        if relative_datetime_labels:
            return convert_labelled_predictions_to_relative_datetime(cached_predictions)
        else:
            return cached_predictions

    labelled_predictions = __predict(station, wind_speed_avg_10min_before=pred_data['wind_speed_avg_10min'],
                                     wind_direction_10min_before=pred_data['wind_direction'],
                                     air_temperature_10min_before=pred_data['air_temperature'],
                                     day=datetime.datetime.now().day, month=datetime.datetime.now().month,
                                     year=datetime.datetime.now().year, data_datetime=latest_data_datetime)

    prediction_cache[station] = labelled_predictions

    if relative_datetime_labels:
        return convert_labelled_predictions_to_relative_datetime(labelled_predictions)
    else:
        return labelled_predictions


def __get_cached_predictions(station, latest_data_datetime):
    """
    Returns the cached predictions for the given station if they are available and the data has not changed since.
    Args:
        station: The station to get predictions for
        latest_data_datetime: The latest datetime of the data
    Returns: The cached predictions if available, otherwise None
    """
    if station in prediction_cache:
        if list(prediction_cache[station][0].keys())[0] == latest_data_datetime:
            # Return copy of cached predictions
            return [prediction.copy() for prediction in prediction_cache[station]]

    return None


def __predict(station, air_temperature_10min_before, wind_speed_avg_10min_before,
              wind_direction_10min_before, day, month, year, data_datetime):
    """
    Predicts the wind speed, wind direction and air temperature for the next 60 minutes. The predictions are based on the given data.
    Args:
        station: The station to predict for
        air_temperature_10min_before:
        wind_speed_avg_10min_before:
        wind_direction_10min_before:
        day: The day of the prediction
        month: The month of the prediction
        year: The year of the prediction
        data_datetime: The datetime of the data provided

    Returns: A list of dictionaries, each dictionary containing a key-value pair of the relative time and the prediction

    """
    with open('./weather_model.pkl', 'rb') as f:
        model = pickle.load(f)

        pred_df = pd.DataFrame({
            'station': [__convert_station_to_int(station)],
            'air_temperature_10min_before': [air_temperature_10min_before[0]],
            'wind_speed_avg_10min_before': [wind_speed_avg_10min_before[0]],
            'wind_direction_10min_before': [wind_direction_10min_before[0]],
            'day': [day],
            'month': [month],
            'year': [year]
        })

        predictions = [[wind_speed_avg_10min_before[0], wind_direction_10min_before[0]]]
        labelled_predictions = [{data_datetime: [wind_speed_avg_10min_before[0], wind_direction_10min_before[0]]}]

        for i in range(0, 6):
            offset_time = (i + 1) * 10
            pred_df['wind_speed_avg_10min_before'] = predictions[i][0]
            pred_df['wind_direction_10min_before'] = predictions[i][1]
            prediction = model.predict(pred_df)[0].tolist()
            predictions.append(prediction)
            labelled_predictions.append({f"+{offset_time}'": np.round(prediction, 2)})

        return labelled_predictions


def __convert_station_to_int(station):
    return 0 if station == 'mythenquai' else 1


def convert_labelled_predictions_to_relative_datetime(labelled_predictions):
    """
    Converts the labelled predictions to a dictionary with relative datetime as keys. Omits the first prediction, as it is not a prediction.
    Args:
        labelled_predictions: The labelled predictions to convert
    Returns: A dictionary with relative datetime as keys and the predictions as values
    """
    first_prediction_datetime = list(labelled_predictions[0].keys())[0]
    return {first_prediction_datetime + datetime.timedelta(minutes=int(key[1:3])): value
            for prediction in labelled_predictions
            for key, value in prediction.items() if not isinstance(key, datetime.datetime) and key.startswith("+")}


def __predict_all_stations():
    logger.debug('Predicting all stations')
    for station in wr.get_stations():
        try:
            get_predictions(station)
            logger.debug(f'Predicted {station}')
        except Exception as e:
            logger.error(f'Error predicting station {station}: {e}')

    logger.debug('Done predicting all stations')


def init():
    __predict_all_stations()
    schedule.every(10).minutes.do(__predict_all_stations)
