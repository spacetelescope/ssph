#!PYTHON
# This hook is placed in /secure/return.cgi on the Shibboleth-enabled
# Apache server.  It is modified for the path where the python
# and the ssph package are stored.
import sys
import cgitb
cgitb.enable()

sys.path.insert( 0, "SSPH_PYTHON_PATH" )
import ssph.return_
sys.exit( ssph.return_.run() )
