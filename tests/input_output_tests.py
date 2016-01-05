#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from cli_yanbinbot import patch_do_request, patch_schedule_fetching, TheBot
from schedule import weekday

import os
import argparse
import unittest
import io
import json
import datetime


SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
INPUT_OUTPUT_TEST_SCHEDULE = 'schedule.json'
INPUT_OUTPUT_TEST_QUERIES = 'queries.txt'
INPUT_OUTPUT_TEST_EXPECTED = 'expected.txt'

class YanBinBotTest(unittest.TestCase):
    def setUp(self):
        self.bot = TheBot()



def read_and_close(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def patch_weekday_today():
    def fake_today():
        return weekday.MON

    weekday.today = fake_today


def test_functions_factory(directory):
    def test_function(self):
        # patching today
        patch_weekday_today()

        # patching schedule
        schedule = read_and_close(os.path.join(directory, INPUT_OUTPUT_TEST_SCHEDULE))
        patch_schedule_fetching(json.loads(schedule))

        # patching network
        output = io.StringIO()
        queries = read_and_close(os.path.join(directory, INPUT_OUTPUT_TEST_QUERIES))
        patch_do_request(io.StringIO(queries), output, False)

        # make requests
        for query in queries.splitlines():
            output.write('{0} {1} {0}\n'.format('#'*10, query))
            self.bot.process_response('http://stub-url.com')

        # check result
        expected = read_and_close(os.path.join(directory, INPUT_OUTPUT_TEST_EXPECTED))
        try:
            self.assertEqual(expected, output.getvalue())
        except AssertionError:
            with open(os.path.join(directory, 'got.txt'), 'wb') as f:
                f.write(output.getvalue().encode('utf-8'))
            raise

    return test_function


def add_input_output_tests(cls, directory):
    for f in os.listdir(directory):
        test_dir = os.path.join(directory, f)
        if not os.path.isdir(test_dir):
            continue

        setattr(cls, 'test_{0}'.format(f), test_functions_factory(test_dir))


if __name__ == '__main__':
    add_input_output_tests(YanBinBotTest, SCRIPT_DIRECTORY)
    unittest.main()
