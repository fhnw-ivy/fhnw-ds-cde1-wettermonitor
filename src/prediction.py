import datetime
import logging
import pickle

import numpy as np
import pandas as pd
import schedule

logger = logging.getLogger("app")

import weather_repository as wr

prediction_cache = {}


def get_cached_predictions(station: str):
    if station in prediction_cache:
        if (datetime.datetime.now() - prediction_cache[station][1]).seconds < 600:
            return prediction_cache[station][0]
    return None


def get_predictions(station: str, air_temperature_10min_before: float, wind_speed_avg_10min_before: float,
                    wind_direction_10min_before: float, day: int, month: int, year: int):
    with open('./weather_model.pkl', 'rb') as f:
        model = pickle.load(f)

        pred_df = pd.DataFrame({
            'station': [convert_station_to_int(station)],
            'air_temperature_10min_before': [air_temperature_10min_before[0]],
            'wind_speed_avg_10min_before': [wind_speed_avg_10min_before[0]],
            'wind_direction_10min_before': [wind_direction_10min_before[0]],
            'day': [day],
            'month': [month],
            'year': [year]
        })

        predictions = [[wind_speed_avg_10min_before[0], wind_direction_10min_before[0]]]
        labelled_predictions = [{"NOW": [wind_speed_avg_10min_before[0], wind_direction_10min_before[0]]}]

        for i in range(0, 6):
            offset_time = (i + 1) * 10
            pred_df['wind_speed_avg_10min_before'] = predictions[i][0]
            pred_df['wind_direction_10min_before'] = predictions[i][1]
            prediction = model.predict(pred_df)[0].tolist()
            predictions.append(prediction)
            labelled_predictions.append({f"+{offset_time}'": np.round(prediction, 2)})

        prediction_cache[station] = (labelled_predictions, datetime.datetime.now())
        return labelled_predictions


def convert_station_to_int(station: str):
    return 0 if station == 'mythenquai' else 1


def convert_labelled_predictions_to_relative_datetime(labelled_predictions, reference_datetime, value_index=None):
    return {reference_datetime + datetime.timedelta(minutes=int(key[1:3])): value[value_index] if value_index is not None else value
            for prediction in labelled_predictions
            for key, value in prediction.items() if key != 'NOW'}

def predict_all_stations():
    measurements = [wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_direction, wr.Measurement.Air_temp]

    logger.debug('Predicting all stations')
    for station in wr.get_stations():
        try:
            query = wr.WeatherQuery(station, measurements)
            pred_data = wr.run_query(query)

            get_predictions(station, wind_speed_avg_10min_before=pred_data['wind_speed_avg_10min'],
                            wind_direction_10min_before=pred_data['wind_direction'],
                            air_temperature_10min_before=pred_data['air_temperature'],
                            day=datetime.datetime.now().day, month=datetime.datetime.now().month,
                            year=datetime.datetime.now().year)

            logger.debug(f'Predicted {station}')
        except Exception as e:
            logger.error(f'Error predicting station {station}: {e}')

    logger.debug('Done predicting all stations')


def init():
    predict_all_stations()

    schedule.every(10).minutes.do(predict_all_stations)
