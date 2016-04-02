from datetime import datetime
import re
import sys

from action import EnterAction, DisconnectAction, LeaveAction


################################################################################

RE_DATE = re.compile("(?P<month>\\d+)/(?P<day>\\d+)/(?P<year>\\d+)")


################################################################################

class TestScript(object):
    def __init__(self, file):
        self.actions = []
        self.__parse(file)

    def render_all(self, out=sys.stdout):
        for action in self.actions:
            out.write(action.render() + "\n")

    def __parse(self, file):
        line_no = 1
        date = None

        def __parse_action_list(self, file, date):
            lines = 0

            for line in f:
                if len(line.strip()) == 0:
                    break

                line = map(lambda x: x.strip(), line.split(","))
                name = line[2]
                action = None

                if name == "enter":
                    action = EnterAction.build(date, line)
                elif name == "disconnect":
                    action = DisconnectAction.build(date, line)
                elif name == "leave":
                    action = LeaveAction.build(date, line)

                self.actions.append(action)
                lines += 1

            return lines

        f = open(file)

        for line in f:
            m = RE_DATE.match(line)
            
            if None in m.groups():
                print "Malformed date on line", line_no
                continue

            date = datetime(int(m.group("year")), int(m.group("month")), int(m.group("day")))
            line_no += __parse_action_list(self, file, date)

        f.close()
