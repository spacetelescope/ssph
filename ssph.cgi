#!PYTHON
# This hook is modified and used for each cgi that gets installed
import sys
import cgitb
cgitb.enable()

if "LBRYPATH" != "" :
	import os
	x=os.environ.get("LD_LIBRARY_PATH",None)
	if x :
		os.environ["LD_LIBRARY_PATH"] = x + ":LBRYPATH"
	else :
		os.environ["LD_LIBRARY_PATH"] = "LBRYPATH"

sys.path.insert( 0, "SSPH_PYTHON_PATH" )

import ssph_server.MODULE as r
sys.exit( r.run() )

