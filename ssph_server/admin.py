"""
This module implements $DOCUMENTROOT/unsecured/ssph_admin.cgi; it provides
a few management capabilities for SSPH.

Edit the source code to grant permissions.

"""

# put a list of eppn of people who are permitted to create an SP here.
# These people can see and submit this form.
permitted_users = (
    ( 'https://sso-test.stsci.edu/idp/shibboleth',  'sienkiew@stsci.edu' ),
    ( 'https://sso-test.stsci.edu/idp/shibboleth',  'cslocum@stsci.edu' ),
    ( 'https://sso-test.stsci.edu/idp/shibboleth',  'chanley@stsci.edu' ),
    ( 'https://sso-test.stsci.edu/idp/shibboleth',  'deighton@stsci.edu' ),
    ( 'https://sso-test.stsci.edu/idp/shibboleth',  'lipinski@stsci.edu' ),

    # bug: add/change-to the real SSO when it is set up.

    )

# no edit beyond here
#######


import cgi
import os

from ssph_server.admin_text import html_page

def run() :

    # BUG: include the IDP in this test
    if not ( os.environ["Shib_Identity_Provider"], os.environ['eppn'] ) in permitted_users :
        print "status: 500\ncontent-type: text/plain\n"
        print "\nlogged in but not permitted to admin\n"
        print "you are ",os.environ["Shib_Identity_Provider"],os.environ['eppn']
        return 1

    # we never get here unless we are authorized IT people, so it is ok
    # to enable tracebacks.  It is easier than providing proper error
    # messages.
    import cgitb
    cgitb.enable()

    # get the cgi parameters
    data = cgi.FieldStorage()

    if 'db_pass' in data :
        from ssph_server.db import password_file
        f=open(password_file,"w")
        os.chmod(password_file, 0600)
        f.write(data['db_pass'].value)
        f.close()
        print "content-type: text/plain"
        print ""
        print "done"
        return 0

    if 'get_db_pass' in data :
        from ssph_server.db import password_file
        f=open(password_file,"r")
        print "content-type: text/plain"
        print ""
        print f.read()
        f.close()
        return 0


    if 'sp' in data :
        import json
        from ssph_server.db import core_db

        dbcreds = data['dbcreds'].value

        if dbcreds != "" :
            dbcreds = json.dumps( json.loads( dbcreds ) )

        core_db.execute("""
            INSERT INTO ssph_sp_info 
            ( sp, url, dbtype, dbcreds, contact, email, secret, hash )
            VALUES
            ( :1, :2, :3,      :4,      :5,     :6,      :7,    :8 )
            """,
            (   data['sp'].value,
                data['url'].value,
                data['dbtype'].value,
                dbcreds,
                data['contact'].value,
                data['email'].value,
                data['secret'].value,
                data['hash'].value
            )
        )

        core_db.commit()
        print "content-type: text/plain"
        print ""
        print "done"
        return 0 

    if 'delete_sp' in data :
        from ssph_server.db import core_db
        c = core_db.execute("DELETE FROM ssph_sp_info WHERE sp = :1 ",
            ( data['delete_sp'].value, )
            )
        core_db.commit()
        print "content-type: text/plain"
        print ""
        print "done"
        return 0

    if 'listsp' in data :
        t = listtb( 'ssph_sp_info', order_by='ORDER BY sp' )
        print "content-type: text/html"
        print ""
        print t.get_html(headings=True)
        return 0

    if 'listau' in data:
        t = listtb( 'ssph_auth_events', 'ORDER BY tyme' )
        print "content-type: text/html"
        print ""
        print t.get_html(headings=True)
        return 0

    # None of the CGI parameters were present, so this is not a form
    # submission.  Show the user the form.
    print "content-type: text/html"
    print ""
    print html_page
    return 0

def listtb( table, order_by='' ):
    import pandokia.text_table
    # unremarkable way to shove the database table into a pandokia
    # text_table and then display it as html.
    from ssph_server.db import core_db
    c = core_db.execute("select * from %s %s" % (table, order_by) )
    t = pandokia.text_table.text_table()
    t.set_html_table_attributes("border=1")
    for col, name in enumerate(c.description) :
        t.define_column( name, col, html=name[0] )
    for row, x in enumerate(c) :
        for col, value in enumerate(x) :
            t.set_value(row, col, value )
    return t

