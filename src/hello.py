from flask import Flask
import weatherdata

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello world!"


def init_db(db_config):
    weatherdata.connect_db(config=db_config)
    weatherdata.clean_db(config=db_config)


if __name__ == '__main__':
    init_db(weatherdata.Config())
    app.run(debug=True)
