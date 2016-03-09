# -*- coding: utf-8 -*-
'''
    >>> MON == 'Понедельник'
    True
    >>> MON == 'Вторник'
    False
    >>> days[1] == '2'
    True
    >>> days[3] == 'THU'
    True
    >>> 'sat' == SAT
    True

    >>> SUN
    Weekday(sun)

    >>> MON + 1
    Weekday(tue)
    >>> FRI + 5
    Weekday(wed)
'''

import datetime
import itertools


class Weekday(object):
    def __init__(self, short, ru, *other_names):
        self._short = short
        self._ru_name = ru
        self._names = tuple(itertools.chain([short, ru], other_names))

    def short(self):
        return self._short

    def ru_name(self):
        return self._ru_name

    def __eq__(self, other):
        if isinstance(other, str):
            return other.strip().lower() in self._names or other == repr(self)
        return self._names == other._names

    def __repr__(self):
        return 'Weekday({0})'.format(self._short)

    def __hash__(self):
        return hash(repr(self))

    def __add__(self, shift):
         if shift < 0:
             return self - (-shift)
         return days[(days.index(self) + shift) % len(days)]

    def __sub__(self, shift):
         if shift < 0:
             return self + (-shift)
         return self + (len(days) - shift%len(days))


MON = Weekday('mon', 'понедельник', '1', 'monday', 'пн')
TUE = Weekday('tue', 'вторник', '2', 'tuesday', 'вт')
WED = Weekday('wed', 'среда', '3', 'wednesday', 'ср')
THU = Weekday('thu', 'четверг', '4', 'thursday', 'чт')
FRI = Weekday('fri', 'пятница', '5', 'friday', 'пт')
SAT = Weekday('sat', 'суббота', '6', 'saturday', 'сб')
SUN = Weekday('sun', 'воскресенье', '7', 'sunday', 'вс')


days = [
    MON,
    TUE,
    WED,
    THU,
    FRI,
    SAT,
    SUN,
]


def today():
    return days[datetime.datetime.now().weekday()]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
