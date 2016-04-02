#!/usr/bin/python

from __future__ import print_function
import argparse
import ConfigParser
from datetime import datetime, date, timedelta
import os
import re
import string
import sys


################################################################################

LOG_QUIET = False
LOG_SILENT = False

TIME_FORMAT = "%m/%d/%Y %H:%M"
TODAY = datetime.today()
TODAY_F = TODAY.strftime("%m/%d/%Y")

HOME = "/home/minebox/"
CONFIG = HOME + ".activity-monitor"
UPLOAD_LOG = HOME + "uploadlog"
OUTPUT_LOG = HOME + "activity.log"
LOG_FILE = HOME + "spigot/logs/latest.log"

RE_LIST_ITEM = re.compile("'(?P<item>[^']+)'")

RE_TIMESTAMP = re.compile("\\[(?P<time>\\d+:\\d+:\\d+)\\] \\[(?P<thread>[^/]*)/(?P<type>[^\\]]*?)\\]: (?P<line>.*)")

RE_LOGIN = re.compile("(?P<name>[^\\[]*)\\[/(?P<ip>\\d+\\.\\d+\\.\\d+\\.\\d+):(?P<port>\\d+)\\] logged in with entity id (?P<entity>\\d+) at \\(\\[(?P<world>[^\\]]*)\\](?P<x>\\d+\\.\\d+), (?P<y>\\d+\\.\\d+), (?P<z>\\d+\\.\\d+)\\)")

RE_DISCONNECT = re.compile("(?P<name>.*?) lost connection: (?P<reason>.*)")

RE_LOGOUT = re.compile("(?P<name>.*?) left the game")

REGEXES = []

online_players = set()

empty_since = None

last_run = None

line_count = 0

################################################################################

def format_time(time):
    return time.strftime(TIME_FORMAT)


def parse_set(str):
    set_out = set()
    for item in RE_LIST_ITEM.findall(str):
        set_out.add(item)
    return set_out


def log(file, msg):
    msg = "  " + msg.__str__() + "  "
    remainder = 80 - len(msg)
    half = remainder / 2
    builder = ('#' * half) + msg + ('#' * half)
    file.write(builder + "\n")


def log_blank(file, n=1):
    file.write("\n" * n)


def log_echo(file, msg=""):
    if not LOG_QUIET and not LOG_SILENT:
        print(msg)

    if not LOG_SILENT:
        file.write(msg.__str__() + "\n")


def get_line_count(file):
    count = 0

    for line in file:
        count += 1

    file.seek(0)
    return count


def get_last_line_count(config):
    if not config.has_option("config", "line"):
        config.set("config", "line", 0)
        line_count = 0
    else:
        line_count = config.getint("config", "line")

    return line_count


def get_empty_since(config):
    if not config.has_option("config", "empty_since"):
        print(len(online_players), "online")
        empty_since = None if len(online_players) > 0 else datetime.now()
        config.set("config", "empty_since", "" if empty_since == None else format_time(empty_since))
        return empty_since

    empty_since = config.get("config", "empty_since")

    if len(empty_since) == 0:
        return None if len(online_players) > 0 else datetime.now()
    else:
        return datetime.strptime(empty_since, TIME_FORMAT)


def get_last_run(config):
    if not config.has_option("config", "last_run"):
        today = date.today()
        config.set("config", "last_run", today.strftime("%m/%d/%Y"))
        return today

    return datetime.strptime(config.get("config", "last_run"), "%m/%d/%Y").date()
        

def load_config():
    config = ConfigParser.ConfigParser()
    config.read(CONFIG)

    if not config.has_section("config"):
        config.add_section("config")

    if not config.has_option("config", "players"):
        config.set("config", "players", "[]")

    empty_since = get_empty_since(config)
    online_players = parse_set(config.get("config", "players"))
    line_count = get_last_line_count(config)
    last_run = get_last_run(config)

    return (config, (empty_since, online_players, line_count, last_run))


def save_config(filename, config):
    global empty_since

    config.set("config", "players", "[" + string.join(["'{}'".format(name) for name in online_players], ", ") + "]")
    config.set("config", "line", line_count)
    config.set("config", "empty_since", "" if empty_since == None else format_time(empty_since))
    config.set("config", "last_run", date.today().strftime("%m/%d/%Y"))

    file = open(filename, "w")
    config.write(file)
    file.close()


def open_log(file_name):
    #print("open_log", file_name)

    try:
        file = open(LOG_FILE if file_name == None else file_name)
    except IOError:
        print("Can't find " + LOG_FILE)
        sys.exit()

    return file


def open_output_log(filename):
    file = open(filename, "a")
    return file


def close_output_log(file):
    file.close()


