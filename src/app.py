import datetime
import threading
import time

import schedule as schedule
from flask import Flask, redirect, render_template

import weather_repository as wr
import plotting as plt

app = Flask(__name__)
service_ready = False

loading_template = "loading.html"


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

    return render_template('index.html', subpage="base", station=station, data=weather_data, refresh_interval=60)


@app.route("/weatherstation/<station>/plots/<plot_name>")
def plots(station: str, plot_name: str):
    if not service_ready:
        return render_template(loading_template)

    return render_template(f'plots/{station}_{plot_name}.html')


def job_watcher():
    print("Checking for pending jobs...")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=6540, debug=True, use_reloader=False)).start()

    # Weather repository
    while not service_ready:
        try:
            wr.init()

            print("Service is ready.")
            service_ready = True
        except Exception as e:
            print("Weather repo init failed. Retrying in 3s...")
            print(e)
            time.sleep(3)

    threading.Thread(target=wr.import_latest_data_periodic).start()

    # Plotting
    plt.init()

    job_watcher()
    print("Application finished.")
