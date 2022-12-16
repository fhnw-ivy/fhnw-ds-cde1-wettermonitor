import pickle
import pandas as pd
import numpy as np

def getPredictionFor(station: str, air_temperature_10min_before: float, wind_speed_avg_10min_before: float, wind_direction_10min_before: float, day: int, month: int, year: int):
    with open('../prediction/weather_model.pkl', 'rb') as f:
        model = pickle.load(f)

        pred_df = pd.DataFrame({
            'station': [convertStationToInt(station)],
            'air_temperature_10min_before': [air_temperature_10min_before[0]],
            'wind_speed_avg_10min_before': [wind_speed_avg_10min_before[0]],
            'wind_direction_10min_before': [wind_direction_10min_before[0]],
            'day': [day],
            'month': [month],
            'year': [year]
        })

        predictions = [[wind_speed_avg_10min_before[0], wind_direction_10min_before[0]]]
        labelled_predictions = [{ "NOW":[wind_speed_avg_10min_before[0], wind_direction_10min_before[0]]}]

        for i in range(0, 6):
            offset_time = (i+1)*10
            pred_df['wind_speed_avg_10min_before'] = predictions[i][0]
            pred_df['wind_direction_10min_before'] = predictions[i][1]
            prediction = model.predict(pred_df)[0].tolist()
            predictions.append(prediction)
            labelled_predictions.append({f"+{offset_time}'":np.round(prediction, 2)})

        return labelled_predictions

def convertStationToInt(station: str):
    return 0 if station == 'mythenquai' else 1