"""
This module implements $DOCUMENTROOT/unsecured/ssph_confirm.cgi;

Service Providers ask this CGI to confirm that a user is authenticated,
and to fetch the information returned by the authentication.  Since
this URL is only used by the SPs, we know they must be within our
service net.  Any request from outside our service net is an attack.

For extra bonus security, we could keep an IP list of servers that
host each SP, but I don't think it is worth the extra work.

"""
import logging
import cgi
import hashlib
import json
import os
import sys
import ipaddr
import datetime
import iso8601
import pytz

urlfile = '/internal/data1/other/pylibs/ssph/ssph_server/urllist.json'

with open(urlfile,'r') as servicefile:
    service_net = json.load(servicefile)

# bug: refuse auth for evid that is too old
# bug: refuse auth for evid that was used before

from ssph_server.db import core_db
logging.basicConfig(filename='ssph.log', level=logging.DEBUG)

debug = True

#####
#
# Call this function whenever you think the client is doing something
# odd enough to be worth logging/alerting for.
#

def _barf(data, message) :
    # if there is a reason to barf, we will just tell the client "barf"
    print "Content-type: text/plain"
    print ""
    print "barf"

    # in debug mode, we will give a little more information.  This is
    # mainly for testing SSPH, not for clients.
    if debug :
        print message

    # Who is the remote?  Who are we?  Who did it?  Log all of these.
    remote = os.environ["REMOTE_ADDR"]
    server = os.environ["SERVER_ADDR"]

    # log to the apache error log
    sys.stderr.write(
        "\n\n\nERROR IN SSPH? date: %s from: %s to: %s type: %s\n\n"
        % (datetime.datetime.now().isoformat(' '), remote, server, message)
        )
    sys.stderr.flush()

    # add your own alerting here if you want some.

    return


#####
#
# The CGI calls this function; all the work happens here.
#
#

def run() :

    # checking that the client is in the network range that we expect
    # to serve
    remote_addr = os.environ["REMOTE_ADDR"]

    ###

    # Collect the fields of the query that was passed by the client.
    # Quietly ignore unexpected fields.
    data = cgi.FieldStorage()

    sp = data["sp"].value
        # the name of the SP that is the client here
    evid = data["evid"].value
        # the session authentication event id being validated
    signature = data["sig"].value
        # the hash computed by the client of the input for this request

    ### write your own if statements here
    match = False
    # service_net is now a dictionary, but we only want the values
    for url in service_net.values():
        if ipaddr.IPv4Address(remote_addr) in ipaddr.IPNetwork(str(url)) :
	    match = True
    if not match:
        logging.debug('Address: {}'.format(ipaddr.IPv4Address(remote_addr)))
        logging.debug(ipaddr.IPNetwork(str(url)))
        _barf(data,'ip-mismatch')
        sys.exit(1)

    ###
    # look up information about the service provider

    c = core_db.execute("SELECT dbtype, secret, hash FROM ssph_sp_info WHERE sp = :1",(sp,))
    ans = c.fetchone()
    if ans is None :
        # The service provider is not known to us.  We cannot proceed.
        # (Also, unknown SP should not make requests.)
        _barf(data, "sp-unk")
        return 1

    dbtype, secret, hash = ans

    ###
    # This service provider is expected to use CGI confirmations?
    # If we do not expect it, then the SP should be looking directly into
    # its own database and not using this interface.  If the SP is not
    # expected to use the CGI, then we do not need to allow this as a
    # potential attack vector.

    if dbtype != "ssph" :
        # if this
        _barf(data, "mode")
        return 1

    ###
    # The demo use the secret 12345678.  A production SSPH
    # should not permit the demo value in the example.  It's too
    # much like setting your password to "password"

    if not debug :
        if secret == "12345678" :
            print "content-type: text/plain\n\nbarf\n"
            print "---\n\nreally? you used the demo secret in non-debug mode???\n\n---"
        return 1

    ###
    # The different clients can be configured for different hash
    # algorithms.  Use the coolest one that the client supports.
    try :
        hash_ok = hash in hashlib.algorithms
    except AttributeError :
        # python 2.6
        hash_ok = hash in ( "md5", "sha1", "sha224", "sha256", "sha384", "sha512" )

    if not hash_ok :
        # Notice that the choice of hash algorithms is in the SSPH
        # database, so in principle you will never encounter this
        # case, but mistakes happen.
        logging.debug("hash: {}".format(hash))
        _barf(data, "hash")
        return 1

    ###
    # compute the signature of the request

    # exec is ok because we know that hash is one of the strings from
    # hashlib.algorithms
    exec "m = hashlib.%s()" % hash
    m.update( sp )
    m.update(" ")
    m.update( evid )
    m.update(" ")
    m.update( secret )

    ###
    # compare the submitted signature of the request to the computed signature

    if signature != m.hexdigest() :
        # the client does not know its own secret
        logging.debug("hash-match: {}, {}".format(signature, m.hexdigest()))
        _barf(data, "hash-match")
        return 1

    ###
    # Look up the authentication cookie in the table of recent
    # authentications.  It should be impossible for the client to ask for
    # a cookie that has not been successfully authenticated.  That would
    # imply either a buggy SP or an attack.
    c = core_db.execute("""SELECT tyme, attribs FROM ssph_auth_events
            WHERE auth_event_id = :1 AND sp = :2 AND consumed = 'N' """,
            ( evid, sp )
        )
    ans = c.fetchone()
    if ans is None :
        _barf(data, "cookie-missing")
        return 1

    # Finally, we have the information we are searching for.  This is
    # the data that was stored when the user was initially authenticated.
    tyme, attribs = ans

    ###
    # if it took the SP more than 5 minutes to check up on this user, I
    # think something funky is going on.
    timeobj = datetime.timedelta(datetime.datetime.now(pytz.utc).second - iso8601.parse_date(tyme).second)
    if timeobj.total_seconds() > 300:
        core_db.execute(
            "UPDATE ssph_auth_events SET consumed = 'E' WHERE auth_event_id = :1 AND sp = :2",
            ( evid, sp )
            )
        core_db.commit()
        logging.debug("expired: {}".format(timeobj.total_seconds()))
        _barf(data, "expired" )
        return 1

    ###
    # we have used this authentication record.  It may not be used again.
    core_db.execute(
        "UPDATE ssph_auth_events SET consumed = 'Y' WHERE auth_event_id = :1 AND sp = :2",
        (  evid, sp )
        )
    core_db.commit()

    ###
    # sign the returned info with the same shared secret so the client
    # knows it really came from us.
    exec "m = hashlib.%s()" % hash
    m.update(attribs)
    m.update(' ')
    m.update(secret)
    signature = m.hexdigest()

    ###
    # send back 1 line of signature, then arbitrarily long information.
    # (in practice, it is usually a single line of json, but it might
    # be multi-line if somebody pretty printed it into the database.)
    print "content-type: text/plain"
    print ""
    print signature
    print attribs
    return 0
