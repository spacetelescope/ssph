"""
This module implements $DOCUMENTROOT/unsecured/ssph_confirm.cgi; 

Service Providers ask this CGI to confirm that a user is authenticated,
and to fetch the information returned by the authentication.  Since
this URL is only used by the SPs, we know they must be within our
service net.  Any request from outside our service net is an attack.

For extra bonus security, we could keep an IP list of servers that
host each SP, but I don't think it is worth the extra work.

"""
import cgi
import hashlib
import json
import os
import sys
import ipaddr

from ssph_server.db import core_db

debug = True

#####
#
# Call this function whenever you think the client is doing something
# odd enough to be worth logging/alerting for.
#

def _barf(message) :
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
    user = os.environ["REMOTE_USER"]
        # yes, I know we can't trust REMOTE_USER, but we might as well
        # gather it in case the attacker is stupid, or is not really
        # an attacker.

    # log to the apache error log
    sys.stderr.write(
        "\n\n\nATTACK ON SSPH? date: %s from: %s %s to: %s type: %s\n\n\n" 
        % (datetime.datetime.now().isoformat(), remote, user, server, message) 
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

    ### write your own if statements here

    if not ipaddr.ip_address(remote_addr) in ipaddr.IPNetwork(service_net) :
        _barf()
        sys.exit(1)
    
    ###

    # Collect the fields of the query that was passed by the client.
    # Quietly ignore unexpected fields.
    data = cgi.FieldStorage()
    sp = data["sp"].value
        # the name of the SP that is the client here
    auth_event_id = data["auth_event_id"].value
        # the session auth_event_id being validated
    garbage = data["garbage"].value
        # garbage is a salt chosen by the client.  It makes it 
        # slightly more difficult to attack the shared secret by
        # intercepting multiple transactions
    signature = data["sig"].value
        # the hash computed by the client of the input for this request

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
    # a database somewhere and not using this interface.  If the SP
    # is not expected to use the CGI, then we do not need to allow
    # this as an attack vector.

    if dbtype != "ssph" :
        # if this
        _barf(data, "mode")
        return 1

    ###
    # The client examples use the secret 12345678.  A production SSPH
    # should not permit the default value in the example.  It's too
    # much like setting your password to "password"

    if not debug :
        if secret == "12345678" :
            print "content-type: text/plain\n\nbarf\n"
            print "---\n\nreally? you used the default secret in non-debug mode???\n\n---"
        return 1

    ###
    # The different clients can be configured for different hash
    # algorithms.  Use the coolest one that the client supports.
    # Notice that the choice of hash algorithms is in the SSPH
    # database, so in principle you will never encounter this
    # case, but mistakes happen.
    try :
        hash_ok = hash in hashlib.algorithms
    except AttributeError :
        # python 2.6
        hash_ok = hash in ( "md5", "sha1", "sha224", "sha256", "sha384", "sha512" )

    if not hash_ok :
        _barf(data, "hash")
        return 1

    ###
    # compute the signature of the request

    # exec is ok because we know that hash is one of the strings from
    # hashlib.algorithms
    exec "m = hashlib.%s()" % hash
    m.update(garbage)
    m.update(" ")
    m.update( sp )
    m.update(" ")
    m.update( auth_event_id )
    m.update(" ")
    m.update( secret )

    ###
    # compare the submitted signature of the request to the computed signature

    if signature != m.hexdigest() :
        # the client does not know its own secret
        _barf(data, "hash-match")
        return 1

    ###
    # Look up the authentication cookie in the table of recent
    # authentications.  It should be impossible for the client to ask for
    # a cookie that has not been successfully authenticated.  That would
    # imply either a buggy SP or an attack.
    c = core_db.execute("""SELECT attribs FROM ssph_auths
            WHERE auth_event_id = :1 AND sp = :2 """,
            ( auth_event_id, sp )
        )
    ans = c.fetchone()
    if ans is None :
        _barf("cookie-missing")
        return 1

    # Finally, we have the information we are searching for.  This is
    # the data that was stored when the user was initially authenticated.
    attribs = ans[0].strip()

    ###
    # sign the returned info with the same shared secret so the client
    # knows it really came from us.  There is no salting here because
    # the client has already proven that it knows the secret.
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

