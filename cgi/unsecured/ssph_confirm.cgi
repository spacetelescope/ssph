#!/internal/data1/other/third_party/envs/pandeia_13/bin/python
# This hook is modified and used for each cgi that gets installed
import sys
sys.path.append("/internal/data1/other/pylibs/ssph")

import os
import ssph_server.confirm as r

with open('/home/svc_ssph/logs.log','w') as logfile:
    logfile.write("We are here!!!")

sys.exit(r.run())

