import threading

from flask import Flask, redirect
import weather_repository as wr

app = Flask(__name__)


@app.route('/')
@app.route('/wetterstation')
def index():
    return redirect("/wetterstation/tiefenbrunnen")


@app.route("/wetterstation/<station>")
def wetterstation(station: str):
    if not wr.data_initialized:
        return "Service not ready"

    return station


if __name__ == '__main__':
    # Weather repository
    wr.init()
    threading.Thread(target=wr.import_latest_data_periodic).start()

    app.run(host='0.0.0.0', port=6540, debug=True)
