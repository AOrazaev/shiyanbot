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
    Weekday(7)
'''

import datetime


class Weekday(object):
    def __init__(self, names):
        self._names = tuple(names)

    def __eq__(self, other):
        if isinstance(other, str):
            return other.strip().lower() in self._names or other == repr(self)
        return self._names == other._names

    def __repr__(self):
        return 'Weekday({0})'.format(self._names[0])

    def __hash__(self):
        return hash(repr(self))


MON = Weekday(['mon', '1', 'monday', 'понедельник', 'пн'])
TUE = Weekday(['tue', '2', 'tuesday', 'вторник', 'вт'])
WED = Weekday(['wed', '3', 'wednesday', 'среда', 'ср'])
THU = Weekday(['thu', '4', 'thursday', 'четверг', 'чт'])
FRI = Weekday(['fri', '5', 'friday', 'пятница', 'пт'])
SAT = Weekday(['sat', '6', 'saturday', 'суббота', 'сб'])
SUN = Weekday(['sun', '7', 'sunday', 'воскресенье', 'вс'])


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