def parse_arguments():
    global LOG_FILE, OUTPUT_LOG, CONFIG
    parser = argparse.ArgumentParser(description="Monitors the activity of a running Minecraft server")
    parser.add_argument("--reset", dest="reset", action="store_const", const=True, help="Forgets all data collected")
    parser.add_argument("--inactive", dest="inactive", action="store_const", const=True, help="Returns 1 if the server was already empty by the time the server was last backed up, 0 otherwise")
    parser.add_argument("--num-users", dest="num_users", action="store_const", const=True, help="Returns the number of players on the server")
    parser.add_argument("--inactive-since", dest="inactive_since", action="store_const", const=True, help="Prints the date and time the last player left the server")
    parser.add_argument("--conf", dest="conf")
    parser.add_argument("--log-file", dest="logfile", help="The Minecraft server log to read")
    parser.add_argument("--out", dest="outfile")

    args = parser.parse_args()

    if args.logfile:
        LOG_FILE = args.logfile

    if args.outfile:
        OUTPUT_LOG = args.outfile

    if args.conf:
        CONFIG = args.conf

    return args


def get_last_log(date):
    path, _ = os.path.split(LOG_FILE)
    log_prefix = date.strftime("%Y-%m-%d-")
    log_suffix = ".log.gz"

    gen = os.walk(path)
    logs = gen.next()[2]
    logs = filter(lambda x: x.startswith(log_prefix), logs)
    logs = map(lambda x: x[:(len(x) - x.find(".")) * -1], logs)
    max_log = reduce(lambda acc, val: max(val.split("-")[3]), logs, -1)

    return path + "/" + log_prefix + max_log + log_suffix

def read_log(date=None):
    global line_count

    file_name = None
    if date != None:
        file_name = get_last_log(date)
        os.spawnl("/bin/gunzip", "", file_name)

    file = open_log(file_name)

    # Skip old lines
    for i in range(0, line_count):
        line = file.readline()

    # Parse log entries and call hooks for recognized entries
    for line in file:
        line_count += 1
            
        line = RE_TIMESTAMP.match(line)
        if line == None:
            continue
                
        line_time = line.group("time")
        line = line.group("line")
                
        for name, expr, hook in REGEXES:
            #print(line)
            match = expr.match(line)
            if match:
                out_line = "[{0} {1}]\nmatched '{2}'".format(TODAY_F, line_time, name)
                log_echo(out_file, out_line)
                    
            for key, value in match.groupdict().items():
                prop = "\t{0}:\t{1}".format(key, value)
                log_echo(out_file, prop)

            log_echo(out_file)

            if hook != None:
                hook(match, datetime.strptime(TODAY_F + " " + line_time, "%m/%d/%Y %H:%M:%S"))
            break

    file.close()
    if file_name != None:
        os.spawnl("/bin/gzip ", "", file_name)


################################################################################

def hook_enter(match, time):
    global empty_since
    empty_since = None

    name = match.group("name")
    online_players.add(name)

    log_echo(out_file, "HOOK: enter ({0})".format(name))
    log_echo(out_file, online_players)
    log_echo(out_file)


def hook_leave(match, time):
    global empty_since
    empty_since = time

    name = match.group("name")
    if name in online_players:
        online_players.remove(name)

    log_echo(out_file, "HOOK: leave ({0})".format(name))
    log_echo(out_file, online_players)
    log_echo(out_file)


def time_of_last_backup():
    s = os.stat(UPLOAD_LOG)
    modified = datetime.fromtimestamp(s.st_mtime)
    return modified


REGEXES.append(("enter", RE_LOGIN, hook_enter))
REGEXES.append(("leave", RE_LOGOUT, hook_leave))
REGEXES.append(("disconnect", RE_DISCONNECT, None))


################################################################################

def main():
    global empty_since, online_players, line_count, last_run

    args = parse_arguments()

    config, options = load_config()
    empty_since, online_players, line_count, last_run = options

    if args.reset:
        line_count = 0

    if last_run < date.today():
        # A new log has started since we last ran. Finish reading the last one and start the next
        read_log(date.today() - timedelta(days=1))
        line_count = 0

    read_log()

    out_file = open_output_log(OUTPUT_LOG)
    close_output_log(out_file)
    save_config(CONFIG, config)

    if args.inactive_since:
        print(format_time(empty_since))

    elif args.inactive:
        # inactive = server was already empty before the last backup took place
        if empty_since != None and empty_since <= time_of_last_backup():
            code = 1
            print("There has been no activity since", format_time(empty_since))
        else:
            code = 0

        sys.exit(code)

    elif args.num_users:
        sys.exit(len(online_players))

if __name__ == "__main__":
    main()
