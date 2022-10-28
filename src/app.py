import datetime
import threading

from flask import Flask, redirect, render_template

import weather_repository as wr

app = Flask(__name__)
service_ready = False


@app.route('/')
@app.route('/weatherstation')
def index():
    return redirect("/weatherstation/tiefenbrunnen")


@app.route("/weatherstation/<station>")
def wetterstation(station: str):
    if not service_ready:
        return "Service not ready"

    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_data = wr.get_all_entries(station=station, start_time=start_time, stop_time=stop_time)
    return render_template('index.html', subpage="base", station=station, data=weather_data, refresh_interval=10)


if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=6540, debug=True, use_reloader=False)).start()

    # Weather repository
    wr.init()
    service_ready = True

    threading.Thread(target=wr.import_latest_data_periodic).start()
