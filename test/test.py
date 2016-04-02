#!/usr/bin/python

from datetime import datetime
import os
import sys

import script


################################################################################

if len(sys.argv) < 2:
    sys.exit()

test_script = sys.argv[1]
dot = test_script.find(".")
test_base = test_script if dot == -1 else test_script[:dot]
script_out = test_base + ".log"
out_log = test_base + "-activity.log"
out_conf = test_base + ".config"

script = script.TestScript(sys.argv[1])
f = open(script_out, "w")
script.render_all(f)
f.close()

os.spawnl(os.P_WAIT, "./activity-monitor.py", "", "--log-file=" + script_out, "--conf=" + out_conf, "--out=" + out_log)
