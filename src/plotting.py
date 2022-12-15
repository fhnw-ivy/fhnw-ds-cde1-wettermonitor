import datetime
import os

import schedule

import weather_repository as wr
import plotly.express as px

import logging
logger = logging.getLogger("app")

plots_directory = "./static/plots/"

def generate_wind_speed_plot_today(station: str):
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Wind_speed_avg_10min], start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    plot = px.line(weather_data, x="time", y="wind_speed_avg_10min",
                   title="Windgeschwindigkeit (10min Mittelwert) der letzten 24 Stunden",
                   labels={"value": "Windgeschwindigkeit (m/s)", "variable": "Messung", "time": "Zeit"})
    save_plot(plot, "wind_speed", station)

def generate_wind_direction_plot(station: str):
    start_time = datetime.datetime.now() - datetime.timedelta(hours=6)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_direction], start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    plot = px.bar_polar(weather_data, r="wind_speed_avg_10min", theta="wind_direction",
                        title="Windrichtung (10min Mittelwert) der letzten Stunde",
                        labels={"value": "Windgeschwindigkeit (m/s)", "variable": "Messung", "time": "Zeit"})
    save_plot(plot, "wind_direction", station)

def save_plot(plot, plot_name, station):
    if not os.path.exists(plots_directory + station):
        os.makedirs(plots_directory + station)

    plot_file_name = f"{station}/{plot_name}"

    try:
        plot.write_image(f"{plots_directory}{plot_file_name}.svg")
        logger.debug(f"Saved plot {plot_name}.")
    except Exception as e:
        logger.error(f"Saving plot {plot_name} failed.")
        logger.error(e)

# Generate each plot for each station and catch any errors retry every single plot 3 times
def generate_all_plots():
    for station in wr.get_stations():
        try:
            generate_wind_speed_plot_today(station)
        except Exception as e:
            logger.error(f"Generating wind speed plot for station {station} failed.")
            logger.error(e)

        try:
            generate_wind_direction_plot(station)
        except Exception as e:
            logger.error(f"Generating wind direction plot for station {station} failed.")
            logger.error(e)

def init():
    # First generate all plots®
    generate_all_plots()

    # Then schedule the generation of new plots every 10 minutes
    schedule.every(10).minutes.do(generate_all_plots)
