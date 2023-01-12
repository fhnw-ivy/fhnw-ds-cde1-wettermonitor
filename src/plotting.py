import datetime
import logging
import os

import plotly.graph_objects as go
import schedule

import prediction as pr
import weather_repository as wr

logger = logging.getLogger("app")

plots_directory = "./static/plots/"
plot_size = (1000, 650)  # width, height


def get_plots():
	"""
    Returns a list of all plot names.
    """
	return ['wind_speed_1d', 'wind_speed_7d', 'air_temperature_1d', 'air_temperature_7d', 'wind_direction']


def resample_and_interpolate_data(df, resample_rule="H", interpolation_method="linear"):
	"""
    Resamples and interpolates the given data frame.
    Args:
        df: The data frame to resample and interpolate.
        resample_rule: The rule to resample with.
        interpolation_method: The interpolation method to use.

    Returns: The resampled and interpolated data frame.
    """
	df = df.resample(resample_rule).mean()
	df = df.interpolate(method=interpolation_method)
	return df


def add_mean_min_max_to_plot(plot, df, property_key, unit):
	"""
    Adds a mean line and min/max points to the given plot.
    Args:
        plot: The plot to add the mean line and min/max points to.
        df: The data frame containing the data.
        property_key: The key of the property to add the mean line and min/max points for.
        unit: The unit of the property.
    """
	plot.add_trace(go.Scatter(x=[df.index.min(), df.index.max()],
	                          y=[df[property_key].mean()] * 2, mode='lines',
	                          name=f"Mean: {df[property_key].mean():.2f}{unit}",
	                          line=dict(dash='dash')))

	plot.add_trace(go.Scatter(x=[df[property_key].idxmin()],
	                          y=[df[property_key].min()],
	                          mode='markers',
	                          name=f"Min: {df[property_key].min():.2f}{unit}",
	                          marker=dict(size=10, color="red")))

	plot.add_trace(go.Scatter(x=[df[property_key].idxmax()],
	                          y=[df[property_key].max()],
	                          mode='markers',
	                          name=f"Max: {df[property_key].max():.2f}{unit}",
	                          marker=dict(size=10, color="red")))


def save_plot(plot, plot_name, station):
	"""
    Saves the given plot to a file.
    Args:
        plot: The plot to save.
        plot_name: The name of the plot.
        station: The station the plot is for.
    Returns: None
    """

	plot.update_layout(
		autosize=False,
		width=plot_size[0],
		height=plot_size[1],
	)

	if not os.path.exists(plots_directory + station):
		os.makedirs(plots_directory + station)

	plot_file_name = f"{station}/{plot_name}"

	try:
		plot.write_image(os.path.join(os.path.dirname(__file__), plots_directory, plot_file_name + ".svg"))

		logger.debug(f"Saved plot {plot_name} for station {station} as svg file.")
	except Exception as e:
		logger.error(f"Saving plot {plot_name} failed.")
		logger.error(e)


