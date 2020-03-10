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
    else:
        revoke the existing session cookie
        create and issue a session cookie
        return a display saying "you are no longer XXX, you are YYY; click to proceed"
else:
    create and issue a session cookie


"""
# In debug mode, we'll tell a client how they messed up.  Otherwise,
# they get nothing but blanks.
debug = False

import sys
import cgi
import os
import re
import json
import time
import datetime
import re

from ssph_server.db import core_db

if debug:
    import cgitb
    cgitb.enable()

# This function creates an identifier for the newly authenticated session.
#
# I guess I could include a serial number, but getting the same two
# 48 bit strings out of /dev/urandom in the same 0.15 second interval?
# Seems pretty unlikely.
def create_auth_event_id():
    import binascii
    # os.urandom gets that many bytes from /dev/urandom
    # Using %010x gets us an extra digit (from multiplying by 7)
    # and gets us past the 2038 problem (one more digit after 32 bits)
    # without the string growing.  The total returned string is 48*2+10=106
    # hex characters.
    # b.t.w.  The weakest part of this is /dev/urandom on machines that
    # don't have hardware random numbers.
    # BUG: the x format statement can only translate integers on Python 3
    return str(binascii.b2a_hex(os.urandom(48))) + ("{:010x}".format(int(time.time()*7)))

###
# function to insert an authentication event into the database table
def insert_auth(db, tyme, sp, auth_event_id, attribs, consumed):
    db.execute(
        """INSERT INTO ssph_auth_events ( tyme, sp, auth_event_id, client_ip, idp, stsci_uuid, attribs, consumed )
        VALUES ( :1, :2, :3, :4, :5, :6, :7, :8 ) """,
        (tyme, sp, auth_event_id, os.environ['REMOTE_ADDR'],
            os.environ["Shib_Identity_Provider"], os.environ["STScI_UUID"], attribs, consumed)
        )
    db.commit()

###
#
# The main program
#
def run():
    # To get through all the redirects from the SP, through Shibboleth, and back
    # to here, we use a single parameter in a GET-style CGI request.
    # After the authentication, that single parameter comes here as
    # sp=... giving the name of the service provider that is requesting
    # service.

    data = cgi.FieldStorage()

    if "sp" in data:
        sp = data["sp"].value.strip()
    else:
        print("Content-type: text/plain\n")
        if debug:
            print("SSO did not return the SP field")
            print("CGI ARGS")
            for x in data:
                print(data[x].value)
            print("ENVIRONMENT")
            for x in sorted([x for x in os.environ]):
                print("%s=%s"%(x,os.environ[x]))
        sys.exit()

    # sp is now the name of the service provider

    # validate sp; make sure the string only contains alphanumeric characters,
    # dashes, underscores, and periods
    if not re.match("^[A-Za-z0-9_:.-]*$", sp):
        sys.exit(1)

    ###
    # look up information about the service provider
    c = core_db.execute("SELECT url, dbtype, dbcreds FROM ssph_sp_info WHERE sp = :1",(sp,))
    ans = c.fetchone()

    if ans is None:
        # hm - we do not know your SP; you lose.
        print("Content-type: text/plain\n")
        if debug:
            print("Do not know your application: ",sp)
        sys.stderr.write(
            "\n\n\SSPH: unknown SP %s date: %s\n\n\n"
            % (sp, datetime.datetime.now().isoformat())
            )
        sys.stderr.flush()

        sys.exit()

    return_url, dbtype, dbcreds = ans

    ###
    # auth_event_id is a crypto-strong random identifier for this
    # authentication event.  It has so many random bits that we assume it
    # is unique.

    auth_event_id = create_auth_event_id()

    ###
    # a note about session fixation:  Eve could log in here and get
    # a valid evid.  She could then use a session fixation attack to
    # cause Alice to log in as Eve by tricking her into using the
    # evid that was issued to Eve. Alice is then logged in as Eve, which
    # presumably would raise some red flags when Alice returns to the
    # application and sees "You are logged in as Eve".  The link that
    # Eve provides has to go directly to the SP return_url.
    #
    # If Alice then uploads some valuable data, then Eve can log in
    # another session to see it.  In the event that Alice does not
    # notice she is logged in as Eve, she will also wonder where her
    # data went next time she logs in.
    #
    # You could probably guard against this by having the SP make
    # a crypto-cookie and passing it to SSPH.  Then you look for the same
    # crypto-cookie coming back when loading the return_url on the SP and
    # checking that the incoming evid matches the original crypto-cookie.
    #
    # I may come back and add this feature later, but this is insufficiently
    # high risk for me to be concerned about how.

    ###
    # url is where we will return the user to.  It is the part of the
    # SP that receives the authentication event.
    return_url = return_url + "?evid=" + auth_event_id

    sys.stderr.write("\n\n%s" % (return_url))
    sys.stderr.flush()


    ###
    # attribs is all the information there is to report about the user.
    # It is all in environment variables.  I got this regex from Dan
    # Deighton when he set up my shibboleth-enabled apache server for
    # testing: "(STScI_|Shib_|[a-z_0-9])+"
    # In fact, I don't think that is really the right way to do it,
    # so I'm using the regex below.  Starts with STScI_ or starts
    # with Shib_ or starts with a lower case letter or starts with _ .
    # The rest is a letter, digit, _ or - .
    attribs = {}
    shib_vars = re.compile("^(STScI_|Shib_|[a-z_])[A-Za-z0-9_-]*")
    for x in os.environ:
        if shib_vars.match(x):
            attribs[x] = os.environ[x]

    ###
    # We store all the user attribs in a json block
    attribs = json.dumps(attribs)

    ###
    # We store the time of the authentication event in ISO format,
    # but with a space instead of a 'T'.  Use UTC to avoid worrying
    # about time zones.
    tyme = datetime.datetime.utcnow().isoformat(' ')

    sys.stderr.write(tyme)
    sys.stderr.flush()

    if dbtype == "ssph":

        ###
        # log the authentication event in our table. it is not consumed
        insert_auth(core_db, tyme, sp, auth_event_id, attribs, 'N')

    else:
        ###
        # If the SP wants us to put it into their database, enter it in
        # our database in the SP database.

        # consumed=D to indicate that the CGI authenticator should never
        # see a request to validate this authentication event.
        insert_auth(core_db, tyme, sp, auth_event_id, attribs, 'D')

        # if using the SP's database, we have to connect to it.
        # (exec is ok because we got dbtype from our trusted configuration data)
        exec("import pandokia.db_%s as client_dbm" % dbtype)
        dbcreds = json.loads(dbcreds)
        cdb = client_dbm.PandokiaDB( dbcreds )

        insert_auth(cdb, tyme, sp, auth_event_id, attribs)


    ###
    # Redirect the user back to the SP.

    print("Status: 303 See Other\nLocation: {}\n".format(return_url))

    sys.exit()
