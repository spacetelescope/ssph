#!/internal/data1/other/third_party/envs/pandeia_13/bin/python
# This hook is modified and used for each cgi that gets installed
import sys
sys.path.append("/internal/data1/other/pylibs/ssph")

import os
import ssph_server.ssph_auth as r

sys.exit(r.run())

