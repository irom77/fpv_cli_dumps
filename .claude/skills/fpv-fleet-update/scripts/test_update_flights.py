#!/usr/bin/env python3
import unittest

import update_flights


class FlightCaptureFilterTests(unittest.TestCase):
    def test_accepts_capture_with_minimum_duration_and_throttle_activity(self):
        summary = {'duration_s': 1.0, '_max_throttle': 1001}

        self.assertTrue(update_flights.is_flight_capture(summary))

    def test_rejects_capture_without_throttle_activity(self):
        summary = {'duration_s': 6.0, '_max_throttle': 1000}

        self.assertFalse(update_flights.is_flight_capture(summary))
        self.assertEqual(
            update_flights.flight_capture_rejection_reasons(summary),
            ['peak throttle 1000 did not exceed idle 1000'],
        )

    def test_rejects_capture_shorter_than_minimum_duration(self):
        summary = {'duration_s': 0.9, '_max_throttle': 1250}

        self.assertFalse(update_flights.is_flight_capture(summary))
        self.assertEqual(
            update_flights.flight_capture_rejection_reasons(summary),
            ['duration 0.900s is below 1.000s'],
        )

    def test_reports_all_reasons_for_skipped_capture(self):
        summary = {'_duration_s': 0.725, '_max_throttle': 1000}

        self.assertEqual(
            update_flights.flight_capture_rejection_reasons(summary),
            [
                'duration 0.725s is below 1.000s',
                'peak throttle 1000 did not exceed idle 1000',
            ],
        )

    def test_formats_skipped_log_message_with_file_index_and_reasons(self):
        message = update_flights.format_skipped_log(
            'capture.BBL',
            10,
            ['duration 0.725s is below 1.000s', 'peak throttle 1000 did not exceed idle 1000'],
        )

        self.assertEqual(
            message,
            'Skipped capture.BBL log 10: duration 0.725s is below 1.000s; '
            'peak throttle 1000 did not exceed idle 1000',
        )


class DurableFlightMergeTests(unittest.TestCase):
    def test_replaces_rows_for_present_logs_and_retains_absent_logs(self):
        existing = {
            ('present.BBL', '9'): {'file': 'present.BBL', 'log_index': '9', 'duration_s': '6.2'},
            ('present.BBL', '10'): {'file': 'present.BBL', 'log_index': '10', 'duration_s': '0.7'},
            ('archived.BBL', '1'): {'file': 'archived.BBL', 'log_index': '1', 'duration_s': '30.0'},
        }
        current = {
            ('present.BBL', '9'): {'file': 'present.BBL', 'log_index': 9, 'duration_s': 6.2},
        }

        merged = update_flights.merge_flight_rows(existing, current, {'present.BBL'})

        self.assertEqual(
            set(merged),
            {('present.BBL', '9'), ('archived.BBL', '1')},
        )


if __name__ == '__main__':
    unittest.main()
