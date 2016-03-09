#!/usr/bin/env python3
# coding: utf-8

import urllib.request
import urllib.parse
import time
import logging
import json
import re
import argparse
import os
import sys
import datetime
import subprocess
import random

import utils
import schedule.fetcher
import schedule.weekday as weekday


BotName = 'yanbinbot'
ServerUrl = 'https://api.telegram.org/bot'
BotToken = ''
RootUsers = ['lainindo']

ProgPath = os.path.abspath(sys.argv[0])
ProgDir = os.path.dirname(ProgPath)
ProjDir = os.path.dirname(ProgDir)
DataDir = os.path.join(ProjDir, 'data')
DaemonizePath = os.path.join(ProgDir, 'daemonize.py')


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-s', '--state', help='path to bot state file')
    p.add_argument('-p', '--pid', help='path to pid file')
    p.add_argument('-l', '--log', help='path to log')
    return p.parse_args()


def init(args):
    args.server_url = ServerUrl + BotToken
    if not args.pid:
        args.pid = os.path.join(DataDir, 'shiyanbin.pid')
    if not args.state:
        args.state = os.path.join(DataDir, 'shiyanbin.json')
    if not args.log:
        args.log = os.path.join(ProjDir, 'log', 'shiyanbin.log')
    log_dir = os.path.dirname(args.log)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(format='[%(levelname)s] %(asctime)s: %(message)s', level=logging.WARNING)


def get_next_token(text):
    delims = ' \n\t,.:!?'
    m = re.search('([^{0}]+)[{0}]+(.*)'.format(delims), text)
    if not m:
        return text, None
    return m.group(1), m.group(2)


def map_to_aliases(aliases_map):
    all_aliases = {}
    for name, aliases in aliases_map.items():
        for alias in aliases:
            all_aliases[alias] = name
    return all_aliases


