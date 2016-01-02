# -*- coding: utf-8 -*-


from collections import namedtuple

Lesson = namedtuple(
    'Lesson',
    ['starts', 'ends', 'name',
     'place', 'difficulty', 'teacher',
     'complex', 'comment', 'audience'])
