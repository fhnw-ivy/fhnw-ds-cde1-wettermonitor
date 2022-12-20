import datetime
import os
import threading
import time

from service_status import ServiceStatus

is_development = os.environ.get("ENVIRONMENT") == "development"

import schedule as schedule
from flask import Flask, redirect, render_template

import weather_repository as wr
import plotting as plt
import prediction as pred

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] - [%(levelname)s] - [%(module)s] - [%(threadName)s] : %(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

logger = logging.getLogger("app")
logger.info("Starting app")

app = Flask(__name__)
service_ready = False
loading_template = "loading.html"
default_refresh_interval = 10
default_station = wr.get_stations()[0]


@app.route('/')
@app.route('/weatherstation')
def index():
    return redirect("/weatherstation/tiefenbrunnen")


@app.route("/weatherstation/<station>")
def wetterstation(station: str):
    if not service_ready:
        return render_template(loading_template)

    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    measurements = [wr.Measurement.Humidity, wr.Measurement.Pressure, wr.Measurement.Air_temp]

    weather_query = wr.WeatherQuery(station=station, measurements=measurements)
    weather_data = wr.run_query(weather_query)

    return render_template('index.html', subpage="station", station=station, data=weather_data,
                           station_list=wr.get_stations(), status=ServiceStatus.get_status(),
                           refresh_interval=default_refresh_interval)


@app.route('/weatherstation/<station>/plots')
def plots_index(station: str):
    return redirect(f"/weatherstation/{station}/plots/wind_speed")


@app.route("/weatherstation/<station>/plots/<plot_type>")
def plots(station: str, plot_type: str):
    if not service_ready:
        return render_template(loading_template)

    return render_template('index.html', subpage="plots", station=station, plot_type=plot_type,
                           status=ServiceStatus.get_status(), refresh_interval=default_refresh_interval,
                           station_list=wr.get_stations())


@app.route("/weatherstation/<station>/predictions")
def predictions(station: str):
    if not service_ready:
        return render_template(loading_template)

    prediction_data = pred.get_cached_predictions(station)
    if prediction_data is None:
        measurements = [wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_direction, wr.Measurement.Air_temp]

        pred_query = wr.WeatherQuery(station=station, measurements=measurements)
        pred_data = wr.run_query(pred_query)

        prediction_data = pred.get_predictions(station, wind_speed_avg_10min_before=pred_data['wind_speed_avg_10min'],
                                               wind_direction_10min_before=pred_data['wind_direction'],
                                               air_temperature_10min_before=pred_data['air_temperature'],
                                               day=datetime.datetime.now().day, month=datetime.datetime.now().month,
                                               year=datetime.datetime.now().year)

    return render_template('index.html', subpage="prediction", station=station, prediction=prediction_data,
                           station_list=wr.get_stations(), status=ServiceStatus.get_status(),
                           refresh_interval=default_refresh_interval)


def job_watcher():
    logger.info("Checking for pending jobs...")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    threads = []
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=6540, debug=is_development, use_reloader=False, threaded=True))
    threads.append(flask_thread)
    flask_thread.start()

    # Weather repository
    while not service_ready:
        try:
            wr.init()

            logger.info("Service is ready.")
            service_ready = True
        except Exception as e:
            logger.error("Weather repo init failed. Retrying in 3s...")
            logger.error(e)
            time.sleep(3)

    periodic_read_thread = threading.Thread(target=wr.import_latest_data_periodic)
    threads.append(periodic_read_thread)
    periodic_read_thread.start()

    # Plotting
    plt.init()

    # Prediction
    pred.init()

    job_watcher()
    logger.info("Application finished.")
