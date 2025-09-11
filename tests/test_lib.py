import datetime as dt
import random
import unittest
from unittest.mock import patch

from enerbitdso.enerbit import (
    DSOClient,
    InvalidParameterError,
)

from .mocked_responses import (
    create_mocked_usages,
    create_mocked_schedules,
    get_mocked_schedules,
    get_mocked_usages,
    mocked_schedules,
    mocked_usages,
)

WEEKS_TO_TEST = 5


class TestMyLibrary(unittest.TestCase):
    @patch("enerbitdso.enerbit.get_auth_token")
    def test_get_all_usage_records(self, mock_get_auth_token):
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        create_mocked_schedules(frt_code=frontier, since=since_month, until=until_month)
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        with patch(
            "enerbitdso.enerbit.get_schedule_usage_records",
            side_effect=get_mocked_usages,
        ):
            usages = ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=frontier, since=since_month, until=until_month
            )
        self.assertEqual(usages, mocked_usages)

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_get_part_usage_records(self, mock_get_auth_token):
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        since = until_month - dt.timedelta(weeks=WEEKS_TO_TEST - 2)
        until = until_month
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        create_mocked_schedules(frt_code=frontier, since=since_month, until=until_month)
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        with patch(
            "enerbitdso.enerbit.get_schedule_usage_records",
            side_effect=get_mocked_usages,
        ):
            usages = ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=frontier, since=since, until=until
            )
        for usage in usages:
            self.assertIn(
                usage, mocked_usages, "The usage is not in mocked usages list"
            )

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_get_empty_usage_records(self, mock_get_auth_token):
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        since = since_month - dt.timedelta(weeks=WEEKS_TO_TEST - 2)
        until = since_month
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        create_mocked_schedules(frt_code=frontier, since=since_month, until=until_month)
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        with patch(
            "enerbitdso.enerbit.get_schedule_usage_records",
            side_effect=get_mocked_usages,
        ):
            usages = ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=frontier, since=since, until=until
            )
        self.assertEqual(usages, [])

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_get_all_schedule_records(self, mock_get_auth_token):
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        create_mocked_usages(frt_code=frontier, since=since_month, until=until_month)
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        with patch(
            "enerbitdso.enerbit.get_schedule_measurement_records",
            side_effect=get_mocked_schedules,
        ):
            schedules = ebconnector.fetch_schedule_measurements_records_large_interval(
                frt_code=frontier, since=since_month, until=until_month
            )
        self.assertEqual(schedules, mocked_schedules)

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_get_part_schedule_records(self, mock_get_auth_token):
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        since = until_month - dt.timedelta(weeks=WEEKS_TO_TEST - 2)
        until = until_month
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        create_mocked_usages(frt_code=frontier, since=since_month, until=until_month)
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        with patch(
            "enerbitdso.enerbit.get_schedule_measurement_records",
            side_effect=get_mocked_schedules,
        ):
            schedules = ebconnector.fetch_schedule_measurements_records_large_interval(
                frt_code=frontier, since=since, until=until
            )
        for schedule in schedules:
            self.assertIn(
                schedule, mocked_schedules, "The schedule is not in mocked usages list"
            )

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_get_empty_schedule_records(self, mock_get_auth_token):
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        since = since_month - dt.timedelta(weeks=WEEKS_TO_TEST - 2)
        until = since_month
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        create_mocked_usages(frt_code=frontier, since=since_month, until=until_month)
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        with patch(
            "enerbitdso.enerbit.get_schedule_measurement_records",
            side_effect=get_mocked_schedules,
        ):
            schedules = ebconnector.fetch_schedule_measurements_records_large_interval(
                frt_code=frontier, since=since, until=until
            )
        self.assertEqual(schedules, [])

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_parameter_validation_both_parameters(self, mock_get_auth_token):
        """Test that providing both frt_code and meter_serial raises InvalidParameterError"""
        today = dt.datetime.now()
        yesterday = today - dt.timedelta(days=1)
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        meter = "".join(random.choices("0123456789", k=5))
        
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        
        with self.assertRaises(InvalidParameterError) as context:
            ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=frontier, meter_serial=meter, since=yesterday, until=today
            )
        
        self.assertIn("No se pueden especificar tanto", str(context.exception))

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_parameter_validation_no_parameters(self, mock_get_auth_token):
        """Test that providing neither frt_code nor meter_serial raises InvalidParameterError"""
        today = dt.datetime.now()
        yesterday = today - dt.timedelta(days=1)
        
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        
        with self.assertRaises(InvalidParameterError) as context:
            ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=None, meter_serial=None, since=yesterday, until=today
            )
        
        self.assertIn("Debe especificar al menos uno", str(context.exception))

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_parameter_validation_empty_strings(self, mock_get_auth_token):
        """Test that empty strings are treated as None"""
        today = dt.datetime.now()
        yesterday = today - dt.timedelta(days=1)
        
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        
        with self.assertRaises(InvalidParameterError) as context:
            ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code="", meter_serial="  ", since=yesterday, until=today
            )
        
        self.assertIn("Debe especificar al menos uno", str(context.exception))

    @patch("enerbitdso.enerbit.get_auth_token")
    def test_meter_serial_filtering(self, mock_get_auth_token):
        """Test filtering by meter_serial parameter"""
        today = dt.datetime.now()
        since_month = today - dt.timedelta(weeks=WEEKS_TO_TEST)
        until_month = today
        frontier = "Frt" + "".join(random.choices("0123456789", k=5))
        test_meter = "12345"
        
        # Create mocked data
        create_mocked_usages(frt_code=frontier, since=since_month, until=until_month)
        # Modify first few records to have our test meter serial
        for i in range(min(3, len(mocked_usages))):
            mocked_usages[i].meter_serial = test_meter
        
        mock_get_auth_token.return_value = "my_token"
        ebconnector = DSOClient(
            api_base_url="https://dso.enerbit.me/",
            api_username="test",
            api_password="test",
        )
        
        with patch(
            "enerbitdso.enerbit.get_schedule_usage_records",
            side_effect=get_mocked_usages,
        ):
            usages = ebconnector.fetch_schedule_usage_records_large_interval(
                frt_code=None, meter_serial=test_meter, since=since_month, until=until_month
            )
        
        # Verify all returned records have the correct meter_serial
        for usage in usages:
            self.assertEqual(usage.meter_serial, test_meter)
        
        # Should have exactly 3 records (the ones we modified)
        self.assertEqual(len(usages), 3)


if __name__ == "__main__":
    unittest.main()
