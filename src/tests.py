import datetime
import unittest

import app
import weather_repository as wr


class WeatherQueryTestCase(unittest.TestCase):
	def test_query_simple(self):
		"""
        Test that the weather_query string is created correctly when no time is specified.
        """
		measurements = [wr.Measurement.Water_temp, wr.Measurement.Air_temp]
		query = wr.WeatherQuery(station="test", measurements=measurements)
		self.assertEqual("SELECT water_temperature,air_temperature FROM test ORDER BY time DESC LIMIT 1",
		                 query.create_query_string())

	def test_query_with_time(self):
		"""
        Test that the weather_query string is created correctly when a time is specified.
        """
		measurements = [wr.Measurement.Water_temp, wr.Measurement.Air_temp]
		query = wr.WeatherQuery(station="test", measurements=measurements,
		                        start_time=datetime.datetime(2021, 1, 1, 0, 0, 0),
		                        stop_time=datetime.datetime(2021, 1, 1, 0, 0, 0))
		self.assertEqual(
			"SELECT water_temperature,air_temperature FROM test WHERE time >= '2021-01-01T00:00:00Z' AND time <= '2021-01-01T00:00:00Z'",
			query.create_query_string())


class WeatherRepositoryTestCase(unittest.TestCase):
	def test_get_units(self):
		"""
        Test that the right units are returned for the different measurements using the unit_mapping dictionary.
        """
		self.assertEqual("°C", wr.get_unit(wr.Measurement.Air_temp.value))
		self.assertEqual("°C", wr.get_unit(wr.Measurement.Water_temp.value))
		self.assertEqual("m/s", wr.get_unit(wr.Measurement.Wind_speed_avg_10min.value))
		self.assertEqual("m/s", wr.get_unit(wr.Measurement.Wind_gust_max_10min.value))
		self.assertEqual("°", wr.get_unit(wr.Measurement.Wind_direction.value))
		self.assertEqual("hPa", wr.get_unit(wr.Measurement.Pressure.value))
		self.assertEqual("mm", wr.get_unit(wr.Measurement.Precipitation.value))


class UserInterfaceTestCase(unittest.TestCase):
	def test_convert_to_datetime_string(self):
		"""
        Test that the datetime is converted to a string correctly.
        """
		self.assertEqual("01.01.2021 00:00", app.convert_to_datetime_string(datetime.datetime(2021, 1, 1, 0, 0, 0)))

		today = datetime.datetime.now()
		today = today.replace(hour=12, minute=14, second=0, microsecond=0)
		self.assertEqual("12:14", app.convert_to_datetime_string(today))


if __name__ == '__main__':
	unittest.main()
