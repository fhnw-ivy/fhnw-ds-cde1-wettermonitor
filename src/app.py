import os
import threading
import time

import pandas as pd

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
default_plot_type = "wind_speed_with_predictions"


@app.before_request
def before_request():
    if not service_ready:
        return render_template(loading_template)


@app.route('/')
@app.route('/weatherstation')
def index():
    return redirect("/weatherstation/tiefenbrunnen")


@app.route("/weatherstation/<station>")
def wetterstation(station: str):
    weather_data = pd.DataFrame()
    try:
        weather_query = wr.WeatherQuery(station=station)
        weather_data = wr.run_query(weather_query)

        if weather_data is None:
            weather_data = pd.DataFrame()
    except Exception as e:
        logger.error(f"Error while loading data: {e}")

    return render_template('index.html', subpage="station", station=station, data=weather_data,
                           station_list=wr.get_stations(), status=ServiceStatus.get_status(),
                           refresh_interval=default_refresh_interval)


@app.route('/weatherstation/<station>/plots')
def plots_index(station: str):
    return redirect(f"/weatherstation/{station}/plots/{default_plot_type}")


@app.route("/weatherstation/<station>/plots/<plot_type>")
def plots(station: str, plot_type: str):
    return render_template('index.html', subpage="plots", station=station, plot_type=plot_type,
                           status=ServiceStatus.get_status(), refresh_interval=default_refresh_interval,
                           station_list=wr.get_stations())


@app.route("/weatherstation/<station>/predictions")
def predictions(station: str):
    prediction_data = []
    try:
        prediction_data = pred.get_predictions(station)
    except Exception as e:
        logger.error(f"Error while loading data: {e}")

    return render_template('index.html', subpage="prediction", station=station, prediction=prediction_data,
                           station_list=wr.get_stations(), status=ServiceStatus.get_status(),
                           refresh_interval=default_refresh_interval)


def job_watcher():
    logger.info("Checking for pending jobs...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error while running job: {e}")


if __name__ == '__main__':
    threads = []

    while not service_ready:
        try:
            # Flask
            flask_thread = threading.Thread(
                target=lambda: app.run(host='0.0.0.0', port=6540, debug=is_development, use_reloader=False,
                                       threaded=True))
            threads.append(flask_thread)
            flask_thread.start()

            # Weather repository
            wr.init()

            # Prediction
            pred.init()

            # Plotting
            plt.init()

            # Start periodic data read
            periodic_read_thread = threading.Thread(target=wr.import_latest_data_periodic)
            threads.append(periodic_read_thread)
            periodic_read_thread.start()

            # Schedule health check
            wr.health_check()
            schedule.every(default_refresh_interval).seconds.do(wr.health_check)

            logger.info("Service is ready.")
            service_ready = True
        except Exception as e:
            logger.error("Service init failed. Retrying in 3s...")
            logger.error(e)
            time.sleep(3)

    job_watcher()
    logger.info("Application finished.")
