#!/usr/bin/env python

# set the url of the SSPH server
ssph_url = 'https://etcbrady.stsci.edu'

# select one of these methods of confirming the identity of the user
# who logged in.
if 0 :
    # SSPH inserts the authentication into your database
    confirm_mode = 'db'
    my_sp_name = 'ssph_demo_db'

if 1 :
    # you ask SSPH for the authentication information
    confirm_mode = 'cgi'
    my_sp_name = 'ssph_demo_cgi'
    ssph_confirm_url = ssph_url+'/unsecured/ssph_confirm.cgi'


# This is the database used by this demo application, no matter which
# confirmation method you choose above.
import etc_utils.db_mysqldb

db = etc_utils.db_mysqldb.PandokiaDB(
    {
    "host"      : "banana.stsci.edu",
    "user"      : "ssph_demo_user",
    "passwd"    : "some long password",
    "db"        : "ssph_demo",
    }
    )

# notice that this application does not use SSL, and therefore is
# inherently insecure.  I just don't want to get in to the difficulty of
# making this work with SSL.  Your app necessarily will have to have
# SSL (well, really TLS), but the interaction with SSPH is the same.

### end of configurable data

import os
import os.path
import sys
import binascii
import cgi
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

#######

from tornado.options import define, options

define("port", default=4460, help="run on the specified port", type=int)

import platform, os, time


# the name of the session cookie
# note: look in to httponly=true, secure=true for the cookie

session_cookie_name='demo_session'

#####
# object that performs the get/posts
import string

