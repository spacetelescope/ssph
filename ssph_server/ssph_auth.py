"""
This module implements $DOCUMENTROOT/secure/ssph_auth.cgi?sp=SPNAME

During the SSO dance, the user is directed here, bounced to the SSO
machine by the Apache module, logs in on the SSO, then is bounced back
here with valid authentication.  The authentication looks just like HTTP
BASICAUTH to us, except that there are more environment variables.

We create a magic cookie (not a web cookie) that identifies this
authentication event.  We store the magic cookie and the authentication
even in the authorization table in the database, then use a GET-type
redirect to send the user back to the return_url of the requesting
application.

When the SP gets the return_url loaded, it uses the magic cookie in
in the URL to find the authentication record in the database.

If the SP receives a session cookie:
    if the identity declared by SSPH is the same as the identity declared by the session cookie:
        extend the expiration of the session cookie
    else :
        revoke the existing session cookie
        create and issue a session cookie
        return a display saying "you are no longer XXX, you are YYY; click to proceed"
else:
    create and issue a session cookie


"""
# In debug mode, we'll tell a client how they messed up.  Otherwise,
# they get nothing but blanks.

debug = True

import sys
import cgi
import os
import re
import json
import time
import datetime

from ssph_server.db import core_db
from ssph_server.validate_sp_ip import validate_ip

if debug:
    import cgitb
    cgitb.enable()

# This function creates an identifier for the newly authenticated session.
#
# I guess I could include a serial number, but getting the same two
# 48 bit strings out of /dev/urandom in the same 0.15 second interval?
# Seems pretty unlikely.
def get_auth_event_id() :
    import binascii
    # os.urandom gets that many bytes from /dev/urandom
    # Using %010x gets us an extra digit (from multiplying by 7)
    # and gets us past the 2038 problem (one more digit after 32 bits)
    # without the string growing.  The total returned string is 48*2+10=106
    # hex characters.
    # b.t.w.  The weakest part of this is /dev/urandom on machines that
    # don't have hardware random numbers.
    return binascii.b2a_hex(os.urandom(48)) + ( "%010x" % (time.time()*7) )

###
# function to insert an authentication event into the database table
def insert_auth( db, tyme, sp, auth_event_id, attribs ) :
    db.execute(
        """INSERT INTO ssph_auth_events ( tyme, sp, auth_event_id, client_ip, idp, eppn, attribs )
        VALUES ( :1, :2, :3, :4, :5, :6, :7 ) """,
        ( tyme, sp, auth_event_id, os.environ['REMOTE_ADDR'],
            os.environ["Shib_Identity_Provider"], os.environ["eppn"], attribs ) 
        )
    db.commit()

###
#
# The main program
#
def run() :
    # To get through all the redirects from the SP, through Shibboleth, and back
    # to here, we use a single parameter in a GET-style CGI request.
    # After the authentication, that single parameter comes here as
    # sp=... giving the name of the service provider that is requesting
    # service.

    data = cgi.FieldStorage()
    if "sp" in data :
        sp = data["sp"].value.strip()
    else :
        print "Content-type: text/plain"
        print ""
        if debug :
            print "SSO did not return the SP field"
            print "CGI ARGS"
            for x in data :
                print data[x].value
            print "ENVIRONMENT"
            for x in sorted( [x for x in os.environ] ):
                print "%s=%s"%(x,os.environ[x])
        return 0
    
    # sp is now the name of the service provider


    ###
    # look up information about the service provider

    c = core_db.execute("SELECT url, dbtype, dbcreds, expiry FROM ssph_sp_info WHERE sp = :1",(sp,))
    ans = c.fetchone()
    if ans is None :
        # hm - we do not know your SP; you lose.
        print "Content-type: text/plain"
        print ""
        if debug :
            print "Do not know your application: ",sp
        # bug: log the attack here.
        return 0

    validate_ip( sp )
    
    return_url, dbtype, dbcreds, expire = ans

    ###
    # auth_event_id is a crypto-strong random identifier for this
    # authentication event.  It has so many random bits that we assume it
    # is unique.

    auth_event_id = get_auth_event_id()

    ###
    # url is where we will return the user to.  It is the part of the
    # SP that receives the authentication event.
    return_url = return_url + "?evid=" + auth_event_id

    ###
    # attribs is all the information there is to report about the user.
    # It is all in environment variables.  I got this regex from Dan
    # Deighton when he set up my shibboleth-enabled apache server for
    # testing.
    attribs = { }
    shib_vars = re.compile("(STScI_|Shib_|[a-z_0-9])+")
    for x in os.environ :
      if shib_vars.match(x):
        attribs[x] = os.environ[x]

    ###
    # We store all the user attribs in a json block
    attribs = json.dumps( attribs )

    ###
    # We store the time of the authentication event in ISO format,
    # but with a space instead of a 'T'.  Use UTC to avoid worrying
    # about time zones.
    tyme = datetime.datetime.utcnow().isoformat(' ')

    ###
    # log the authentication event in our table
    insert_auth( core_db,  tyme, sp, auth_event_id, attribs  )

    ###
    # If the SP wants us to put it into their database, do that too
    if dbtype != "ssph" :
        # if using the SP's database, we have to connect to it.
        # (exec is ok because we got dbtype from our trusted configuration data)
        exec "import pandokia.db_%s as client_dbm" % dbtype
        dbcreds = json.loads(dbcreds)
        cdb = client_dbm.PandokiaDB( dbcreds )

        insert_auth( cdb,  tyme, sp, auth_event_id, attribs  )

    ###
    # Redirect the user back to the SP.

    if debug:
        print "content-type: text/plain"
        print ""
        print url

    print "Status: 303 See Other"
    print "Location:",url
    print ""

    return 0

