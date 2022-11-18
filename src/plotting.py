import datetime

import weather_repository as wr
import seaborn as sns
import plotly.express as px
sns.set_theme()


def generate_last_week_plots():
    start_time = datetime.datetime.now() - datetime.timedelta(days=1)
    stop_time = datetime.datetime.now()
    measurements = [wr.Measurement.Air_temp, wr.Measurement.Water_temp, wr.Measurement.Precipitation]

    data_query = wr.WeatherQuery(start_time=start_time, stop_time=stop_time, station="tiefenbrunnen", measurements=measurements)
    data = wr.run_query(data_query)

    plot = sns.lineplot(data=data, x="time", y=wr.Measurement.Air_temp.value)
    plot = px.line(data, x="time", y=wr.Measurement.Air_temp.value)

    save_plot(plot, "air_temp_7days")



def save_plot(plot, plot_name):
    try:
        plot.savefig(f"/static/plots/{plot_name}.png")
        # plot.get_figure().savefig(f'./static/{plot_name}.png', dpi=500, bbox_inches='tight')
    except Exception as e:
        print("save_plot failed.")
        print(e)