#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''Command line interface to shiyanbot

Main idea: after monkey patching utils.do_request we can send
messages using stdin.
'''

from yanbinbot import TheBot
from schedule.schedule import Lesson
from schedule.weekday import Weekday

import argparse
import sys
import utils
import itertools
import schedule.fetcher
import json


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-s', '--schedule', type=argparse.FileType('rb'),
                        help='use given schedule.json instead of fetching')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Turn on debug output')

    return parser.parse_args()


def patch_do_request(input_file=sys.stdin, output_file=sys.stdout, debug=True):
    update_id_counter = itertools.count()
    def fake_do_request(server_url, action, data=None):
        if action != 'getUpdates':
            if debug:
                print(data, file=output_file, flush=True)
            else:
                print(data.get('text'), file=output_file, flush=True)
            return

        text = input_file.readline()
        return {
            'result': [{
                'message': {
                    'text': text,
                    'from': {'username': 'You'},
                    'chat': {'id': 0},
                },
                'update_id': next(update_id_counter),
            }],
            'ok': bool(text)
        }

    utils.do_request = fake_do_request


def schedule_from_json(data):
    result = {}
    for discipline in data:
        result[discipline] = {}
        for day in data[discipline]:
            for lesson in data[discipline][day]:
                result[discipline].setdefault(day, []).append(Lesson(*lesson))
    return result


def patch_schedule_fetching(data):
    # Copying to avoid outreferencing
    result = schedule_from_json(data)
    def fake_fetch():
        return result
    schedule.fetcher.fetch = fake_fetch


def main(args):
    patch_do_request(debug=args.debug)
    if args.schedule:
        patch_schedule_fetching(json.loads(args.schedule.read().decode('utf-8')))

    TheBot().run('https://no-url-here.com', 0)


if __name__ == '__main__':
    main(parse_args())
