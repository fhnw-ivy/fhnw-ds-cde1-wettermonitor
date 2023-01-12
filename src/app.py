import datetime
import logging
import os
import random
import threading
import time

import pandas as pd
import schedule as schedule
from flask import Flask, redirect, render_template

import plotting as plt
import prediction as pred
import weather_repository as wr
from service_status import ServiceStatus

is_development = os.environ.get("ENVIRONMENT") == "development"

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] - [%(levelname)s] - [%(module)s] - [%(threadName)s] : %(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

logger = logging.getLogger("app")
logger.info("Starting app...")

app = Flask(__name__)
service_ready = False
index_template = "index.html"
loading_template = "loading.html"
default_refresh_interval = 60
default_station = wr.get_stations()[0]
show_current = ['air_temperature', 'water_temperature', 'barometric_pressure_qfe', 'humidity', 'windchill']


def convert_to_datetime_string(date):
    """
    Converts a datetime object to a string for the template
    Args:
        date: Datetime object

    Returns: String representation of the datetime object
    """

    if date is None:
        return "Never"

    if date.date() == datetime.datetime.now().date():
        return date.strftime("%H:%M")
    else:
        return date.strftime("%d.%m.%Y %H:%M")


def get_sanitized_service_status():
    """
    Returns the service status in a format that can be used in the template
    Returns: Well formatted service status
    """
    is_live, last_fetch = ServiceStatus.get_status()
    return [is_live, convert_to_datetime_string(last_fetch)]


def get_shuffled_plots():
    """
    Returns a shuffled list of all plots in order to randomize the order of the plots shown in the slider on the dashboard
    """
    return random.sample(plt.get_plots(), len(plt.get_plots()))


@app.before_request
def before_request():
    """
    Checks if the service is ready to serve requests
    Returns: Redirect to loading page if service is not ready
    """
    if not service_ready:
        return render_template(loading_template)


@app.route('/')
@app.route('/weatherstation')
def index():
    return redirect(f"/weatherstation/{default_station}")


@app.route("/weatherstation/<station>")
def weatherstation_station(station):
    # Dashboard data (Current weather)
    weather_data = pd.DataFrame()
    try:
        weather_query = wr.WeatherQuery(station=station)
        weather_data = wr.run_query(weather_query)

        if weather_data is None:
            weather_data = pd.DataFrame()
    except Exception as error:
        logger.error(f"Error while loading dashboard data: {error}")

    # Prediction data
    prediction_data = []
    try:
        prediction_data = pred.get_predictions(station)

        # Replace datetime of first prediction with datetime string
        prediction_data[0] = {
            convert_to_datetime_string(list(prediction_data[0].keys())[0]): list(prediction_data[0].values())[0]}

    except Exception as error:
        logger.error(f"Error while loading prediction data: {error}")

    current_data = {}
    if weather_data is not None and not weather_data.empty:
        for variable in show_current:
            current_data[variable] = {
                "name": variable.replace("_", " ").title(),
                "value": weather_data[variable].iloc[-1],
                "unit": wr.get_unit(variable)
            }

            # Round all numbers to 2 decimal places
            if isinstance(current_data[variable]["value"], float):
                current_data[variable]["value"] = round(current_data[variable]["value"], 2)

    return render_template(index_template, subpage="station", station=station, plot_list=get_shuffled_plots(),
                           data=weather_data,
                           prediction=prediction_data, station_list=wr.get_stations(),
                           status=get_sanitized_service_status(),
                           refresh_interval=default_refresh_interval, current_list=current_data)


@app.route("/weatherstation/<station>/plots/<plot_type>")
def weatherstation_station_plots(station, plot_type):
    return render_template(index_template, subpage="plot", station=station, plot_list=get_shuffled_plots(),
                           station_list=wr.get_stations(), status=get_sanitized_service_status(),
                           refresh_interval=default_refresh_interval, plot_type=plot_type)


def job_watcher():
    logger.info("Checking for pending jobs...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as error:
            logger.error(f"Error while running job: {error}")


if __name__ == '__main__':
    threads = []

    try:
        # Flask
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=6540, debug=is_development, use_reloader=False,
                                   threaded=True))
        threads.append(flask_thread)
        flask_thread.start()
        logger.debug("Flask thread started.")

        # Weather repository
        wr.init()
        logger.debug("Weather repository initialized.")

        # Prediction
        pred.init()
        logger.debug("Prediction initialized.")

        # Plotting
        plt.init()
        logger.debug("Plotting initialized.")

        # Start periodic data read
        periodic_read_thread = threading.Thread(target=wr.import_latest_data_periodic)
        threads.append(periodic_read_thread)
        periodic_read_thread.start()
        logger.debug("Periodic data read started.")

        # Schedule health check
        wr.health_check()
        schedule.every(default_refresh_interval).seconds.do(wr.health_check)
        logger.debug("Health check scheduled.")

        logger.info("Service is ready.")
        service_ready = True

        job_watcher()
    except Exception as e:
        logger.error("App crashed.")
        logger.error(e)
    finally:
        logger.info("Application finished.")
