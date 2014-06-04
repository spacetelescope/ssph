"""
This module implements $DOCUMENTROOT/secure/ssph.cgi

During the SSO dance, the user is redirected here, bounced to the SSO
machine by the Apache module, logs in on the SSO, then is bounced back
here with valid authentication.  The authentication looks just like
HTTP BASICAUTH, except with more environment variables.

We store information about the Session Cookie provided by the SP and
the authentication information provided by the SSO system.  Later,
the SP confirms the authentication by looking up the database record
of the authentication event.

"""

import sys
import cgi
import os
import re
import json
import time

from ssph_server.db import core_db

def run() :
    ###
    # To get through all the redirects, we use a single parameter in a
    # GET-style CGI request.  After the authentication, that single parameter
    # comes here as sp=...

    data = cgi.FieldStorage()
    sp, cookie = data["sp"].value.split(",",1)
    # sp is the name of the service provider
    # cookie is the session cooke that the service provider created

    ###
    # look up information about the service provider
    c = core_db.execute("SELECT url, dbtype, dbcreds, expiry FROM ssph_sp_info WHERE sp = :1",(sp,))
    ans = c.fetchone()
    if ans is None :
        # hm - we do not know your SP; you lose.
        print "Content-type: text/plain"
        print ""
        print "Do not know your application ",sp
        return 0
    
    url, dbtype, dbcreds, expire = ans

    ###
    # url is where we will return the user to.  The SP will receive the
    # cookie in a GET transaction, and then can confirm that the cookie
    # now is associated with an authenticated user.
    url = url + "?c=" + cookie

    ###
    # info is all the information there is to report about the user.
    # It is all in environment variables.  I got this regex from Dan
    # Deighton when he set up my shibboleth-enabled apache server.
    info = { }
    shib_vars = re.compile("(STScI_|Shib_|[a-z_0-9])+")
    for x in os.environ :
      if shib_vars.match(x):
        info[x] = os.environ[x]

    ###
    # We store all the user info in a json block
    info = json.dumps( info )

    ###
    # We will put the information collected on the authenticated user
    # into a database table, indexed by Service Provider and session cookie.
    # There are two choices of database:
    #   - put it in our database ("ssph"); the SP needs read access to
    #     the ssph_auths table in our database.
    #   - put it into the SP's database.  We will need access/authentication
    #     to write to the ssph_auths table in the SP's database.
    if dbtype is None or dbtype == "ssph" :
        # if using our database, we just use the already open handle
        cdb = core_db
    else :
        # if using their database, we have to connect to it.
        # (exec is ok because we got dbtype from our own configuration data)
        exec "import pandokia.db_%s as client_dbm" % dbtype
        dbcreds = json.loads(dbcreds)
        cdb = client_dbm.PandokiaDB( dbcreds )

    ###
    # Delete the record that is already there and insert a new one.
    # The user may go through the auth path more than once, so this is
    # effectively an update without the complications.
    cdb.execute("""DELETE FROM ssph_auths
            WHERE sp = :1 AND cookie = :2
            """,
            ( sp, cookie )
        )
    cdb.execute("""INSERT INTO ssph_auths 
            ( sp, cookie, info, expire, idp, eppn )
            VALUES ( :1, :2, :3, :4, :5, :6 )""",
            ( sp, cookie, info, time.time() + expire,
                os.environ["Shib_Identity_Provider"],
                os.environ["eppn"]
            )
        )

    cdb.commit()

    ###
    # after the database commit, we are done.  Redirect the user back
    # to the SP.

    print "Status: 303 See Other"
    print "Location:",url
    print ""

    return 0
