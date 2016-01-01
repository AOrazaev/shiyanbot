#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from schedule import Lesson
import weekday
import pickle

import pyquery
import requests
import parse
import json


SHIYANBIN_SCHEDULE_LINK = 'https://docs.google.com/spreadsheets/d/1qrSKfJFQ79qYXdmEPNAy20ibVyMWhOOw1lscJG8lALQ/pubhtml#'

NO_TEXT = '---NO_TEXT---'


def request_shiyanbin_schedule():
    response = requests.get(SHIYANBIN_SCHEDULE_LINK)
    if response.ok:
        return pyquery.PyQuery(response.content.decode('utf-8'))('table')


def iterrows(table):
    for row in table.findall('.//tr'):
        yield [NO_TEXT if td.text is None else td.text.strip() for td in row.findall('td')]


def parse_table(table, row_parser):
    current_day = 0
    schedule = {}
    for row in iterrows(table):
        if current_day < len(weekday.days) and row and weekday.days[current_day] == row[0]:
            current_day += 1
            continue

        if current_day == 0:
            continue

        if row[0] != NO_TEXT:
            schedule.setdefault(repr(weekday.days[current_day - 1]), []).append(row_parser(row))
    return schedule


def parse_lesson_from_kungfu_table(row):
    result = parse.parse('{starts}###{ends}###{name}###'
                         '{place}###{teacher}###{difficulty}'
                         '###{complex}###{comment}###{}###{audience}',
                         '###'.join(row))
    if result is None:
        return None

    values = result.named
    for k, v in values.items():
        if v == NO_TEXT:
            values[k] = ''
    if result[0] != NO_TEXT:
        values['complex'] += ' ({0})'.format(result[0])
    return Lesson(**values)


def parse_lesson_from_qigong_table(row):
    result = parse.parse('{starts}###{ends}###{name}###'
                         '{place}###{teacher}###{comment}'
                         '###{difficulty}###{complex}###{}###{audience}',
                         '###'.join(row))
    if result is None:
        return None

    values = result.named
    for k, v in values.items():
        if v == NO_TEXT:
            values[k] = ''
    if result[0] != NO_TEXT:
        values['complex'] += ' ({0})'.format(result[0])
    return Lesson(**values)


def parse_lesson_from_children_table(row):
    result = parse.parse('{starts}###{ends}###{name}###'
                         '{audience}###{}###{place}'
                         '###{teacher}###{complex}###{comment}',
                         '###'.join(row))
    if result is None:
        return None

    values = result.named
    for k, v in values.items():
        if v == NO_TEXT:
            values[k] = ''
    if result[0] != NO_TEXT:
        values['audience'] += ' (age {0})'.format(result[0])
    values['difficulty'] = ''
    return Lesson(**values)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes', '__value__': list(python_object)}
    if isinstance(python_object, weekday.Weekday):
        return repr(python_object)
        raise TypeError(repr(python_object) + ' is not JSON serializable')


def fetch_schedule():
    qigong, kungfu, children = request_shiyanbin_schedule()
    kungfu = parse_table(kungfu, parse_lesson_from_kungfu_table)
    qigong = parse_table(qigong, parse_lesson_from_qigong_table)
    children = parse_table(children, parse_lesson_from_children_table)
    print(json.dumps(
        {'qigong': qigong, 'kungfu': kungfu, 'children': children},
        default=to_json,
        ensure_ascii=False,
        indent=2,
        separators=(',', ': ')))


if __name__ == '__main__':
    fetch_schedule()