class TheBot(object):
    CmdMap = {
        'restart': ['обновись', 'восстань', 'проснись', 'вставай'],
        'beforebeforeyesterday': ['позапозавчера'],
        'beforeyesterday': ['позавчера'],
        'yesterday': ['вчера'],
        'today': ['сегодня'],
        'tomorrow': ['завтра'],
        'aftertomorrow': ['послезавтра'],
        'monday': ['mon', 'пн', "понедельник"],
        'tuesday': ['tue', 'вт', "вторник"],
        'wednesday': ['wed', 'ср', "среда", 'среду'],
        'thursday': ['thu', 'чт', "четверг"],
        'friday': ['fri', 'пт', "пятница", 'пятницу'],
        'saturday': ['sat', 'сб', "суббота", 'субботу'],
        'sunday': ['sun', 'вс', "воскресенье"],
        'teachers': ['инструкторы', "мастера", "инструктора", "мастеры", "учителя", 'учители'],
        'all_lessons': ['все', 'занятия', 'неделя'],
    }
    TeacherMap = {
        'александр': ['саша'],
        'анастасия': ['настя'],
        'анна': ['аня'],
        'артем': ['тема', "тёма"],
        'валерий': ['валера'],
        'виталий': ['виталя'],
        'владимир': ['володя'],
        'даниил': ['даня', "данила"],
        'дмитрий': ['дима'],
        'евгений': ['женя'],
        'елена': ['лена'],
        'иван': ['ваня'],
        'катерина': ['катя'],
        'мария': ['маша'],
        'ольга': ['оля'],
        'пэнчжоу': ['пx?[еэ]?н[дч]?жо[у]?'],
        'янбин': ['шифу', "ши фу", 'ян бин'],
        'янфан': ['ян фан'],
    }
    AttrsToSave = ['offset']

    def __init__(self):
        self.offset = 0
        self.need_restart = False
        self.cmd_aliases = map_to_aliases(self.CmdMap)
        self.teacher_aliases = map_to_aliases(self.TeacherMap)
        self.schedule = None
        self.schedule_time = None


    def get_schedule(self):
        now = datetime.datetime.now()
        if self.schedule != None and now - self.schedule_time < datetime.timedelta(hours=1):
            return self.schedule
        self.schedule = schedule.fetcher.fetch()
        self.schedule_time = now
        return self.schedule


    def process_command(self, command, text, msg):
        if isinstance(command, list):
            if len(command) > 1:
                text = ' '.join(command[1:] + [text])
            command = command[0]
        if '@' in command:
            cmd, name = command.rsplit('@', 1)
            logging.warning('command only for %s: %s', name, cmd)
            if name.lower() != BotName:
                logging.warning('skipping command: %s', command)
                return []
            command = cmd
        command = command.rstrip('!,.)')
        logging.warning('processing command: %s', command)
        command = self.cmd_aliases.get(command, command)
        method = getattr(self, command+'_cmd', None)
        if not method:
            text = command + ' ' + text if text else command
            return self.all_lessons_cmd(text, msg)
        return method(text, msg)


    def monday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.MON)

    def tuesday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.TUE)

    def wednesday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.WED)

    def thursday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.THU)

    def friday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.FRI)

    def saturday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.SAT)

    def sunday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.SUN)

    def today_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.today(), today=True)

    def tomorrow_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.today() + 1)

    def aftertomorrow_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.today() + 2)

    def yesterday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.today() - 1)

    def beforeyesterday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.today() - 2)

    def beforebeforeyesterday_cmd(self, text, msg):
        return self.show_lessons(text, msg, weekday.today() - 3)

    def teachers_cmd(self, text, msg):
        return [{'text': '\n'.join(sorted(self.get_all_teachers()))}]

    def all_lessons_cmd(self, text, msg):
        ans = []
        for dow in weekday.days:
            ans.append({'text': '\n*%s*\n\n' % dow.ru_name().upper()})
            ans += self.show_lessons(text, msg, dow)
        return ans


    def get_all_teachers(self, lower=False):
        schdl = self.get_schedule()
        all_teachers = set()
        for week in schdl.values():
            for day in week.values():
                for lesson in day:
                    if lesson:
                        teacher = lesson.teacher.strip()
                        if teacher:
                            all_teachers.add(teacher.lower() if lower else teacher)
        return all_teachers


    @staticmethod
    def find_and_extract(text, pattern):
        m = re.match('(.*\s+|^)(%s)(\s+.*|$)'%pattern, text)
        if m:
            text = (m.group(1).strip() + ' ' + m.group(3).strip()).strip()
        return text, (m.group(2) if m else None)


    def show_lessons(self, text, msg, dow=None, today=False):
        s = self.get_schedule()
        all_teachers = self.get_all_teachers(True)
        types = set()
        only_teachers = set()
        if text:
            text = text.strip().lower()
            logging.warning('filter: %s', text)
            patterns = {'kungfu':'кунгфу|кунг-фу|кунг фу',
                        'qigong': 'цигун|ци-гун|ци гун|тайцзи|тайчи|тайцзицюань',
                        'children': 'дети|детские'}
            for kind, pattern in patterns.items():
                text, word = self.find_and_extract(text, pattern)
                if word != None:
                    types.add(kind)
            if text.strip():
                for teacher in all_teachers:
                    if re.search(text, teacher):
                        logging.warning('only teacher: %s', teacher)
                        only_teachers.add(teacher)
        ans = ''
        for name, label in [('qigong', 'Цигун'), ('kungfu', 'Кунг-фу'), ('children', 'Дети')]:
            if types and name not in types:
                continue
            lessons = []
            for l in s[name][dow]:
                if l:
                    if today:
                        starts = datetime.datetime.strptime(l.starts, '%H.%M').strftime('%H.%M') # to process time format like 8.30
                        now = datetime.datetime.today().strftime('%H.%M')
                        if starts < now:
                            continue
                    if only_teachers and l.teacher.strip().lower() not in only_teachers:
                        continue
                    lessons.append(l)
            if lessons:
                ans += '*%s*\n\n' % label
                for l in lessons:
                    ans += '_%s%s_ *%s* _%s_: %s, %s' % (l.starts, ('-'+l.ends if l.ends else ''), l.teacher, l.name, l.complex, l.place)
                    if l.difficulty.strip():
                        ans += ', *%s нагрузка*' % l.difficulty.strip()
                    if l.audience.strip():
                        ans += ', %s' % l.audience.strip()
                    if l.comment.strip():
                        ans += ' - *%s*' % l.comment.strip()
                    ans += '\n\n'
                ans += '\n'
        if not ans:
            ans += 'занятия, соответствующие вашему запросу, не найдены\n'
        return [{'text': ans}]


    def restart_cmd(self, text, msg):
        if not self.is_root(msg):
            return []
        self.need_restart = True
        return [{'text': 'Обновляюсь'}]


    def is_root(self, msg):
        return self.get_username(msg).lower() in RootUsers


    @staticmethod
    def get_username(msg):
        return msg.get('from',{}).get('username', '<UNKNOWN>')


    @staticmethod
    def is_username_defined(msg):
        return msg.get('from',{}).get('username') is not None


    @staticmethod
    def get_first_name(msg):
        return msg.get('from',{}).get('first_name') or self.get_username(msg)


    def start_cmd(self, text, msg):
        return [{'text': 'Welcome, %s!'%self.get_first_name(msg)}]


    def replace_teacher_aliases(self, text):
        for alias, name in self.teacher_aliases.items():
            txt, replaced = self.find_and_extract(text, alias)
            if replaced:
                return txt + ' ' + name
        return text


    def process_text_message(self, msg):
        if msg.get('forward_from'):
            return []
        text = msg.get('text', '').lower()
        text, _ = self.find_and_extract(text, 'занятия|занятие')
        text, _ = self.find_and_extract(text, 'в|во')
        text = self.replace_teacher_aliases(text)
        result = []
        cmd = None
        if text[:1] == '/':
            text = text[1:]
        else:
            for c in list(self.CmdMap.keys()) + list(self.cmd_aliases.keys()):
                text, word = self.find_and_extract(text, c)
                if word != None:
                    cmd = c
                    rest = text
                    break
        if not cmd:
            cmd, rest = get_next_token(text)
        result += self.process_command(cmd, rest, msg)
        if not result:
            return []
        for r in result:
            r['chat_id'] = msg['chat']['id']
        return result


    def process_response(self, server_url):
        response = utils.do_request(server_url, 'getUpdates', {'offset': self.offset})
        if response and isinstance(response, dict) and response.get('ok'):
            updates = response['result']
            if updates and isinstance(updates, list):
                logging.warning('got updates: %s', str(updates))
                for update in updates:
                    try:
                        msg = update.get('message')
                        msg_out = None
                        if msg and 'text' in msg:
                            msg_out = self.process_text_message(msg)
                        if msg_out is not None:
                            for msg in msg_out:
                                action = 'sendPhoto' if 'photo' in msg else 'sendLocation' if 'latitude' in msg else 'sendMessage' 
                                if action == 'sendMessage':
                                    msg['disable_web_page_preview'] = True
                                    msg['parse_mode'] = 'Markdown'
                                #logging.warning('sending: %s', str(msg))
                                utils.do_request(server_url, action, msg)
                    except Exception as ex:
                        logging.error('failed to process update: %s\n%s', str(update), str(ex))
                    self.offset = max(update['update_id']+1, self.offset)
        else:
            logging.error('failed to get updates: %s', str(response))


    def run(self, server_url, wait_time):
        self.need_restart = False
        while True:
            try:
                self.process_response(server_url)
            except KeyboardInterrupt:
                logging.error('keyboard interrupt, stopped processing messages')
                break
            except Exception as ex:
                logging.error('got error: %s', str(ex))
            if self.need_restart:
                break
            time.sleep(wait_time)


    def save(self, fpath):
        with open(fpath, 'w') as f_out:
            data = {}
            for attr in self.AttrsToSave:
                data[attr] = getattr(self, attr)
            json.dump(data, f_out)


    @staticmethod
    def load(fpath):
        with open(fpath) as f_in:
            data = json.load(f_in)
            bot = TheBot()
            for attr in bot.AttrsToSave:
                if attr in data:
                    setattr(bot, attr, data[attr])
            return bot


