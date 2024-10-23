"""
This module implements $DOCUMENTROOT/unsecured/ssph_admin.cgi; it provides
a few management capabilities for SSPH.

Edit the source code to grant permissions.

"""

# put a list of stsci_uuid of people who are permitted to create an SP here.
# These people can see and submit this form.
permitted_users = (
    # otam@stsci.edu
    ('https://ssoportal.stsci.edu/idp/shibboleth', '2b73c1ee-90f9-4b24-87d5-6678dfd06276'),
    # riedel@stsci.edu
    ('https://ssoportal.stsci.edu/idp/shibboleth', 'a43c09e3-4d06-45c9-aa1b-62e4b72e8313'),
    # dchittiraibalan@stsci.edu
    ('https://ssoportal.stsci.edu/idp/shibboleth', 'dedb4dc0-f0bf-41e3-96ec-8c08e781a5ff'),
    # sontag@stsci.edu
    ('https://ssoportal.stsci.edu/idp/shibboleth', '99d5b6f9-8a36-46dc-8e0a-99fe54548a32'),
    # ispitzer@stsci.edu
    ('https://ssoportal.stsci.edu/idp/shibboleth', '137490cb-a969-4a3d-b3e4-e0a28d67df8b'),
    # laidler@stsci.edu
    ('https://ssoportal.stsci.edu/idp/shibboleth', '4bea59fe-03ac-47d0-8894-7f29f8247812'),
)

# no edit beyond here
#######

import sys
import cgi
import os
import cgitb
import utils.text_table
# unremarkable way to shove the database table into a pandokia
# text_table and then display it as html.
from ssph_server.db import core_db

cgitb.enable(display=0, logdir="/internal/data1/other/logs")

from ssph_server.admin_text import html_page

def run():
    # BUG: include the IDP in this test
    if not (os.environ["Shib_Identity_Provider"], os.environ['STScI_UUID']) in permitted_users:
        print("status: 500\ncontent-type: text/plain\n")
        print("\nlogged in but not permitted to admin\n")
        print("you are ", os.environ["Shib_Identity_Provider"], os.environ['STScI_UUID'])
        sys.exit(1)

    # we never get here unless we are authorized IT people, so it is ok
    # to enable tracebacks.  It is easier than providing proper error
    # messages.
    import cgitb
    cgitb.enable(display=0, logdir="/internal/data1/other/logs")

    # get the cgi parameters
    data = cgi.FieldStorage()

    if 'db_pass' in data:
        from ssph_server.db import password_file
        f=open(password_file,"w")
        os.chmod(password_file, 0o600)
        f.write(data['db_pass'].value)
        f.close()
        print("content-type: text/plain\n\ndone")
        sys.exit()

    if 'get_db_pass' in data:
        from ssph_server.db import password_file
        f=open(password_file,"r")
        print("content-type: text/plain\n\n{}".format(f.read()))
        f.close()
        sys.exit()


    if 'sp' in data:
        import json
        from ssph_server.db import core_db

        dbcreds = data['dbcreds'].value

        if dbcreds != "":
            dbcreds = json.dumps(json.loads(dbcreds))

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
        print("content-type: text/plain\n\ndone")
        sys.exit()

    if 'delete_sp' in data:
        from ssph_server.db import core_db
        c = core_db.execute("DELETE FROM ssph_sp_info WHERE sp = :1 ",
            (data['delete_sp'].value,)
            )
        core_db.commit()
        print("content-type: text/plain\n\ndone")
        sys.exit()

    if 'listsp' in data:
        t = listtb('ssph_sp_info', order_by='ORDER BY sp')
        print("content-type: text/html\n\n{}".format(t.get_html(headings=True)))
        sys.exit()

    if 'listau' in data:
        t = listtb('ssph_auth_events', 'ORDER BY tyme DESC LIMIT 100')
        print("content-type: text/html\n\n{}".format(t.get_html(headings=True)))
        sys.exit()

    # None of the CGI parameters were present, so this is not a form
    # submission.  Show the user the form.
    print("content-type: text/html\n\n{}".format(html_page))
    sys.exit()

def listtb(table, order_by=''):
    c = core_db.execute("select * from %s %s" % (table, order_by))
    t = utils.text_table.text_table()
    t.set_html_table_attributes("border=1")
    for col, name in enumerate(c.description):
        t.define_column( name, col, html=name[0] )
    for row, x in enumerate(c):
        for col, value in enumerate(x):
            t.set_value(row, col, value )
    return t
