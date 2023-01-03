import datetime
import logging
import os

import plotly.express as px
import schedule

import prediction as pr
import weather_repository as wr

logger = logging.getLogger("app")

plots_directory = "./static/plots/"
plots_size = (1024, 600)

def get_plots():
    """
    Returns a list of all plot names.
    """
    return ['wind_speed', 'air_temperature', 'wind_direction']

def generate_wind_speed_plot(station: str):
    """
    Generates a plot of the wind speed measurements for the given station. The plot also contains predictions for the next hour.
    Args:
        station: The station to generate the plot for.

    Returns: None
    """

    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_gust_max_10min],
                                    start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    predictions = pr.get_predictions(station, relative_datetime_labels=True)

    plot = px.line(weather_data, x=weather_data.index, y="wind_speed_avg_10min")

    plot.add_scatter(x=weather_data.index, y=weather_data["wind_gust_max_10min"], name="Wind gust (10min max)", mode="lines")
    plot.add_scatter(x=list(predictions.keys()), y=list(x[0] for x in predictions.values()), mode='lines', name='Wind speed prediction (10min avg)')

    plot.update_layout(
        title="Wind speed (10min avg)",
        xaxis_title="Time",
        yaxis_title="Wind speed (m/s)"
    )

    save_plot(plot, "wind_speed", station)

def generate_air_temperature_plot(station: str):
    """
    Generates a plot of the air temperature for the given station.
    Args:
        station: The station to generate the plot for.

    Returns: None
    """

    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Air_temp],
                                    start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    plot = px.line(weather_data, x=weather_data.index, y="air_temperature")

    plot.update_layout(
        title="Air temperature",
        xaxis_title="Time",
        yaxis_title="Temperature (C)",
    )

    plot.update_yaxes(range=[min(-5, weather_data["air_temperature"].min() - 3), max(5, weather_data["air_temperature"].max() + 3)])
    save_plot(plot, "air_temperature", station)

def generate_wind_direction_plot(station: str):
    """
    Generates a plot of the wind direction for the given station. The plot also contains predictions for the next hour.
    Args:
        station: The station to generate the plot for.

    Returns: None
    """

    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Wind_direction],
                                    start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    predictions = pr.get_predictions(station, relative_datetime_labels=True)

    plot = px.line(weather_data, x=weather_data.index, y="wind_direction")
    plot.add_scatter(x=list(predictions.keys()), y=list(x[1] for x in predictions.values()), mode='lines', name='Prediction')

    plot.update_layout(
        title="Wind direction",
        xaxis_title="Time",
        yaxis_title="Wind direction (degree)",
    )

    plot.update_yaxes(range=[0, 360])

    save_plot(plot, "wind_direction", station)

def save_plot(plot, plot_name, station):
    """
    Saves the given plot to a file.
    Args:
        plot: The plot to save.
        plot_name: The name of the plot.
        station: The station the plot is for.
    Returns: None
    """

    if not os.path.exists(plots_directory + station):
        os.makedirs(plots_directory + station)

    plot_file_name = f"{station}/{plot_name}"

    try:
        plot.write_image(os.path.join(os.path.dirname(__file__), plots_directory, plot_file_name + ".png"),
                         width=plots_size[0], height=plots_size[1])
        logger.debug(f"Saved plot {plot_name} for station {station} as png file.")
    except Exception as e:
        logger.error(f"Saving plot {plot_name} failed.")
        logger.error(e)


def generate_all_plots():
    """
    Generates all plots for all stations.
    Returns: None
    """

    for station in wr.get_stations():
        try:
            generate_wind_speed_plot(station)
        except Exception as e:
            logger.error(f"Generating wind speed plot for station {station} failed.")
            logger.error(e)

        try:
            generate_air_temperature_plot(station)
        except Exception as e:
            logger.error(f"Generating air temperature plot for station {station} failed.")
            logger.error(e)

        try:
            generate_wind_direction_plot(station)
        except Exception as e:
            logger.error(f"Generating wind direction plot for station {station} failed.")
            logger.error(e)

def init():
    """
    Initializes the plotting module.
    Returns: None
    """

    # First generate all plots
    generate_all_plots()

    # Then schedule the generation of new plots every 10 minutes
    schedule.every(10).minutes.do(generate_all_plots)