class AppVector(tornado.web.RequestHandler) :

    def get(self, *args, **kwargs):
        url = args[0]

        # Notice that we still have the database open, and mysql normally
        # runs in REPEATABLE READ mode.  Since our last select, we have been
        # in a transaction.  In principle, you should end the transaction
        # when you are done handling a request, but this ensures that
        # the transaction is always ended before we start on a new task.
        db.rollback()

        # n.b. According to this, MS SQL SERVER behaves like the mysql
        # READ COMMITTED.  Postgres defaults to like REPEATABLE READ.
        # http://www.databasejournal.com/features/mysql/article.php/3393161/MySQL-Transactions-Part-II---Transaction-Isolation-Levels.htm

        ####
        #### you noticed this is a demo, right?  Don't do this in your real app.
        ####
        if url == '/t' :
            c = db.execute("SELECT auth_event_id, idp, eppn FROM ssph_auth_events order by tyme")
            for x in c :
                print x
            c.close()
            db.rollback()
            return

        # initializing these so they can be included in the template
        # expansions even if we don't use them
        auth = 'N'
        idp = 'none'
        eppn = 'none'
        err = 'none'
        msg = 'none'

        #####
        # returning from SSPH with a confirmed login
        if url == '/login_return.html' :
            evid = self.get_arguments('evid')
            if ( evid is None) or ( len(evid) == 0 ):
                # did not include evid parameter - they're messing with us
                print "NO evid"
                self.set_status( 500 )
                self.set_header("content-type", "text/plain")
                self.write("???")
                return
            evid = evid[0]

            if confirm_mode == 'db' :
                # find the data corresponding to the event id of the login event
                print "EVID", evid
                # bug: refuse if evid is too old
                # bug: refuse if evid was used before
                c = db.execute("SELECT idp, eppn, attribs FROM ssph_auth_events WHERE auth_event_id = :1",
                        ( evid, )
                    )
                x = c.fetchone()
                c.close()
                if x is None :
                    # not an evid issued by SSPH - they're messing with us
                    print "Did not find evid in database"
                    self.set_status(400)
                    self.set_header("content-type", "text/plain")
                    self.write("???")
                    db.rollback()
                    return
                else :
                    # ok, it's for real.  find out who they are.
                    # (idp, eppn) identify a user
                    # attribs has a bunch of other characteristics of the user.  We don't use them
                    # here, but you might in a real system.
                    idp, eppn, attribs = x

            elif confirm_mode == 'cgi' :
                from ssph_client.cgi import ssph_validate, HashException, Refused
                try :
                    attribs = ssph_validate( my_sp_name, evid=evid, secret='12345678', url=ssph_confirm_url )
                except HashException :
                    print "hash exception"
                    self.set_status(400)
                    self.set_header("content-type", "text/plain")
                    self.write("???")
                    db.rollback()
                    return
                except Refused :
                    print "Refused authentication"
                    self.set_status(400)
                    self.set_header("content-type", "text/plain")
                    self.write("???")
                    db.rollback()
                    return

                idp = attribs['Shib_Identity_Provider']
                eppn = attribs['eppn']

            # who were we before?
            old_cookie = self.get_cookie( session_cookie_name )

            # create a new crypto-strong session cookie, even if the user currently has a cookie
            session_cookie = binascii.b2a_hex(os.urandom(48)) + ( "%010x" % (time.time()*7) )

            cookie_expires = int(time.time())+600

            # remember who the user is in our session cookie table
            db.execute("""INSERT INTO ssph_demo_cookies ( cookie, auth, idp, eppn, expire ) VALUES
                ( :1, :2, :3, :4, :5 ) """,
                    ( 
                    session_cookie, 
                        # the session cookie we created.  do not re-use evid because that opens
                        # a session fixation attack vector.
                    'Y', 
                        # For demo purposes, they are authenticated.  You might have various levels
                        # or types of authentication.
                    idp, 
                    eppn, 
                        # (idp, eppn) identify the user.  A real application might create its
                        # own integer uid when it sees a new (idp, eppn) for convenience in
                        # tracking users.
                    cookie_expires,
                        # here is when our cookie is going to expire.
                    )
                )
            db.commit()
            print "SESSION COOKIE UPDATED"
            print "COOKIE", session_cookie
            print "IDP", idp
            print "EPPN", eppn
            self.set_cookie( session_cookie_name, session_cookie, expires=cookie_expires )
            print "REDIRECT /"
            c = db.execute("SELECT idp, eppn FROM ssph_demo_cookies WHERE cookie = :1", (old_cookie,) )
            x = c.fetchone()
            if x is None :
                old_idp = ''
                old_eppn = 'anonymous'
            else:
                old_idp, old_eppn = x
            self.set_header( 'Content-type', "text/html" )
            self.set_status( 200 )
            self.write("YOU WERE: %s %s.<br>YOU ARE: %s %s<br><a href=/>Back to application</a><br>" %
                ( cgi.escape(old_idp), cgi.escape(old_eppn), cgi.escape(idp), cgi.escape(eppn) )
                )
            return

        session_cookie = self.get_cookie(session_cookie_name)
        print "SESSION COOKIE",session_cookie

        if session_cookie is not None :
            c = db.execute("SELECT auth, idp, eppn, expire  FROM ssph_demo_cookies WHERE cookie = :1",
                ( session_cookie, )
                )
            x = c.fetchone()
            c.close()
            if x is None :
                print "COOKIE NOT FOUND"
                auth = 'N'
                msg = "You do not have a valid cookie"
            else :
                auth, idp, eppn, expire = x
                if expire <= time.time()  :
                    print "COOKIE EXPIRED"
                    auth = 'N'
                    msg = "You are expired"
                else :
                    print "COOKIE OK"
                    auth = 'Y'
                    msg = "You are %s from %s" % ( eppn, idp )
 
        if url == '/favicon.ico' :
            self.set_status( 500 )
            return
            

        if url == '/' :
            url = '/index.html'

        if url == '/protected.txt' or url == '/demo.py' :
            if auth != 'Y' :
                self.set_header( 'Content-type', "text/html" )
                self.set_status( 200 )
                self.write('You must be logged in first<br><a href="/">Back to top</a>')
                return
            

        if 1 :

            url = url[1:]

            file_text = string.Template( open(url,"r").read() )
            
            if url.endswith(".html") :
                print "HTML"
                self.set_header( 'Content-type', "text/html" )
            else :
                print "TEXT"
                self.set_header( 'Content-type', "text/plain" )
            self.set_status( 200 )
            err = 'No err'
            self.write(
                file_text.substitute (  
                    { 
                    'msg' : msg,
                    'cookie' : session_cookie, 
                    'auth' : auth, 
                    'err' : err, 
                    'eppn' : eppn, 
                    'idp' : idp, 
                    'my_sp_name' : my_sp_name,
                    'ssph_url' : ssph_url,
                     }
                 ) 
            )

        else :
            self.set_status(500)
            self.set_header("Content-type", "text/plain")
            self.write("Invalid URL")

#####
# main program of the tornado-based web server

if __name__ == '__main__':
    tornado.options.parse_command_line()

    # tornado tries to match the urls in this order, so put the more
    # frequently used first.  Pay attention to the pattern matching,
    # though.
    handlers = [
        ( '(/.*)',            AppVector ),
        ]

    # Start up the tornado application

    app = tornado.web.Application(
        handlers=handlers,
    )

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)

    i = tornado.ioloop.IOLoop.instance()

    if False :
        # here is how you do periodic timeouts
        def alive() :
            print "still alive"
        tornado.ioloop.PeriodicCallback( alive, 10000).start()

    print "starting"
    i.start()

    # NOTREACHED

