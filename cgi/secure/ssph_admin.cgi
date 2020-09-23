#!/internal/data1/other/tp_11/envs/pandeia_11/bin/python
# This hook is modified and used for each cgi that gets installed
import sys
sys.path.append("/internal/data1/other/pylibs/ssph")

import sys
import os
import ssph_server.admin as r
sys.exit(r.run())

