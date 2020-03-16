#!/internal/data1/other/tp_9.4/envs/pandeia_9.4/bin/python
# This hook is modified and used for each cgi that gets installed
import sys
sys.path.append("/internal/data1/other/pylibs/ssph")

import os
import ssph_server.confirm as r
sys.exit(r.run())