def is_proc_alive(pid_path):
    if os.path.exists(pid_path):
        with open(pid_path) as f_in:
            pid = f_in.readline().rstrip('\n')
            if pid:
                if os.path.exists('/proc/%s'%pid):
                    return True
    return False


def restart(args):
    if os.path.exists(args.pid):
        os.remove(args.pid)
    cmd = [DaemonizePath, '-p', args.pid, '--', ProgPath, '-l', args.log, '-s', args.state, '-p', args.pid]
    subprocess.check_call(cmd)
    time.sleep(3) # give daemon time to start
    return is_proc_alive(args.pid)



def run_bot(args):
    if os.path.exists(args.state):
        bot = TheBot.load(args.state)
        logging.warning('Bot state loaded from %s', args.state)
    else:
        bot = TheBot()
    while True:
        try:
            bot.run(args.server_url, 5)
        except (KeyboardInterrupt, Exception) as ex:
            logging.error(str(ex))
            pass
        bot.save(args.state)
        logging.warning('Bot state saved to %s', args.state)

        if bot.need_restart:
            if restart(args):
                logging.warning(BotName + ' restarted as a daemon.')
                break
            logging.error('Could not restart bot. Continuing working.')


def main():
    args = parse_args()
    random.seed(int(time.time()))
    init(args)
    run_bot(args)


if __name__ == "__main__":
    main()