def generate_wind_speed_plot(station: str, days_delta):
	"""
    Generates a plot of the wind speed measurements for the given station. The plot also contains predictions for the next hour.
    Args:
        station: The station to generate the plot for.
        days_delta: The number of days to go back in time.

    Returns: None
    """

	start_time = datetime.datetime.now() - datetime.timedelta(days=days_delta)
	stop_time = datetime.datetime.now()

	weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Wind_speed_avg_10min,
	                                                               wr.Measurement.Wind_gust_max_10min],
	                                start_time=start_time,
	                                stop_time=stop_time)
	weather_data = wr.run_query(weather_query)

	predictions = None

	if days_delta > 1:
		weather_data = resample_and_interpolate_data(weather_data)
	else:
		predictions = pr.get_predictions(station, relative_datetime_labels=True)

	plot = go.Figure()

	plot.add_trace(
		go.Scatter(x=weather_data.index, y=weather_data["wind_speed_avg_10min"], mode='lines',
		           name='Wind speed (10min avg)'))
	plot.add_trace(
		go.Scatter(x=weather_data.index, y=weather_data["wind_gust_max_10min"], mode='lines',
		           name='Wind gust (10min max)'))

	if predictions is not None:
		plot.add_trace(go.Scatter(x=list(predictions.keys()), y=list(x[0] for x in predictions.values()), mode='lines',
		                          name='Wind speed prediction'))

		plot.update_xaxes(range=[weather_data.index.min(), list(predictions.keys())[-1]])
	else:
		plot.update_xaxes(range=[weather_data.index.min(), weather_data.index.max()])

	add_mean_min_max_to_plot(plot, weather_data, "wind_speed_avg_10min",
	                         wr.unit_mapping[wr.Measurement.Wind_speed_avg_10min.value])

	plot.update_layout(
		title=f"Wind speeds of the last " + ("24 hours" if days_delta == 1 else f"{days_delta} days"),
		xaxis_title="Time",
		yaxis_title="Wind speed [m/s]",
	)

	save_plot(plot, f"wind_speed_{days_delta}d", station)


def generate_air_temperature_plot(station: str, days_delta):
	"""
    Generates a plot of the air temperature for the given station.
    Args:
        station: The station to generate the plot for.
        days_delta: The number of days to go back in time.

    Returns: None
    """

	start_time = datetime.datetime.now() - datetime.timedelta(days=days_delta)
	stop_time = datetime.datetime.now()

	weather_query = wr.WeatherQuery(station=station, measurements=[wr.Measurement.Air_temp],
	                                start_time=start_time,
	                                stop_time=stop_time)
	weather_data = wr.run_query(weather_query)

	if days_delta > 1:
		weather_data = resample_and_interpolate_data(weather_data)

	plot = go.Figure()

	plot.add_trace(
		go.Scatter(x=weather_data.index, y=weather_data["air_temperature"], mode='lines', name='Air temperature'))

	add_mean_min_max_to_plot(plot, weather_data, "air_temperature", wr.unit_mapping[wr.Measurement.Air_temp.value])

	plot.update_xaxes(range=[weather_data.index.min(), weather_data.index.max()])

	plot.update_layout(
		title=f"Air temperature of the last " + ("24 hours" if days_delta == 1 else f"{days_delta} days"),
		xaxis_title="Time",
		yaxis_title="Temperature [°C]"
	)

	save_plot(plot, f"air_temperature_{days_delta}d", station)


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

	plot = go.Figure()

	plot.add_trace(
		go.Scatter(x=weather_data.index, y=weather_data["wind_direction"], mode='lines', name='Wind direction'))

	plot.add_trace(go.Scatter(x=list(predictions.keys()), y=list(x[1] for x in predictions.values()), mode='lines',
	                          name='Prediction'))

	add_mean_min_max_to_plot(plot, weather_data, "wind_direction", wr.unit_mapping[wr.Measurement.Wind_direction.value])

	plot.update_yaxes(range=[0, 360])
	plot.update_xaxes(range=[weather_data.index.min(), list(predictions.keys())[-1]])

	plot.update_layout(
		title=f"Wind direction of the last 24 hours",
		xaxis_title="Time",
		yaxis_title="Wind direction [°]",
	)

	save_plot(plot, "wind_direction", station)


def generate_all_plots():
	"""
    Generates all plots for all stations.
    Returns: None
    """

	days_deltas = [1, 7]

	for station in wr.get_stations():
		for days_delta in days_deltas:
			try:
				generate_wind_speed_plot(station, days_delta)
			except Exception as e:
				logger.error(f"Generating wind speed plot for station {station} with {days_delta} days delta failed.")
				logger.error(e)

			try:
				generate_air_temperature_plot(station, days_delta)
			except Exception as e:
				logger.error(
					f"Generating air temperature plot for station {station} with {days_delta} days delta failed.")
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
