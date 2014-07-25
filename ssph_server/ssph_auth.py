"""
This module implements $DOCUMENTROOT/secure/ssph_auth.cgi?sp=SPNAME

During the SSO dance, the user is directed here, bounced to the SSO
machine by the Apache module, logs in on the SSO, then is bounced back
here with valid authentication.  The authentication looks just like
HTTP BASICAUTH, except with more environment variables.

We create a magic cookie that we send to the SP via a GET-type redirect,
and then store the authentication information associated with that
cookie in the authorization table.

When the SP gets the return_url loaded, it uses the magic cookie in
in the URL to find the authentication record in the database.

If the SP receives a session cookie:
    if the identity declared by SSPH is the same as the identity declared by the session cookie:
        extend the expiration of the session cookie
    else :
        revoke the existing session cookie
        return a display saying "you are no longer XXX, you are YYY; click to proceed"
        create and issue a session cookie
else:
    create and issue a session cookie


"""

import sys
import cgi
import os
import re
import json
import time
import datetime

from ssph_server.db import core_db

# This creates an identifier for the newly authenticated session.
#
# I guess I could include a serial number, but getting the same two
# 48 bit strings out of /dev/urandom in the same 0.1 second interval?
# Seems pretty unlikely.
def get_auth_event_id() :
    import binascii
    # os.urandom gets that many bytes from /dev/urandom
    return binascii.b2a_hex(os.urandom(48)) + ( "%08x" % (time.time()*10) )

###
# function to insert an authentication event into the database table
def insert( db, tyme, sp, auth_event_id, attribs ) :
    db.execute(
        """INSERT INTO ssph_auth_events ( tyme, sp, auth_event_id, client_ip, idp, eppn, attribs )
        VALUES ( :1, :2, :3, :4, :5, :6, :7 ) """,
        ( tyme, sp, auth_event_id, os.environ['REMOTE_ADDR'],
            os.environ["Shib_Identity_Provider"], os.environ["eppn"], attribs ) 
        )
    db.commit()

def run() :
    # To get through all the redirects, we use a single parameter in a
    # GET-style CGI request.  After the authentication, that single parameter
    # comes here as sp=... giving the name of the service provider that is
    # requesting service.

    data = cgi.FieldStorage()
    if "sp" in data :
        sp = data["sp"].value.strip()
    else :
        print "Content-type: text/plain"
        print ""
        print "SSO did not return the SP field"
        print "CGI ARGS"
        for x in data :
            print data[x].value
        print "ENVIRONMENT"
        for x in sorted( [x for x in os.environ] ):
            print "%s=%s"%(x,os.environ[x])
        return 0
    
    # sp is the name of the service provider

    ###
    # look up information about the service provider

    c = core_db.execute("SELECT url, dbtype, dbcreds, expiry FROM ssph_sp_info WHERE sp = :1",(sp,))
    ans = c.fetchone()
    if ans is None :
        # hm - we do not know your SP; you lose.
        print "Content-type: text/plain"
        print ""
        print "Do not know your application: ",sp
        # bug: log the attack here.
        return 0
    
    url, dbtype, dbcreds, expire = ans


    ###
    # auth_event_id is a unique and crypto-strong random identifier for
    # this authentication event.

    auth_event_id = get_auth_event_id()

    ###
    # url is where we will return the user to.  
    url = url + "?evid=" + auth_event_id

    ###
    # info is all the information there is to report about the user.
    # It is all in environment variables.  I got this regex from Dan
    # Deighton when he set up my shibboleth-enabled apache server.
    attribs = { }
    shib_vars = re.compile("(STScI_|Shib_|[a-z_0-9])+")
    for x in os.environ :
      if shib_vars.match(x):
        attribs[x] = os.environ[x]

    ###
    # We store all the user attribs in a json block
    attribs = json.dumps( attribs )

    tyme = datetime.datetime.utcnow().isoformat(' ')


    ###
    # log the authentication event in our table
    insert( core_db,  tyme, sp, auth_event_id, attribs  )

    ###
    # If the SP wants us to put it into their database, do that too
    if dbtype != "ssph" :
        # if using their database, we have to connect to it.
        # (exec is ok because we got dbtype from our own configuration data)
        exec "import pandokia.db_%s as client_dbm" % dbtype
        dbcreds = json.loads(dbcreds)
        cdb = client_dbm.PandokiaDB( dbcreds )

        insert( cdb,  tyme, sp, auth_event_id, attribs  )

    ###
    # Redirect the user back to the SP.
    print "content-type: text/plain"
    print ""
    print url

    print "Status: 303 See Other"
    print "Location:",url
    print ""

    return 0
