#!PYTHON
# This hook is modified and used for each cgi that gets installed
import sys
import os
import ssph_server.MODULE as r
sys.exit( r.run() )

