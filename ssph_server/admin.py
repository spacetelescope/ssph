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

import os
import sys

# unremarkable way to shove the database table into a pandokia
# text_table and then display it as html.
import etc_utils.text_table

#from ssph.templates.admin_text import html_page

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

def process_data(request):
    if request.method == "GET":
        data = request.GET
    elif request.method == "POST":
        data = request.POST
    return data

def run(request):
    
    data = process_data(request)

    # BUG: include the IDP in this test
    if not (os.environ.get("Shib_Identity_Provider"), os.environ.get('STScI_UUID')) in permitted_users:
        msg = "status: 500\ncontent-type: text/plain\n"
        msg += "\nlogged in but not permitted to admin\n"
        msg += f"you are {os.environ["Shib_Identity_Provider"]}, {os.environ['STScI_UUID']}" 
        return HttpResponse(msg)

    if 'listsp' in data:
        t = listtb('ssph_sp_info', order_by='ORDER BY sp')
        return HttpResponse(t.get_html(headings=True))

    elif 'listau' in data:
        t = listtb('ssph_auth_events', 'ORDER BY tyme DESC LIMIT 100')
        return HttpResponse(t.get_html(headings=True))

    elif "sp" in data:
        return add_sp(data)

    elif 'delete_sp' in data:
        return delete_sp(data)

    elif 'form_test' in data:
        return form_test(data)

    elif 'db_pass' in data:
        return set_db_pass(data)
    
    elif 'get_db_pass' in data:
        return get_db_pass()
    
    else:
        return show_form(request)

def listtb(table, order_by=''):
    from ssph_server.db import core_db
    c = core_db.execute("select * from %s %s" % (table, order_by))
    t = etc_utils.text_table.text_table()
    t.set_html_table_attributes("border=1")
    for col, name in enumerate(c.description):
        t.define_column( name, col, html=name[0] )
    for row, x in enumerate(c):
        for col, value in enumerate(x):
            t.set_value(row, col, value )
    del core_db
    return t

def add_sp(data):
    import json
    from ssph_server.db import core_db

    dbcreds = data['dbcreds']

    if dbcreds != "":
        dbcreds = json.dumps(json.loads(dbcreds))

    core_db.execute("""
        INSERT INTO ssph_sp_info
        ( sp, url, dbtype, dbcreds, contact, email, secret, hash )
        VALUES
        ( :1, :2, :3,      :4,      :5,     :6,      :7,    :8 )
        """,
        (   data['sp'],
            data['url'],
            data['dbtype'],
            dbcreds,
            data['contact'],
            data['email'],
            data['secret'],
            data['hash']
        )
    )

    core_db.commit()
    del core_db
    t = listtb('ssph_sp_info', order_by='ORDER BY sp')
    return HttpResponse(t)

def delete_sp(data):
    from ssph_server.db import core_db
    c = core_db.execute("DELETE FROM ssph_sp_info WHERE sp = :1 ",
        (data['delete_sp'],)
        )
    core_db.commit()
    del core_db
    t = listtb('ssph_sp_info', order_by='ORDER BY sp')
    return HttpResponse(t.get_html(headings=True))

def form_test(data):
    msg = "content-type: text/plain\n\n"
    for x in data:
        msg += f"{x}: {data[x]}\n"
    msg += "--------------------------------\n"
    for x in os.environ:
        msg += f"{x}: {os.environ[x]}\n"
    return HttpResponse(msg, content_type="text/plain")

def get_db_pass():
    from ssph_server.db import password_file
    with open(password_file,"r") as pswdfile:
        pswd = pswdfile.read()
    return HttpResponse(pswd, content_type="text/plain")

def set_db_pass(data):
    from ssph_server.db import password_file
    f=open(password_file,"w")
    os.chmod(password_file, 0o600)
    f.write(data['db_pass'])
    f.close()
    return HttpResponse("done", content_type="text/plain")

def show_form(request):
    # None of the CGI parameters were present, so this is not a form
    # submission.  Show the user the form.
    context = {}
    return render(request, "admin_text.html", context)
