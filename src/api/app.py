from flask import Flask, jsonify, request

import json
import weatherdata

app = Flask(__name__)
weather_config = None


@app.route('/weather/stations', methods=['GET'])
def get_weather_stations():
    return jsonify(weather_config.stations), 200


@app.route('/weather/latest', methods=['GET'])
def get_latest_weather_entry():
    station = request.args.get('station')
    if not station:
        return "No station provided", 404

    try:
        latest_entry = weatherdata.__get_last_db_entry(weather_config, station)
        return df_2_json(latest_entry), 200
    except:
        print("Error while getting latest db entry")

    return "There was an error while communicating with the DB", 500


def df_2_json(df):
    return json.loads(df.to_json(orient="index"))


def init_db(db_config):
    weatherdata.connect_db(config=db_config)
    weatherdata.clean_db(config=db_config)

    weatherdata.import_csv_file(config=db_config, file_name="../../data/csv/messwerte_mythenquai_2022.csv",
                                station="mythenquai")
    weatherdata.import_csv_file(config=db_config, file_name="../../data/csv/messwerte_tiefenbrunnen_2022.csv",
                                station="tiefenbrunnen")


if __name__ == '__main__':
    weather_config = weatherdata.Config()
    init_db(weather_config)

    app.run(host='0.0.0.0', port=6540, debug=True)
