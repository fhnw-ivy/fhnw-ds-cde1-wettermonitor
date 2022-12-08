import datetime

import schedule

import logging
logging.basicConfig(
    filename="plotting.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p')

import weather_repository as wr
import plotly.express as px

plots_directory = "./templates/plots/"


# Generate plot for the past 24 hours for a given station and the wind speeds
def generate_wind_speed_plot_today(station: str):
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    measurements = [wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_gust_max_10min]

    weather_query = wr.WeatherQuery(station=station, measurements=measurements, start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    plot = px.line(weather_data, x="time", y=["wind_speed_avg_10min", "wind_gust_max_10min"],
                   title="Windgeschwindigkeit (10min Mittelwert und Spitzenwert) der letzten 24 Stunden für " + station,
                   labels={"value": "Windgeschwindigkeit (m/s)", "variable": "Messung", "time": "Zeit"},
                   template="plotly_dark")
    save_plot(plot, "wind_speed", station)


def save_plot(plot, plot_name, station):
    plot_file_name = f"{station}_{plot_name}.html"
    try:
        plot.write_html(f"{plots_directory}{plot_file_name}")
        logging.info(f"Saved plot {plot_name}.")
    except Exception as e:
        logging.error(f"Saving plot {plot_name} failed.")
        logging.error(e)


def generate_all_plots():
    for station in wr.get_stations():
        generate_wind_speed_plot_today(station)
        logging.info(f"Generated plots for station {station}.")


def init():
    # First generate all plots
    generate_all_plots()

    # Then schedule the generation of new plots every 10 minutes
    schedule.every(10).minutes.do(generate_all_plots)
