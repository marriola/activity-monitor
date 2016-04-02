from datetime import datetime
import re


################################################################################

RE_TIME = re.compile("(?P<hour>\\d+):(?P<minute>\\d+)")


################################################################################

class TestAction(object):
    def __init__(self, time, player):
        self.time = time
        self.player = player

    @classmethod
    def build(cls, date, line):
        player = line[1]
        m = RE_TIME.match(line[0])
        time = datetime(date.year, date.month, date.day, int(m.group("hour")), int(m.group("minute")))                

        return cls(time, player)

    def render(self):
        return ""


class InfoAction (TestAction):
    def __init__(self, time, player):
        super(InfoAction, self).__init__(time, player)

    def render(self):
        return self.time.strftime("[%H:%M:00] [Server thread/INFO]: ")


class EnterAction (InfoAction):
    def __init__(self, time, player):
        super(EnterAction, self).__init__(time, player)

    @classmethod
    def build(cls, date, line):
        return super(EnterAction, cls).build(date, line)

    def render(self):
        return super(EnterAction, self).render() + "{}[/127.0.0.1:12345] logged in with entity id 0 at ([world]0.0, 0.0, 0.0)".format(self.player)


class DisconnectAction (InfoAction):
    def __init__(self, time, player, reason):
        super(DisconnectAction, self).__init__(time, player)
        self.reason = reason

    @classmethod
    def build(cls, date, line):
        obj = super(DisconnectAction, cls).build(date, line)
        obj.reason = reason

    def render(self):
        return super(DisconnectAction, self).render() + "{} lost connection: {}".format(self.player, self.reason)


class LeaveAction (InfoAction):
    def __init__(self, time, player):
        super(LeaveAction, self).__init__(time, player)

    @classmethod
    def build(cls, date, line):
        return super(LeaveAction, cls).build(date, line)

    def render(self):
        return super(LeaveAction, self).render() + "{} left the game.".format(self.player)
