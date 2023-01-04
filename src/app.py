import datetime
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
index_template = "index.html"
loading_template = "loading.html"
default_refresh_interval = 60
default_station = wr.get_stations()[0]
default_plot_type = "wind_speed_with_predictions"
show_current = ['air_temperature', 'water_temperature', 'barometric_pressure_qfe', 'humidity', 'windchill']


def convert_to_datetime_string(dt):
    """
    Converts a datetime object to a string for the template
    Args:
        dt: Datetime object

    Returns: String representation of the datetime object
    """

    if dt.date() == datetime.datetime.now().date():
        return dt.strftime("%H:%M")
    else:
        return dt.strftime("%d.%m.%Y %H:%M")

def get_sanitized_service_status():
    """
    Returns the service status in a format that can be used in the template
    Returns: Well formatted service status
    """
    is_live, last_fetch = ServiceStatus.get_status()
    return [is_live, convert_to_datetime_string(last_fetch)]

@app.before_request
def before_request():
    if not service_ready:
        return render_template(loading_template)


@app.route('/')
@app.route('/weatherstation')
def index():
    return redirect(f"/weatherstation/{default_station}")


@app.route("/weatherstation/<station>")
def wetterstation(station: str):
    # Dashboard data (Current weather)
    weather_data = pd.DataFrame()
    try:
        weather_query = wr.WeatherQuery(station=station)
        weather_data = wr.run_query(weather_query)

        if weather_data is None:
            weather_data = pd.DataFrame()
    except Exception as e:
        logger.error(f"Error while loading dashboard data: {e}")

    # Prediction data
    prediction_data = []
    try:
        prediction_data = pred.get_predictions(station)

        # Replace datetime of first prediction with datetime string
        prediction_data[0] = {convert_to_datetime_string(list(prediction_data[0].keys())[0]): list(prediction_data[0].values())[0]}

    except Exception as e:
        logger.error(f"Error while loading prediction data: {e}")

    current_data = {}
    for variable in show_current:
        current_data[variable] = {
                                    "name": variable.replace("_", " ").title(),
                                    "value": weather_data[variable].iloc[-1],
                                    "unit": wr.get_unit(variable)
                                 }

        # Round all numbers to 2 decimal places
        if isinstance(current_data[variable]["value"], float):
            current_data[variable]["value"] = round(current_data[variable]["value"], 2)

    return render_template(index_template, subpage="station", station=station, plot_list=plt.get_plots(), data=weather_data,
                           prediction=prediction_data, station_list=wr.get_stations(), status=get_sanitized_service_status(),
                           refresh_interval=default_refresh_interval, current_list=current_data)

@app.route("/weatherstation/<station>/plots/<plot_type>")
def plot(station: str, plot_type: str):
    return render_template(index_template, subpage="plot", station=station, plot_list=plt.get_plots(), station_list=wr.get_stations(), status=get_sanitized_service_status(),
                           refresh_interval=default_refresh_interval, plot_type=plot_type)

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
