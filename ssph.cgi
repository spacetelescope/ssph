#!PYTHON
# This hook is placed in /secure/return.cgi on the Shibboleth-enabled
# Apache server.  It is modified for the path where the python
# and the ssph package are stored.
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
import ssph_server.return_ as r
sys.exit( r.run() )

