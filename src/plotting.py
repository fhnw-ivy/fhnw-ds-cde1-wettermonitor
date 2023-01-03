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


def generate_wind_speed_plot_with_predictions(station: str):
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Wind_speed_avg_10min],
                                    start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    predictions = pr.get_predictions(station, relative_datetime_labels=True)

    plot = px.line(weather_data, x=weather_data.index, y="wind_speed_avg_10min")
    plot.add_scatter(x=list(predictions.keys()), y=list(x[0] for x in predictions.values()), mode='markers', name='Prediction')

    plot.update_layout(
        title="Wind speed (10min average)",
        xaxis_title="Time",
        yaxis_title="Wind speed (m/s)",
    )

    save_plot(plot, "wind_speed_with_predictions", station)


def generate_wind_speed_and_direction_plot_with_predictions(station: str):
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()

    weather_query = wr.WeatherQuery(station=station,
                                    measurements=[wr.Measurement.Wind_speed_avg_10min, wr.Measurement.Wind_direction],
                                    start_time=start_time,
                                    stop_time=stop_time)
    weather_data = wr.run_query(weather_query)

    predictions = pr.get_predictions(station, relative_datetime_labels=True)

    plot = px.bar_polar(weather_data, r="wind_speed_avg_10min", theta="wind_direction")

    plot.add_barpolar(r=list(x[0] for x in predictions.values()), theta=list(x[1] for x in predictions.values()),
                      name='Prediction')

    plot.update_layout(
        title="Wind speed and direction (10min average)",
        xaxis_title="Time",
        yaxis_title="Wind speed (m/s)",
    )

    save_plot(plot, "wind_speed_and_direction_with_predictions", station)


def save_plot(plot, plot_name, station):
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
    for station in wr.get_stations():
        try:
            generate_wind_speed_plot_with_predictions(station)
        except Exception as e:
            logger.error(f"Generating wind speed plot for station {station} failed.")
            logger.error(e)

        try:
            generate_wind_speed_and_direction_plot_with_predictions(station)
        except Exception as e:
            logger.error(f"Generating wind direction plot for station {station} failed.")
            logger.error(e)


def init():
    # First generate all plots
    generate_all_plots()

    # Then schedule the generation of new plots every 10 minutes
    schedule.every(10).minutes.do(generate_all_plots)
